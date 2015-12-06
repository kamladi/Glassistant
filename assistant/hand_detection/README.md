## Files
1. `handrecog.py` The set of functions responsible for detecting a hand in a video frame,
and whether the hand is facing up/down and whether the palm is up/down. Call the `detect_hand` function
in the cognitive assitant

2. `main.py` Script to run the hand recognition script with sample data (located in `data/`)

3. `select_threshold_values.py` Script to interactively select the best thresholding values for a given image.
It will load a set of trackbars for setting the low and high threshold values for each channel, and will display
the result of thresholding an image with those values.
