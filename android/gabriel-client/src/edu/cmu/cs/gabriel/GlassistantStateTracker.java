package edu.cmu.cs.gabriel;

import java.util.Calendar;

public class GlassistantStateTracker {
	
	private int currentStep = 0;
	private int nextStep = 0;
	private String currentText = "";
	private String nextText = "";
	private Calendar lastPlayedTime = Calendar.getInstance();
	
	public String getNextText() {
		return nextText;
	}

	public void setNextText(String nextText) {
		this.nextText = nextText;
	}

	public int getNextStep() {
		return nextStep;
	}

	public void setNextStep(int nextStep) {
		this.nextStep = nextStep;
	}

	public int getCurrentStep () {
		return currentStep;
	}	
	
	public int updateState(int newState) {
		currentStep = newState;
		return currentStep;
	}
	
	public void setCurrentText(String text) {
		currentText = text;
	}
	
	public String getCurrentText() {
		return currentText;
	}
	
	public void setLastPlayedTime(Calendar lastPlayedTime){
		this.lastPlayedTime = lastPlayedTime;
	}
	
	public Calendar getLastPlayedTime(){
		return this.lastPlayedTime;
	}

}
