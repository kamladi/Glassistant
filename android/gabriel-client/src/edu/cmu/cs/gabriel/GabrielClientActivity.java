package edu.cmu.cs.gabriel;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Timer;
import java.util.TimerTask;

import org.json.JSONException;
import org.json.JSONObject;

import com.google.android.glass.view.WindowUtils;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.hardware.Camera;
import android.hardware.Camera.PreviewCallback;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.preference.PreferenceManager;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import edu.cmu.cs.gabriel.network.AccStreamingThread;
import edu.cmu.cs.gabriel.network.NetworkProtocol;
import edu.cmu.cs.gabriel.network.ResultReceivingThread;
import edu.cmu.cs.gabriel.network.VideoStreamingThread;
import edu.cmu.cs.gabriel.token.TokenController;

public class GabrielClientActivity extends Activity implements TextToSpeech.OnInitListener, SensorEventListener {
	
	private static final String LOG_TAG = "krha";
	private static final String DEBUG_TAG = "krha_debug";

	private static final int SETTINGS_ID = Menu.FIRST;
	private static final int EXIT_ID = SETTINGS_ID + 1;
	private static final int CHANGE_SETTING_CODE = 2;
	private static final int LOCAL_OUTPUT_BUFF_SIZE = 1024 * 100;

	public static final int VIDEO_STREAM_PORT = 9098;
	public static final int ACC_STREAM_PORT = 9099;
	public static final int GPS_PORT = 9100;
	public static final int RESULT_RECEIVING_PORT = 9101;

	CameraConnector cameraRecorder;
	GlassistantStateTracker stateTracker;

	VideoStreamingThread videoStreamingThread;
	AccStreamingThread accStreamingThread;
	ResultReceivingThread resultThread;
	TokenController tokenController = null;

	private SharedPreferences sharedPref;
	private boolean hasStarted;
	private CameraPreview mPreview;
	private BufferedOutputStream localOutputStream;
	AlertDialog errorAlertDialog;

	private SensorManager mSensorManager = null;
	private Sensor mAccelerometer = null;
	protected TextToSpeech mTTS = null;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		Log.d(DEBUG_TAG, "on onCreate");
		super.onCreate(savedInstanceState);
		
		// Requests a voice menu on this activity.
		getWindow().requestFeature(WindowUtils.FEATURE_VOICE_COMMANDS);
		
		setContentView(R.layout.activity_main);
		getWindow().addFlags(WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED+
                WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON+
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);		
		
		
		// Connect to Gabriel Server if it's not experiment
		if (Const.IS_EXPERIMENT == false){
			final Button expButton = (Button) findViewById(R.id.button_runexperiment);
			expButton.setVisibility(View.GONE);
			init_once();
			init_experiement();			
		}
	}
	
	@Override
    public boolean onCreatePanelMenu(int featureId, Menu menu) {
        if (featureId == WindowUtils.FEATURE_VOICE_COMMANDS) {
            getMenuInflater().inflate(R.menu.main, menu);
            return true;
        }
        // Pass through to super to setup touch menu.
        return super.onCreatePanelMenu(featureId, menu);
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.main, menu);
        return true;
    }

    @Override
    public boolean onMenuItemSelected(int featureId, MenuItem item) {
        if (featureId == WindowUtils.FEATURE_VOICE_COMMANDS) {
            switch (item.getItemId()) {
                case R.id.action_ok:
                	Log.d(DEBUG_TAG, "Received voice command");
                	stateTracker.updateState(stateTracker.getCurrentStep()+1);
                	Log.d(DEBUG_TAG, "Updated state. Current step is: "+stateTracker.getCurrentStep());
                    break;
                default:
                    return true;
            }
            return true;
        }
        return super.onMenuItemSelected(featureId, item);
    }

	boolean experimentStarted = false;
	public void startExperiment(View view) {
		if (!experimentStarted) {
			// scriptized experiement	
			experimentStarted = true;
			runExperiements();
		}
	}
	
	protected void runExperiements(){
		final Timer startTimer = new Timer();
		TimerTask autoStart = new TimerTask(){
			String[] ipList = {"128.237.176.143"};
//			int[] tokenSize = {1};
			int[] tokenSize = {10000};
			int ipIndex = 0;
			int tokenIndex = 0;
			@Override
			public void run() {
				GabrielClientActivity.this.runOnUiThread(new Runnable() {
		            @Override
		            public void run() {
						// end condition
						if ((ipIndex == ipList.length) || (tokenIndex == tokenSize.length)) {
							Log.d(LOG_TAG, "Finish all experiemets");
							startTimer.cancel();
							
							terminate();
							
							return;
						}
						
						// make a new configuration
						Const.GABRIEL_IP = ipList[ipIndex];
						Const.MAX_TOKEN_SIZE = tokenSize[tokenIndex];
						Const.LATENCY_FILE_NAME = "latency-" + ipIndex + "-" + Const.GABRIEL_IP + "-" + Const.MAX_TOKEN_SIZE + ".txt";
						Const.LATENCY_FILE = new File (Const.ROOT_DIR.getAbsolutePath() +
								File.separator + "exp" +
								File.separator + Const.LATENCY_FILE_NAME);
						Log.d(LOG_TAG, "Start new experiemet");
						Log.d(LOG_TAG, "ip: " + Const.GABRIEL_IP +"\tToken: " + Const.MAX_TOKEN_SIZE);

						
						// run the experiment
						init_experiement();
						
						// move on the next experiment
						tokenIndex++;
						if (tokenIndex == tokenSize.length){
							tokenIndex = 0;
							ipIndex++;
						}
		            }
		        });
			}
		};
		
		// run 3 minutes for each experiement
		init_once();
		startTimer.schedule(autoStart, 1000, 10*60*1000);
	}

	private void init_once() {
		Log.d(DEBUG_TAG, "on init once");
		mPreview = (CameraPreview) findViewById(R.id.camera_preview);
		mPreview.setPreviewCallback(previewCallback);
		Const.ROOT_DIR.mkdirs();
		Const.LATENCY_DIR.mkdirs();
		// TextToSpeech.OnInitListener
		if (mTTS == null) {
			mTTS = new TextToSpeech(this, this);
		}
		if (mSensorManager == null) {
			mSensorManager = (SensorManager) getSystemService(SENSOR_SERVICE);
			mAccelerometer = mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
			mSensorManager.registerListener(this, mAccelerometer, SensorManager.SENSOR_DELAY_NORMAL);
		}
		if (this.errorAlertDialog == null) {
			this.errorAlertDialog = new AlertDialog.Builder(GabrielClientActivity.this).create();
			this.errorAlertDialog.setTitle("Error");
			this.errorAlertDialog.setIcon(R.drawable.ic_launcher);
		}
		if (cameraRecorder != null) {
			cameraRecorder.close();
			cameraRecorder = null;
		}
		if (localOutputStream != null){
			try {
				localOutputStream.close();
			} catch (IOException e) {}
			localOutputStream = null;
		}
		
		if (cameraRecorder == null) {
			cameraRecorder = new CameraConnector();
			cameraRecorder.init();
			Log.d(LOG_TAG, "new cameraRecorder");
		}
		if (localOutputStream == null){
			localOutputStream = new BufferedOutputStream(new FileOutputStream(
					cameraRecorder.getInputFileDescriptor()), LOCAL_OUTPUT_BUFF_SIZE);

			Log.d(LOG_TAG, "new localoutputStream");
		}
		
		stateTracker = new GlassistantStateTracker();
		System.out.println("STATE TRACKER INIT");
		
		hasStarted = true;
	}
	
	private void init_experiement() {

		Log.d(DEBUG_TAG, "on init experiment");
		if (tokenController != null){
			tokenController.close();
		}
		if ((videoStreamingThread != null) && (videoStreamingThread.isAlive())) {
			videoStreamingThread.stopStreaming();
			videoStreamingThread = null;
		}
		if ((accStreamingThread != null) && (accStreamingThread.isAlive())) {
			accStreamingThread.stopStreaming();
			accStreamingThread = null;
		}
		if ((resultThread != null) && (resultThread.isAlive())) {
			resultThread.close();
			resultThread = null;
		}
		
		try {
			Thread.sleep(3*1000);
		} catch (InterruptedException e) {}
		
		tokenController = new TokenController(Const.LATENCY_FILE);
		resultThread = new ResultReceivingThread(Const.GABRIEL_IP, RESULT_RECEIVING_PORT, returnMsgHandler, tokenController);
		resultThread.start();
		
		FileDescriptor fd = cameraRecorder.getOutputFileDescriptor();
		videoStreamingThread = new VideoStreamingThread(fd,
				Const.GABRIEL_IP, VIDEO_STREAM_PORT, returnMsgHandler, tokenController, stateTracker);
		videoStreamingThread.start();
		
		accStreamingThread = new AccStreamingThread(Const.GABRIEL_IP, ACC_STREAM_PORT, returnMsgHandler, tokenController);
		accStreamingThread.start();

		stopBatteryRecording();
		startBatteryRecording();
	}
	
	// Implements TextToSpeech.OnInitListener
	public void onInit(int status) {
		if (status == TextToSpeech.SUCCESS) {
			if (mTTS == null){
				mTTS = new TextToSpeech(this, this);
			}
			int result = mTTS.setLanguage(Locale.US);
			if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
				Log.e("krha_app", "Language is not available.");
			}
		} else {
			// Initialization failed.
			Log.e("krha_app", "Could not initialize TextToSpeech.");
		}
	}

	@Override
	protected void onResume() {
		super.onResume();
		Log.d(DEBUG_TAG, "on resume");
	}

	@Override
	protected void onPause() {
		super.onPause();
		Log.d(DEBUG_TAG, "on pause");
		this.terminate();
		Log.d(DEBUG_TAG, "out pause");
	}

	@Override
	protected void onDestroy() {
		this.terminate();
		super.onDestroy();
	}

	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
		Intent intent;

		switch (item.getItemId()) {
		case SETTINGS_ID:
			intent = new Intent().setClass(this, SettingsActivity.class);
			startActivityForResult(intent, CHANGE_SETTING_CODE);
			break;
		}

		return super.onOptionsItemSelected(item);
	}

	private PreviewCallback previewCallback = new PreviewCallback() {
		public void onPreviewFrame(byte[] frame, Camera mCamera) {
			if (hasStarted && (localOutputStream != null)) {
				Camera.Parameters parameters = mCamera.getParameters();
				if (videoStreamingThread != null){
//					Log.d(LOG_TAG, "in");
					videoStreamingThread.push(frame, parameters);					
				}
			}
		}
	};

	private Handler returnMsgHandler = new Handler() {
		public void handleMessage(Message msg) {
			Log.d(DEBUG_TAG, "Message Received: "+(String)msg.obj);
			if (msg.what == NetworkProtocol.NETWORK_RET_FAILED) {
				Bundle data = msg.getData();
				String message = data.getString("message");
//				stopStreaming();
//				new AlertDialog.Builder(GabrielClientActivity.this).setTitle("INFO").setMessage(message)
//						.setIcon(R.drawable.ic_launcher).setNegativeButton("Confirm", null).show();
			}
			if (msg.what == NetworkProtocol.NETWORK_RET_RESULT) {
				if (mTTS != null){
					String ttsMessage = "Assistant is confused";
					boolean newStep = false;

					try {
						JSONObject returnObj= new JSONObject((String) msg.obj);
						ttsMessage = returnObj.getString("message");
						int nextStep = returnObj.getInt("next_step");
//						if (nextStep != stateTracker.getCurrentStep()) {
//							newStep = true;
//						}
						
					} catch (JSONException e) {
						// TODO Auto-generated catch block
						e.printStackTrace();
					}

					int len = TextToSpeech.getMaxSpeechInputLength();
					System.out.print(len);
					
					HashMap<String, String> map = new HashMap<String, String>();
					map.put(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, "LastWord");
					
					Log.d("ILTER", "New Step: " + newStep);

					if (!ttsMessage.equals(stateTracker.getCurrentText()) || 
							(ttsMessage.equals(stateTracker.getCurrentText()) && 
									(Calendar.getInstance().getTimeInMillis() - 20000) > stateTracker.getLastPlayedTime().getTimeInMillis())) {
						Log.d("ILTER", "Speaking " + ttsMessage);
						stateTracker.setCurrentText(ttsMessage);
						
						Log.d(LOG_TAG, "tts string origin: " + ttsMessage);
						String[] words = ttsMessage.split(" "); 
						mTTS.setSpeechRate(2f);
						mTTS.setOnUtteranceProgressListener(new UtteranceProgressListener() {
							
							@Override
							public void onDone(String utteranceId) {
								Log.d(DEBUG_TAG, "Message played.");
//								try {
//									Thread.sleep(5000);
//								} catch (InterruptedException e) {
//									e.printStackTrace();
//								}
								//stateTracker.updateState(stateTracker.getCurrentStep()+1);
								//stateTracker.setLastPlayedTime(Calendar.getInstance());
							}

							@Override
							public void onError(String utteranceId) {}

							@Override
							public void onStart(String utteranceId) {}
						});
						for (int i=0; i < words.length; i++) {
							
							int queuConstant = TextToSpeech.QUEUE_ADD;
							if (i == 0) {
								queuConstant = TextToSpeech.QUEUE_FLUSH;
							}
							if(i == (words.length-1)){
								mTTS.speak(words[i], queuConstant, map);
								break;
							}
							mTTS.speak(words[i], queuConstant, null);
							
						}
					}
				}
			}
		}
	};
	
	public static class CustomUtteranceProgressListener extends UtteranceProgressListener{
		
		private String sentence = null;
		private int noOfUtterances = 0;
		private int currentUtterance = 0;
		private int step = -1;
		private GlassistantStateTracker tracker = null;
		
		public CustomUtteranceProgressListener(String sentence, int noOfUtterances, int step, GlassistantStateTracker tracker) {
			this.noOfUtterances = noOfUtterances;
			this.sentence = sentence;
			this.step = step;
			this.tracker = tracker;
		}

		@Override
		public void onDone(String utteranceId) {
			if(this.currentUtterance == this.noOfUtterances){
				this.tracker.updateState(tracker.getCurrentStep()+1);
				this.tracker.
			}
		}

		@Override
		public void onError(String utteranceId) {}

		@Override
		public void onStart(String utteranceId) {}
		
	}

	protected int selectedRangeIndex = 0;

	public void selectFrameRate(View view) throws IOException {
		selectedRangeIndex = 0;
		final List<int[]> rangeList = this.mPreview.supportingFPS;
		String[] rangeListString = new String[rangeList.size()];
		for (int i = 0; i < rangeListString.length; i++) {
			int[] targetRange = rangeList.get(i);
			rangeListString[i] = new String(targetRange[0] + " ~" + targetRange[1]);
		}

		AlertDialog.Builder ab = new AlertDialog.Builder(this);
		ab.setTitle("FPS Range List");
		ab.setIcon(R.drawable.ic_launcher);
		ab.setSingleChoiceItems(rangeListString, 0, new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				selectedRangeIndex = position;
			}
		}).setPositiveButton("Ok", new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				if (position >= 0) {
					selectedRangeIndex = position;
					
					
				}
				int[] targetRange = rangeList.get(selectedRangeIndex);
				mPreview.changeConfiguration(targetRange, null);
			}
		}).setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				return;
			}
		});
		ab.show();
	}

	protected int selectedSizeIndex = 0;

	public void selectImageSize(View view) throws IOException {
		selectedSizeIndex = 0;
		final List<Camera.Size> imageSize = this.mPreview.supportingSize;
		String[] sizeListString = new String[imageSize.size()];
		for (int i = 0; i < sizeListString.length; i++) {
			Camera.Size targetRange = imageSize.get(i);
			sizeListString[i] = new String(targetRange.width + " ~" + targetRange.height);
		}

		AlertDialog.Builder ab = new AlertDialog.Builder(this);
		ab.setTitle("Image Size List");
		ab.setIcon(R.drawable.ic_launcher);
		ab.setSingleChoiceItems(sizeListString, 0, new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				selectedRangeIndex = position;
			}
		}).setPositiveButton("Ok", new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				if (position >= 0) {
					selectedRangeIndex = position;
				}
				Camera.Size targetSize = imageSize.get(selectedRangeIndex);
				mPreview.changeConfiguration(null, targetSize);
			}
		}).setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int position) {
				return;
			}
		});
		ab.show();
	}

	public void stopStreaming() {
		hasStarted = false;
		if (mPreview != null)
			mPreview.setPreviewCallback(null);
		if (videoStreamingThread != null && videoStreamingThread.isAlive()) {
			videoStreamingThread.stopStreaming();
		}
		if (accStreamingThread != null && accStreamingThread.isAlive()) {
			accStreamingThread.stopStreaming();
		}
		if (resultThread != null && resultThread.isAlive()) {
			resultThread.close();
		}
	}

	public void setDefaultPreferences() {
		// setDefaultValues will only be invoked if it has not been invoked
		PreferenceManager.setDefaultValues(this, R.xml.preferences, false);
		sharedPref = PreferenceManager.getDefaultSharedPreferences(this);

		sharedPref.edit().putBoolean(SettingsActivity.KEY_PROXY_ENABLED, true);
		sharedPref.edit().putString(SettingsActivity.KEY_PROTOCOL_LIST, "UDP");
		sharedPref.edit().putString(SettingsActivity.KEY_PROXY_IP, "128.2.213.25");
		sharedPref.edit().putInt(SettingsActivity.KEY_PROXY_PORT, 8080);
		sharedPref.edit().commit();

	}

	public void getPreferences() {
		sharedPref = PreferenceManager.getDefaultSharedPreferences(this);
		String sProtocol = sharedPref.getString(SettingsActivity.KEY_PROTOCOL_LIST, "UDP");
		String[] sProtocolList = getResources().getStringArray(R.array.protocol_list);
	}

	/*
	 * Recording battery info by sending an intent Current and voltage at the
	 * time Sample every 100ms
	 */
	Intent batteryRecordingService = null;

	public void startBatteryRecording() {
		BatteryRecordingService.AppName = "Gabriel" + File.separator + "exp";
		BatteryRecordingService.setOutputFileNames("Battery-" + Const.LATENCY_FILE.getName(), 
				"CPU-" + Const.LATENCY_FILE.getName());
		Log.i("wenluh", "Starting Battery Recording Service");
		batteryRecordingService = new Intent(this, BatteryRecordingService.class);
		startService(batteryRecordingService);
	}

	public void stopBatteryRecording() {
		Log.i("wenluh", "Stopping Battery Recording Service");
		if (batteryRecordingService != null) {
			stopService(batteryRecordingService);
			batteryRecordingService = null;
		}
	}
	
	private void terminate() {
		Log.d(DEBUG_TAG, "on terminate");
		// change only soft state
		stopBatteryRecording();
		
		if (cameraRecorder != null) {
			cameraRecorder.close();
			cameraRecorder = null;
		}
		if ((resultThread != null) && (resultThread.isAlive())) {
			resultThread.close();
			resultThread = null;
		}
		if ((videoStreamingThread != null) && (videoStreamingThread.isAlive())) {
			videoStreamingThread.stopStreaming();
			videoStreamingThread = null;
		}
		if ((accStreamingThread != null) && (accStreamingThread.isAlive())) {
			accStreamingThread.stopStreaming();
			accStreamingThread = null;
		}
		if (tokenController != null){
			tokenController.close();
			tokenController = null;
		}
		
		// Don't forget to shutdown!
		if (mTTS != null) {
			Log.d(LOG_TAG, "TTS is closed");
			mTTS.stop();
			mTTS.shutdown();
			mTTS = null;
		}
		if (mPreview != null) {
			mPreview.setPreviewCallback(null);
			mPreview.close();
			mPreview = null;
		}
		if (mSensorManager != null) {
			mSensorManager.unregisterListener(this);
			mSensorManager = null;
			mAccelerometer = null;
		}
	}

	@Override
	public void onAccuracyChanged(Sensor sensor, int accuracy) {
	}

	@Override
	public void onSensorChanged(SensorEvent event) {
		if (event.sensor.getType() != Sensor.TYPE_ACCELEROMETER)
			return;
		if (accStreamingThread != null) {
//			accStreamingThread.push(event.values);
		}
		// Log.d(LOG_TAG, "acc_x : " + mSensorX + "\tacc_y : " + mSensorY);
	}
}
