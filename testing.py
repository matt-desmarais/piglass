from subprocess import call
import RPi.GPIO as GPIO
import picamera
import time
import sys
import datetime
import cv2
import numpy as np
import KeyboardPoller

height = 600
width = 800
alphaValue = 64
o = None
recording = 0

camera = picamera.PiCamera()
global zoomcount
zoomcount=0
globalCounter = 0

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
    #camera.rotation = -90
    camera.hflip = False
    camera.vflip = False
    camera.start_preview()
    print "Camera is configured and outputting video..."

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
}

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
alphaValue = 64

# initial config for gpio ports
#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM)

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
gui3 = 'P Key = take pic'
gui4 = 'V Key = take video'
gui5 = ' '

def get_file_name_pic():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def get_file_name_vid():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.h264")

def creategui(target):
    global gui5
    cv2.putText(target, gui1, (10,height-138), font, 10, col, 4)
    cv2.putText(target, gui2, (10,height-108), font, 2, col, 2)
    cv2.putText(target, gui3, (10,height-78), font, 2, col, 2)
    cv2.putText(target, gui4, (10,height-48), font, 2, col, 2)
    cv2.putText(target, gui5, (10,height-18), font, 2, col, 2)
    #camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def patternswitch(target,guitoggle):
    global o, alphaValue
    # first remove existing overlay:
    # cycle through possible patterns:
    #if o != None:
    #	camera.remove_overlay(o)
    toggleonoff()
    if guitoggle == 1:
	    creategui(gui)
    o = camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def patternswitcherRecord(target,guitoggle):
    global o, zoomcount, ycenter
    # first remove existing overlay:
    #if o != None:
    #    camera.remove_overlay(o)
    if guitoggle == 1:
        creategui(gui)

# function 
def togglepatternRecord():
    global togsw,o,curpat,col,ovl,gui,alphaValue,ycenter,zoomcount
    # if overlay is inactive, ignore button:
    if togsw == 0:
        print "Pattern button pressed, but ignored --- Crosshair not visible."
	#zoom_in()
	#ycenter = ycenter + zoomcount
    # if overlay is active, drop it, change pattern, then show it again
    else:
        if guivisible == 0:
            #zoom_in()
	    # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitcherRecord(ovl,0)
	    #if o != None:
            #    camera.remove_overlay(o)
            #o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
	else:
            # reinitialize array
            #zoom_in()
	    gui = np.zeros((height, width, 3), dtype=np.uint8)
	    creategui(gui)
            patternswitcherRecord(gui,1)
            #if o != None:
            #    camera.remove_overlay(o)
            #o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
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
	#ycenter = ycenter + zoomcount
    # if overlay is active, drop it, change pattern, then show it again
    else:
        if guivisible == 0:
            zoom_in()
	    # reinitialize array:
            ovl = np.zeros((height, width, 3), dtype=np.uint8)
            patternswitcherZoomIn(ovl,0)
	    #if o != None:
            #    camera.remove_overlay(o)
            #o = camera.add_overlay(np.getbuffer(ovl), layer=3, alpha=alphaValue)
	else:
            # reinitialize array
            zoom_in()
	    gui = np.zeros((height, width, 3), dtype=np.uint8)
	    creategui(gui)
            patternswitcherZoomIn(gui,1)
            #if o != None:
            #    camera.remove_overlay(o)
            #o = camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
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
    global buttoncounter, zoomcount, guiOn, recording, gui5, gui, o, ovl
    try:
        initialize_camera()
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
                if KeyboardPoller.key=="c":
                    if buttoncounter == 0:
                        for x in range(14-zoomcount):
                            togglepatternZoomIn()
                            time.sleep(.1)
                        buttoncounter=1
                    else:
                        for x in range(zoomcount+1):
                            togglepatternZoomOut()
                            zoomcount = 0
                            time.sleep(.1)
                        buttoncounter=0
                if KeyboardPoller.key=="n":
                    set_min_zoom()
                    zoom_in()
    	            zoom_in()
    	            zoom_in()
                    zoom_in()
                    zoom_in()
                    zoom_in()
                    zoom_in()
                if KeyboardPoller.key=="p":
                    filename = get_file_name_pic()
                    camera.capture(filename, use_video_port=True)
		    gui5 = "Took Photo"
		    togglepatternRecord()
                    toggleonoff()
                    toggleonoff()
		    time.sleep(2)
	            gui5 = ""
		    togglepatternRecord()
		    toggleonoff()
                    toggleonoff()
                if KeyboardPoller.key=="v":           
                    if recording == 0:
                        set_min_zoom()
                        filename = get_file_name_vid()
			#if o != None:
                	#    camera.remove_overlay(o)
			gui5 = "RECORDING"
			togglepatternRecord()
			toggleonoff()
                        toggleonoff()
			camera.start_recording(filename)
                        print('recording')
                        recording = 1
                    else:
                        set_min_zoom()
			camera.stop_recording()
                        recording = 0
                        zoom_in()
                        zoom_in()
                        zoom_in()
                        zoom_in()
                        zoom_in()
                        zoom_in()
                        zoom_in()
			gui5 = " "
			creategui(gui)
			togglepatternRecord()
			toggleonoff()
                        toggleonoff()
                        print('not recording') 
                if KeyboardPoller.key=="t":      
		     toggleonoff()
	    KeyboardPoller.WaitKey().thread.start()    

    finally:
        camera.close()               # clean up camera
        GPIO.cleanup()               # clean up GPIO

if __name__ == "__main__":
    main()
