#!/usr/bin/env python3
# coding=utf-8
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
import os

PIPE_IN_NAME = '/tmp/camin'
PIPE_OUT_NAME = '/tmp/camout'

T = 1.0 # Zeitintervall, in dem Bilder gemacht werden

os.remove(PIPE_IN_NAME)
os.remove(PIPE_OUT_NAME)

os.mkfifo(PIPE_IN_NAME)
os.mkfifo(PIPE_OUT_NAME)

# die Pipes werden zur Kommunikation mit dem Server verwendet - vgl. Server.cpp
with open(PIPE_IN_NAME, 'rb') as pipe_in, open(PIPE_OUT_NAME, 'wb') as pipe_out:
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
        gray = np.asarray(image.convert('LA'))[..., 0]
        cloud_cover = clouded(gray)

        pipe_in.read() # warten auf Anfrage
        pipe_out.write( bytes([0, 0, 0, int(100 * cloud_cover)]) )


        sleep(T + t - time()) # jeder Durchgang der Schleife soll mindestens T minuten dauern



