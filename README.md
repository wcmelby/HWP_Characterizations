# HWP_Characterizations
Code required to take and analyze data with a half-wave plate, specifically using the dual-rotating retarder polarimeter setup. This will yield the entire Mueller matrix of a sample, from which the retardance and fast axis alignment can be determined


Here are instructions on how to characterize a wave-plate using the dual-rotating retarder polarimeter (DRRP) setup. All files pertaining to this method are in the desktop folder DRRP_HWP_Characterization. The theory behind this method can be found in Goldstein’s paper (https://opg.optica.org/ao/fulltext.cfm?uri=ao-31-31-6676&id=40161) or Jaren’s Github. The single rotating half wave plate is a similar method but is less useful because it doesn’t yield the whole Mueller matrix. 

As an example, the JHK waveplate testing is shown in Uncoated_JHK_HWP

General outline for taking data:
1) Take images

a) DRRP_Take_Image is useful for taking single images, and saves files to the Darks subfolder. Always run the camera at -40C. It will take a few minutes to cool, which is also a good time to let the light source warm up

b) Make sure the dark frames have the same tint and fps as the regular image, but with the light source off. Take about 10-15 darks

c) BEFORE running any code that controls the rotation stages, make sure to open the Kinesis app and home each device! This will save a lot of trouble 

d) Actual data is taken with DRRP_Double_Rotate_and_Take_Image. This rotates the two quarter waveplates at a 1:5 ratio, stopping at each angle to take images. Take 5-10 and make sure pixels aren’t saturated. Ideally peaks around 5000. Using higher fps if possible gives a better dark subtraction. Rotate the first QWP between 0 and 180 in 4 or 5 degree increments

e) Calibrations are done with the sample removed (nothing between the two waveplates) and take a full cycle of images. Actual data is taken with the sample placed back in, make sure to use the same conditions and don’t nudge any of the components. 

2) Reduce the raw images

a) Subtract dark frames from the raw images by running the dark_subtraction function. This will save them to a new file

3) Extract data from reduced images

a) Use extract_intensities function to get intensities, make sure index aligns with the center of each spot

b) Depending on the exposure time used, adjust the cutoff value to help identify outliers where the camera messes up. Delete these indices from the data and the angle range for that wavelength

4) Extract polarimetric data

a) Run the function ultimate_polarimetry with the calibration data and the actual data which will give you everything you need. To manually check intermediate steps you can run the other functions separately in case something looks wrong

5) Make a nice plot of results with pretty colors
