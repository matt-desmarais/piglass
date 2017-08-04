from subprocess import call
import RPi.GPIO as GPIO
import picamera
import time
import sys
import datetime
import cv2
import numpy as np

globals = {
    'zoom_step'     : 0.03,

    'zoom_xy_min'   : 0.0,
    'zoom_xy'       : 0.0,
    'zoom_xy_max'   : 0.4,

    'zoom_wh_min'   : 1.0,
    'zoom_wh'       : 1.0,
    'zoom_wh_max'   : 0.2
}

camera = picamera.PiCamera()

# initial config for gpio ports
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

pin_17 = False
pin_18 = False
pin_26 = False

alphaValue = 64

height = 600
width = 800

if (width%32) > 0 or (height%16) > 0:
    print "Rounding down set resolution to match camera block size:"
    width = width-(width%32)
    height = height-(height%16)
    print "New resolution: " + str(width) + "x" + str(height)

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
#height = 600
#width = 800

gui = np.zeros((height, width, 3), dtype=np.uint8)
gui1 = 'PiGlass'
gui2 = 'Version 0.1 alpha'
gui3 = 'button  = take pic'

#def colormap(col):
#    return colors.get(col, (255,255,255))

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
    #set zoom to (almost) line up with your field of vision
    zoom_in()
    zoom_in()
    zoom_in()
    zoom_in()
    zoom_in()
    zoom_in()
    zoom_in()
    # (x, y, w, h)
    #set_min_zoom()
    camera.start_preview()
    print "Camera is configured and outputting video..."

def update_zoom():
    #print "Setting camera to (%s, %s, %s, %s)" % (globals['zoom_xy'], globals['zoom_xy'], globals['zoom_wh'], globals['zoom_wh'])
    camera.zoom = (globals['zoom_xy'], globals['zoom_xy'], globals['zoom_wh'], globals['zoom_wh'])
    print "Camera at (x, y, w, h) = ", camera.zoom

def set_min_zoom():
    globals['zoom_xy'] = globals['zoom_xy_min']
    globals['zoom_wh'] = globals['zoom_wh_min']

def set_max_zoom():
    globals['zoom_xy'] = globals['zoom_xy_max']
    globals['zoom_wh'] = globals['zoom_wh_max']

def zoom_out():
    if globals['zoom_xy'] - globals['zoom_step'] < globals['zoom_xy_min']:
        set_min_zoom()
    else:
        globals['zoom_xy'] -= globals['zoom_step']
        globals['zoom_wh'] += (globals['zoom_step'] * 2)
    update_zoom()

def zoom_in():
    if globals['zoom_xy'] + globals['zoom_step'] > globals['zoom_xy_max']:
        set_max_zoom()
    else:
        globals['zoom_xy'] += globals['zoom_step']
        globals['zoom_wh'] -= (globals['zoom_step'] * 2)
    update_zoom()

def get_file_name():  # new
    return datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S.jpg")

def creategui(target):
    cv2.putText(target, gui1, (10,height-138), font, 10, col, 4)
    cv2.putText(target, gui2, (10,height-108), font, 2, col, 2)
    cv2.putText(target, gui3, (10,height-78), font, 2, col, 2)
    #camera.add_overlay(np.getbuffer(target), layer=3, alpha=alphaValue)
    return

def button_pressed_26(pin):
    global pin_26
    print "pin:", pin
    #camera.stop_preview()
    filename = get_file_name()
    camera.capture(filename, use_video_port=True)
    #camera.start_preview()

def button_pressed_21(pin):
    print "Exiting..."
    camera.stop_preview()
    sys.exit(0)

def button_pressed_17(pin):
    global pin_17
    print "pin:", pin
    zoom_in()
    #print "pin_17", pin_17
    #while pin_17 == True:
    #    print('GPIO #17 button pressed')
    #    time.sleep(0.2)

def button_pressed_18(pin):
    global pin_18
    print "pin:", pin
    zoom_out()
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
    GPIO.add_event_detect(18, GPIO.FALLING, callback=button_pressed_18, bouncetime=200)
    GPIO.add_event_detect(26, GPIO.FALLING, callback=button_pressed_26, bouncetime=200)

    print "Button Listeners are configured and listening..."

def main():
    configure_button_listeners()
    initialize_camera()
    gui = np.zeros((height, width, 3), dtype=np.uint8)
    creategui(gui)
    camera.add_overlay(np.getbuffer(gui), layer=3, alpha=alphaValue)
    raw_input() # Run the loop function to keep script running

if __name__ == "__main__":
    main()
