package edu.cmu.cs.gabriel;

import java.util.Calendar;

public class GlassistantStateTracker {
	
	private int currentStep = 0;
	private String currentText = "";
	private Calendar lastPlayedTime = Calendar.getInstance();
	
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
