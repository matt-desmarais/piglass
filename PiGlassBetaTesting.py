from subprocess import call
import RPi.GPIO as GPIO
import picamera
import time
import sys
import datetime
import cv2
import numpy as np
import KeyboardPoller
import subprocess 
import thread
import re

height = 600
width = 800
alphaValue = 75
o = None
recording = 0
buttoncounter = 0
camera = picamera.PiCamera()
global videoFile
global zoomcount
zoomcount=0
globalCounter = 0
global roi
roi = 0

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

if (width%32) > 0 or (height%16) > 0:
    print "Rounding down set resolution to match camera block size:"
    width = width-(width%32)
    height = height-(height%16)
    print "New resolution: " + str(width) + "x" + str(height)

ovl = np.zeros((height, width, 3), dtype=np.uint8)

globalz = {
    'zoom_step'     : 0.03,
    'zoom_xy_min'   : 0.0,
    'zoom_xy'       : 0.0,
    'zoom_xy_max'   : 0.4,
    'zoom_wh_min'   : 1.0,
    'zoom_wh'       : 1.0,
    'zoom_wh_max'   : 0.2,
}

def update_zoom():
    global roi
    #print roi
    #print str(roi)[1:-1]
    roi = str(globalz['zoom_xy'])[:6], str(globalz['zoom_xy'])[:6], str(globalz['zoom_wh'])[:6], str(globalz['zoom_wh'])[:6]
    print roi
    camera.zoom = (globalz['zoom_xy'], globalz['zoom_xy'], globalz['zoom_wh'], globalz['zoom_wh'])
    print "Camera at (x, y, w, h) = ", camera.zoom

def set_min_zoom():
    globalz['zoom_xy'] = globalz['zoom_xy_min']
    globalz['zoom_wh'] = globalz['zoom_wh_min']

def set_max_zoom():
    globalz['zoom_xy'] = globalz['zoom_xy_max']
    globalz['zoom_wh'] = globalz['zoom_wh_max']

def zoom_out():
    global zoomcount
    if globalz['zoom_xy'] - globalz['zoom_step'] < globalz['zoom_xy_min']:
        set_min_zoom()
    else:
        globalz['zoom_xy'] -= globalz['zoom_step']
        globalz['zoom_wh'] += (globalz['zoom_step'] * 2)
	zoomcount = zoomcount - 1
    update_zoom()

def zoom_in():
    global zoomcount
    if globalz['zoom_xy'] + globalz['zoom_step'] > globalz['zoom_xy_max']:
        set_max_zoom()
    else:
        zoomcount = zoomcount + 1
        globalz['zoom_xy'] += globalz['zoom_step']
        globalz['zoom_wh'] -= (globalz['zoom_step'] * 2)
    update_zoom()

ovl = np.zeros((height, width, 3), dtype=np.uint8)

# initial config for gpio ports
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

colors = {
        'white': (255,255,255),
        'red': (255,0,0),
        'green': (0,255,0),
        'blue': (0,0,255),
        'yellow': (255,255,0),
        }

def colormap(col):
    return colors.get(col, (255,255,255))

col = colormap('white')
font = cv2.FONT_HERSHEY_PLAIN

guivisible = 1
togsw = 1
guiOn = 1
gui = np.zeros((height, width, 3), dtype=np.uint8)
gui1 = 'PiGlass'
gui2 = 'Version 0.5 alpha'
gui3 = 'P Key = take pic'
gui4 = 'V Key = take video'
gui5 = ' '

def get_file_name_pic():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def get_file_name_vid():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.h264")

def creategui(target):
    global gui5
    cv2.putText(target, gui1, (10,height-160), font, 10, col, 6)
    cv2.putText(target, gui2, (10,height-130), font, 3, col, 3)
    cv2.putText(target, gui3, (10,height-90), font, 3, col, 3)
    cv2.putText(target, gui4, (10,height-50), font, 3, col, 3)
    cv2.putText(target, gui5, (10,height-10), font, 3, colormap("green"), 3)
    return

def patternswitch(target,guitoggle):
    global o, alphaValue
    toggleonoff()
    if guitoggle == 1:
	    creategui(gui)
    o = camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def patternswitcherRecord(target,guitoggle):
    global o, zoomcount, ycenter
    if guitoggle == 1:
        creategui(gui)

# function 
def togglepatternRecord():
    global togsw,o,curpat,col,ovl,gui,alphaValue,ycenter,zoomcount
    # if overlay is inactive, ignore button:
    if togsw == 0:
        print "Pattern button pressed, but ignored --- Crosshair not visible."
    else:
        if guivisible == 0:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitcherRecord(ovl,0)
	else:
	    gui = np.zeros((height, width, 3), dtype=np.uint8)
	    creategui(gui)
            patternswitcherRecord(gui,1)
    return

def togglepattern():
    global togsw,o,ovl,gui,alphaValue
    # if overlay is inactive, ignore button:
    if togsw == 0:
        print "Pattern button pressed, but ignored --- Crosshair not visible."
    # if overlay is active, drop it, change pattern, then show it again
    else:
        if guivisible == 0:
            # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitch(ovl,0)
            if o != None:
                camera.remove_overlay(o)
            o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
        else:
            # reinitialize array
            gui = np.zeros((height, width, 3), dtype=np.uint8)
            creategui(gui)
            patternswitch(gui,1)
            if o != None:
                camera.remove_overlay(o)
            o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
    return

def toggleonoff():
    global togsw,o,alphaValue
    if togsw == 1:
        print "Toggle Crosshair OFF"
        if o != None:
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

# function 
def togglepatternZoomIn():
    global togsw,o,curpat,col,ovl,gui,alphaValue,ycenter,zoomcount
    # if overlay is inactive, ignore button:
    if togsw == 0:
        print "Pattern button pressed, but ignored --- Crosshair not visible."
	zoom_in()
    else:
        if guivisible == 0:
            zoom_in()
	    # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitcherZoomIn(ovl,0)
	else:
            # reinitialize array
            zoom_in()
	    gui = np.zeros((height, width, 3), dtype=np.uint8)
	    creategui(gui)
            patternswitcherZoomIn(gui,1)
    return

def togglepatternZoomOut():
    global togsw,o,curpat,col,ovl,gui,alphaValue
    # if overlay is inactive, ignore button:
    if togsw == 0:
        zoom_out()
    else:
        if guivisible == 0:
	    zoom_out()
            # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitcherZoomOut(ovl,0)
            o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
        else:
	    zoom_out()
            # reinitialize array
            gui = np.zeros((height, width, 3), dtype=np.uint8)
            creategui(gui)
            patternswitcherZoomOut(gui,1)
            o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
    return

def patternswitcherZoomIn(target,guitoggle):
    global o, zoomcount, ycenter
    if guitoggle == 1:
        creategui(gui)
    if globalz['zoom_xy'] == globalz['zoom_xy_max']:
	print("zoom at max")

def patternswitcherZoomOut(target,guitoggle):
    global o, zoomcount, ycenter
    # first remove existing overlay:
    if o != None:
        camera.remove_overlay(o)
    if guitoggle == 1:
        creategui(gui)
    if globalz['zoom_xy'] == globalz['zoom_xy_min']:
        print("zoom at min")

def main():
    global buttoncounter, zoomcount, guiOn, recording, gui5, gui, o, ovl, camera
    try:
        initialize_camera()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        zoom_in()
        patternswitch(gui,1)
        guivisible = 1
        while True:
            if KeyboardPoller.keypressed.isSet():  
                if KeyboardPoller.key=="z":
                    togglepatternZoomIn()
                if KeyboardPoller.key=="x":
                    togglepatternZoomOut()
                if KeyboardPoller.key=="i":
                    loopcount = 14 - zoomcount
                    for x in range(loopcount):
                        togglepatternZoomIn()
                if KeyboardPoller.key=="o":
                    loopcount = zoomcount + 1        
                    for x in range(loopcount):
                        togglepatternZoomOut()
                if KeyboardPoller.key=="n":
                    set_min_zoom()
                    update_zoom()
                    for x in range(14):
    	                zoom_in()
                if KeyboardPoller.key=="p":
		    global roi
                    filename = get_file_name_pic()
		    #pushNotification = "curl --data 'key=XXXXXX&title=Photo Taken&msg='"+filename+" https://api.simplepush.io/send"
   	            print camera.zoom
        	    camera.close()
        	    o = None
        	    roi = str(roi)[1:-1]
        	    roi = re.sub("'","",roi)
        	    roi = re.sub(" ","",roi)
        	    print roi
        	    photo = "raspistill -roi "+roi+" -br 55 -ex auto -o /home/pi/piglass/"+filename+" -rot 270"
        	    subprocess.Popen(photo, shell=True)
        	    time.sleep(1)
        	    photofile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload "+filename+" "+filename
        	    time.sleep(6)
        	    camera = picamera.PiCamera()
        	    subprocess.Popen(photofile, shell=True)
        	    #subprocess.Popen(pushNotification, shell=True)
        	    initialize_camera()
        	    camera.start_preview()
        	    update_zoom()
        	    patternswitch(gui, 1)
                    gui5 = "uploading"
                    togglepatternRecord()
                    toggleonoff()
                    toggleonoff()
        	    time.sleep(1)
                    gui5 = ""
                    togglepatternRecord()
                    toggleonoff()
                    toggleonoff()
		
                if KeyboardPoller.key=="v":           
                    if recording == 0:
        		global videoFile, recording
        		print("recording")
		        videoFile = get_file_name_vid()
                        camera.close()
                        o = None
                        vid = "raspivid -t 0 -o /home/pi/piglass/"+videoFile+" -rot 270"
                        subprocess.Popen(vid, shell=True)
	 	        recording = 1

                if KeyboardPoller.key=="b":           
                    global videoFile, recording
                    recording = 0
        	    o = None
                    kill = "killall raspivid"
                    subprocess.Popen(kill, shell=True)
	            #pushNotification = "curl --data 'key=XXXXXX&title=Video Taken&msg='"+videoFile+" https://api.simplepush.io/send"
                    #subprocess.Popen(pushNotification, shell=True)
        	    #time.sleep(2)
        	    vidfile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload "+videoFile+" "+videoFile
                    subprocess.Popen(vidfile, shell=True)
                    camera = picamera.PiCamera()
                    initialize_camera()
                    camera.start_preview()
	            patternswitch(gui, 1)
                    gui5 = "uploaded"
                    togglepatternRecord()
                    toggleonoff()
                    toggleonoff()
                    time.sleep(1)
                    gui5 = ""
                    togglepatternRecord()
                    toggleonoff()
                    toggleonoff()
                if KeyboardPoller.key=="t":      
	            toggleonoff()
	    KeyboardPoller.WaitKey().thread.start()    

    finally:
        camera.close()               # clean up camera
        GPIO.cleanup()               # clean up GPIO

if __name__ == "__main__":
    main()

