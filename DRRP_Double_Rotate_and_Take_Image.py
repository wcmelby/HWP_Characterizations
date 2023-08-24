import FliSdk_V2 as sdk
from astropy.io import fits
import numpy as np
import time
from pylablib.devices import Thorlabs
import copy

# Double rotate and take image for DRRP method. Make sure the second motor rotates at 5x the rate of the first

# Setting context
context = sdk.Init()

print("Detection of grabbers...")
listOfGrabbers = sdk.DetectGrabbers(context)

if len(listOfGrabbers) == 0:
    print("No grabber detected, exit.")
    exit()

print("Done.")
print("List of detected grabber(s):")

for s in listOfGrabbers:
    print("- " + s)

print("Detection of cameras...")
listOfCameras = sdk.DetectCameras(context)

if len(listOfCameras) == 0:
    print("No camera detected, exit.")
    exit()

print("Done.")

cameraIndex = 0
print("Setting camera: " + listOfCameras[cameraIndex])
ok = sdk.SetCamera(context, listOfCameras[cameraIndex])

if not ok:
    print("Error while setting camera.")
    exit()

print("Setting mode full.")

ok = sdk.Update(context)
print("Updating...")
if not ok:
    print("Error Updating")
    exit()

res, mb, fe, pw, init_sensor_temp, peltier, heatsink = sdk.FliCredTwo.GetAllTemp(context)
if res:
    print("Initial Temp: {:.2f}C".format(init_sensor_temp))
else:
    print("Error reading temperature.")

# Querying sensor temperature
try:
    set_temp = input("Temperature to set? (between " + str(-55) + " C and " + str(20)+ " C) ")
    set_temp = float(set_temp)
    ok = sdk.FliCredTwo.SetSensorTemp(context, float(set_temp))
    if not ok:
        print("Error while setting temperature.")
        exit()
except ValueError:
    print("Not a valid temperature")

ok = sdk.Update(context)
print("Starting to cool...")
if not ok:
    print("Error while updating.")
    exit()

res, mb, fe, pw, sensortemp, peltier, heatsink = sdk.FliCredTwo.GetAllTemp(context);

temp_tolerance = 0.3 #get close temp but don't print infinitely

while np.abs(sensortemp - set_temp) >= temp_tolerance:
    res, mb, fe, pw, sensortemp, peltier, heatsink = sdk.FliCredTwo.GetAllTemp(context)
    print("Sensor Temp: {:.2f}C".format(sensortemp),'\n','-------------')
    time.sleep(5)

res, mb, fe, pw, sensortemp, peltier, heatsink = sdk.FliCredTwo.GetAllTemp(context)
print("Finished Setting Temperature",'\n',"Final Temp: {:.2f}C".format(sensortemp))

# Control the fps
fps = 0

if sdk.IsSerialCamera(context):
    res, fps = sdk.FliSerialCamera.GetFps(context)
elif sdk.IsCblueSfnc(context):
    res, fps = sdk.FliCblueSfnc.GetAcquisitionFrameRate(context)
print("Current camera FPS: " + str(fps))


val_fps = input("FPS to set? ")
if val_fps.isnumeric():
    if sdk.IsSerialCamera(context):
        sdk.FliSerialCamera.SetFps(context, float(val_fps))
    elif sdk.IsCblueSfnc(context):
        sdk.FliCblueSfnc.SetAcquisitionFrameRate(context, float(val_fps))


if sdk.IsCredTwo(context) or sdk.IsCredThree(context):
    res, response = sdk.FliSerialCamera.SendCommand(context, "mintint raw")
    minTint = float(response)

    res, response = sdk.FliSerialCamera.SendCommand(context, "maxtint raw")
    maxTint = float(response)

    res, response = sdk.FliSerialCamera.SendCommand(context, "tint raw")

    print("Current camera tint: " + str(float(response)*1000) + "ms")

    set_tint = input("Tint to set? (between " + str(minTint*1000) + "ms and " + str(maxTint*1000)+ "ms) ")
    sdk.FliCredTwo.SetTint(context, float(float(set_tint)/1000))
    ok = sdk.Update(context)
    if not ok:
        print("error setting tint")
        exit()

    res, response = sdk.FliCredTwo.GetTint(context)
    tint = response*1000
    print("Current camera tint: " +str(tint) +"ms")


res = sdk.FliCredTwo.SetConversionGain(context,'low')
if not res:
    print('error setting gain mode')
sdk.Update(context)

val = input("Take how many images?")
val = int(val)


# Now that the camera is setup, prepare for rotating while taking picrues
# Most secure way is to ensure connection with the motor through the Kinesis app before running code

stage1 = Thorlabs.KinesisMotor(Thorlabs.list_kinesis_devices()[0][0],scale='stage')
stage2 = Thorlabs.KinesisMotor(Thorlabs.list_kinesis_devices()[1][0], scale='stage')
print("Connected to K10CR1 devices")

print("Homing devices...")
stage1.move_to(0)
stage1.wait_move()
stage1._setup_homing()
home1 = stage1.home(sync=True)

stage2.move_to(0)
stage2.wait_move()
stage2._setup_homing()
home2 = stage2.home(sync=True)
print('Homing complete')

position1 = stage1.get_position()
position2 = stage2.get_position()

print('Current positions are ' + str(position1) + ' and ' + str(position2) + ' degrees')

# Query the user what angle range and what increments
tot_angle = input("Total angle to rotate (degrees)?")
increment = input("Increment angle to change?")

steps = int(tot_angle)/int(increment)

print("Taking images...")

for i in range(int(steps)+1):
    sdk.EnableGrabN(context, val+1)
    sdk.Update(context)
    sdk.Start(context)
    time.sleep(val*tint/1000)
    counter = 0
    max_iter = 10
    while sdk.IsGrabNFinished(context) is False:
        if counter >= max_iter:
            break
        time.sleep(1)
        counter += 1
    print("Is grab finished? " + str(sdk.IsGrabNFinished(context)))

    frame_list = []
    # Now begin loop for the images
    #fname = r"C:\\Users\\EPL User\\Desktop\\DRRP_HWP_Characterization\\Uncoated_JHK\\Calibrations\\Calibrations_Raw\\Cal_1400_Filter\\"
    fname = r"C:\\Users\\EPL User\\Desktop\\DRRP_HWP_Characterization\\Uncoated_JHK\\Uncoated_Raw\\Uncoated_1400_Filter\\"

    for j in range(val+1):
        image16b = copy.deepcopy(sdk.GetRawImageAsNumpyArray(context, j))
        time.sleep(1.3*tint/1000)

        if j > 0:
            frame_list.append(image16b)
    
    frame_list = np.array(frame_list) 
    hdu_new = fits.PrimaryHDU(frame_list)
    position1 = stage1.get_position()
    position2 = stage2.get_position() 
    print('Position 1 is ' + str(position1) + ' and position 2 is ' + str(position2))
    hdu_new.writeto(fname+ "DRRP_Uncoated_1400nm_"+str(val_fps)+"_"+str(set_tint)+"_"+str(position1)+".fits", overwrite = True)
    print("Files saved to " + str(fname))

    stage1.move_by(int(increment))
    stage1.wait_move()
    stage2.move_by(5*int(increment))
    stage2.wait_move()
    sdk.Stop(context)


print("Exiting SDK, Process Finished...")
sdk.Exit(context)