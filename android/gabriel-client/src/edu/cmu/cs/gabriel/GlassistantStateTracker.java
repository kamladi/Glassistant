package edu.cmu.cs.gabriel;

public class GlassistantStateTracker {
	
	private int currentStep = 0;
	private String currentText = "";
	
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

}
