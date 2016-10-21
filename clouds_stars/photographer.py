#!/usr/bin/env python3
#-------------------------------------------------------------------------------
# Name:       photographer
# Purpose:    
# Created:    21.10.16
__author__ = 'Carlos Esparza-Sanchez'
#-------------------------------------------------------------------------------

from stars import *
import picamera
from time import sleep, time
from io import BytesIO
import PIL.Image as im


T = 1.0 # Zeitintervall, in dem Bilder gemacht werden


while True: #TODO: hier sollten wir vielleicht Uhrzeiten abfragen
    stream = BytesIO() # wir emulieren eine Datei
    t = time()

    # das with-statement sagt Python es soll sich um das schließen von devices etc. kümmern
    with picamera.PiCamera() as camera:
        # einstellungen für Photographie mit wenig Licht
        camera.framerate = 1/4
        camera.shutter_speed = 4000000
        camera.exposure_mode = 'off'
        camera.iso = 600
        camera.capture(stream, format='jpeg') # Photo schießen

    image = im.open(stream.getvalue())
    print(clouded(image))

    sleep(T + t - time()) # jeder Durchgang der Schleife soll  T minuten dauern



