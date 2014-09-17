package edu.cmu.cs.gabriel;

public class GlassistantStateTracker {
	
	private int currentStep = 0;
	private String currentText = "";
	private boolean resetting = false;
	private int internalResetCounter;

	public int getCurrentStep () {
		
		if (resetting) {
			return getCurrentStepWhileResetting();
		}
		
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
	
	public void resetState() {
		currentStep = 0;
		internalResetCounter = 0;
		resetting = true;
	}
	
	private int getCurrentStepWhileResetting() {
		
		internalResetCounter++;
		if (internalResetCounter == 12) {
			resetting = false;
		}
		return 0;
	}

}
