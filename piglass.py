from subprocess import call
import RPi.GPIO as GPIO
import picamera
import time
import sys
import datetime
import cv2
import numpy as np

height = 600
width = 800
alphaValue = 64
o = None
recording = 0

def initialize_camera():
    camera.resolution = (width, height)
    camera.sharpness = 0
    camera.contrast = 0
    camera.brightness = 50
    camera.saturation = 0
    camera.ISO = 0
    camera.video_stabilization = True
    camera.exposure_compensation = 0
    camera.exposure_mode = 'auto'
    camera.meter_mode = 'average'
    camera.awb_mode = 'auto'
    camera.image_effect = 'none'
    camera.color_effects = None
    camera.rotation = -90
    camera.hflip = False
    camera.vflip = False
    camera.start_preview()
    print "Camera is configured and outputting video..."

camera = picamera.PiCamera()
if (width%32) > 0 or (height%16) > 0:
    print "Rounding down set resolution to match camera block size:"
    width = width-(width%32)
    height = height-(height%16)
    print "New resolution: " + str(width) + "x" + str(height)
#initialize_camera()

ovl = np.zeros((height, width, 3), dtype=np.uint8)

globalz = {
    'zoom_step'     : 0.03,

    'zoom_xy_min'   : 0.0,
    'zoom_xy'       : 0.0,
    'zoom_xy_max'   : 0.4,

    'zoom_wh_min'   : 1.0,
    'zoom_wh'       : 1.0,
    'zoom_wh_max'   : 0.2,
#    'o'             : camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)

}

#o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)

def update_zoom():
    #print "Setting camera to (%s, %s, %s, %s)" % (globals['zoom_xy'], globals[$
    camera.zoom = (globalz['zoom_xy'], globalz['zoom_xy'], globalz['zoom_wh'], globalz['zoom_wh'])
    print "Camera at (x, y, w, h) = ", camera.zoom

def set_min_zoom():
    globalz['zoom_xy'] = globalz['zoom_xy_min']
    globalz['zoom_wh'] = globalz['zoom_wh_min']

def set_max_zoom():
    globalz['zoom_xy'] = globalz['zoom_xy_max']
    globalz['zoom_wh'] = globalz['zoom_wh_max']

def zoom_out():
    if globalz['zoom_xy'] - globalz['zoom_step'] < globalz['zoom_xy_min']:
        set_min_zoom()
    else:
        globalz['zoom_xy'] -= globalz['zoom_step']
        globalz['zoom_wh'] += (globalz['zoom_step'] * 2)
    update_zoom()

def zoom_in():
    if globalz['zoom_xy'] + globalz['zoom_step'] > globalz['zoom_xy_max']:
        set_max_zoom()
    else:
        globalz['zoom_xy'] += globalz['zoom_step']
        globalz['zoom_wh'] -= (globalz['zoom_step'] * 2)
    update_zoom()

ovl = np.zeros((height, width, 3), dtype=np.uint8)
alphaValue = 64

# initial config for gpio ports
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

pin_17 = False
pin_18 = False
pin_26 = False

colors = {
        'white': (255,255,255),
        'red': (255,0,0),
        'green': (0,255,0),
        'blue': (0,0,255),
        'yellow': (255,255,0),
        }

def colormap(col):
    return colors.get(col, (255,255,255))

col = colormap('red')
font = cv2.FONT_HERSHEY_PLAIN

guivisible = 1
togsw = 1
guiOn = 1
gui = np.zeros((height, width, 3), dtype=np.uint8)
gui1 = 'PiGlass'
gui2 = 'Version 0.1 alpha'
gui3 = 'button  = take pic'


def get_file_name_pic():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def get_file_name_vid():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.h264")

def creategui(target):
    cv2.putText(target, gui1, (10,height-138), font, 10, col, 4)
    cv2.putText(target, gui2, (10,height-108), font, 2, col, 2)
    cv2.putText(target, gui3, (10,height-78), font, 2, col, 2)
    #camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def patternswitch(target,guitoggle):
    global o, alphaValue
    # first remove existing overlay:
    # cycle through possible patterns:
    if guitoggle == 1:
	    creategui(gui)
    o = camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def togglepattern(channel):
    global togsw,o,ovl,gui,alphaValue
    # if overlay is inactive, ignore button:
    if togsw == 0:
        print "Pattern button pressed, but ignored --- Crosshair not visible."
    # if overlay is active, drop it, change pattern, then show it again
    else:
        #curpat += 1
        #print "Set new pattern: " + str(curpat) 
        #if curpat > patterns.maxpat:     # this number must be adjusted to number of available patterns!
        #    curpat = 1
        if guivisible == 0:
            # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitch(ovl,0)
            #if o in globalz():
            #    camera.remove_overlay(o)
            #o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
        else:
            # reinitialize array
            gui = np.zeros((height, width, 3), dtype=np.uint8)
            creategui(gui)
            patternswitch(gui,1)
            if 'o' in globalz():
                camera.remove_overlay(o)
            o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
    return

def toggleonoff(channel):
    global togsw,o,alphaValue
    if togsw == 1:
        print "Toggle Crosshair OFF"
        camera.remove_overlay(o)
        togsw = 0
    else:
        print "Toggle Crosshair ON"
        if guivisible == 0:
            o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
        else:
            o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
        togsw = 1
    return

def button_pressed_26(pin):
    global pin_26
    print "pin:", pin
    #camera.stop_preview()
    filename = get_file_name_pic()
    camera.capture(filename, use_video_port=True)
    #camera.start_preview()

def button_pressed_21(pin):
    print "Exiting..."
    camera.stop_preview()
    sys.exit(0)

def button_pressed_17(pin):
    global pin_17, recording
    print "pin:", pin
    if recording == 0
        filename = get_file_name_vid()
        camera.start_recording(filename)
	recording = 1
    else:
	camera.stop_recording()
	recording = 0

    #zoom_in()
    #print "pin_17", pin_17
    #while pin_17 == True:
    #    print('GPIO #17 button pressed')
    #    time.sleep(0.2)

def button_pressed_18(pin):
    global pin_18, gui, ovl, guiOn
    print "pin:", pin
    #zoom_out()
    if guiOn == 0:
        patternswitch(ovl, guiOn)
        guiOn = 1
    if guiOn == 1:
        patternswitch(ovl, guiOn)
	guiOn = 0
         
    #print "pin_18", pin_18
    #while pin_17 == True:
    #    print('GPIO #18 button pressed')
    #    time.sleep(0.2)

def configure_button_listeners():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    pin_17 = GPIO.input(17)
    pin_18 = GPIO.input(18)
    pin_26 = GPIO.input(26)
    # GPIO.RISING
    # GPIO.FALLING
    # GPIO.BOTH
    GPIO.add_event_detect(17, GPIO.FALLING, callback=button_pressed_17, bouncetime=200)
    GPIO.add_event_detect(18, GPIO.FALLING, callback=toggleonoff, bouncetime=750)
    GPIO.add_event_detect(26, GPIO.FALLING, callback=button_pressed_26, bouncetime=200)

    print "Button Listeners are configured and listening..."

def main():
    try:
        configure_button_listeners()
        initialize_camera()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        #gui = np.zeros((height, width, 3), dtype=np.uint8)
        patternswitch(gui,1)
        time.sleep(10)
        guivisible = 1
        # cycle through possible patterns:
        patternswitch(ovl,0)
        while True:
            #print('running')
	        x = 1
    finally:
        camera.close()               # clean up camera
        GPIO.cleanup()               # clean up GPIO


if __name__ == "__main__":
    main()
