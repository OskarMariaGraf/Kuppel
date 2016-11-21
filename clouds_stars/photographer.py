#!/usr/bin/env python3
# coding=utf-8
#-------------------------------------------------------------------------------
# Name:       photographer
# Created:    21.10.16

__author__ = 'Carlos Esparza-Sanchez'
#-------------------------------------------------------------------------------

from .stars import *
import numpy as np
import picamera
from time import sleep, time
from io import BytesIO
import PIL.Image as im
import os
import logging
import threading

PIPE_IN_NAME = '/tmp/camin'
PIPE_OUT_NAME = '/tmp/camout'

BASE_SS = 4000000 # Belichtungszeit in microsekunden - und ja, der Name ist Zufall
ISO = 600

T = 1.0 # Zeitintervall, in dem Bilder gemacht werden

def eval_sky():
    global cloud_cover
    logger = logging.Logger('photographer', logging.INFO)
    shutter_speed = BASE_SS

    while True:
        t = time()
        stream = BytesIO()  # wir emulieren eine Datei

        # das with-statement sagt Python es soll sich um das schließen von devices etc. kümmern
        with picamera.PiCamera() as camera:
            # einstellungen für Photographie mit wenig Licht
            camera.framerate = 1 / 4
            camera.shutter_speed = shutter_speed
            camera.exposure_mode = 'off'
            camera.iso = ISO
            camera.capture(stream, format='jpeg')  # Photo schießen

        logger.info('Bild gemacht')
        image = im.open(BytesIO(stream.getvalue()))
        gray = np.asarray(image.convert('LA'))[..., 0]

        if all(gray == 0) : continue # wir wollen keine schwarzen Bilder auswerten...tter_speed * 1.25)
        cloud_cover = clouded(gray)
        logger.info('Cloudcover beträgt {}'.format(cloud_cover))

        helligkeit = np.average(gray)

        if helligkeit > 45:
            shutter_speed = max(shutter_speed * 0.8, 1)
            logger.info('Beleuchtungszeit auf {} ms heruntergesetzt'.format(shutter_speed))
        elif helligkeit < 15 and shutter_speed < BASE_SS:
            shutter_speed = min(BASE_SS, shutter_speed * 1.2)
            logger.info('Beleuchtungszeit auf {} ms heraufgesetzt'.format(shutter_speed))


        sleep(T + t - time())  # jeder Durchgang der Schleife soll mindestens T minuten dauern


if os.path.exists(PIPE_IN_NAME):
    os.remove(PIPE_IN_NAME)

if os.path.exists(PIPE_OUT_NAME):
    os.remove(PIPE_OUT_NAME)

os.mkfifo(PIPE_IN_NAME)
os.mkfifo(PIPE_OUT_NAME)
logging.debug('alte pipes gelöscht, neue erstellt')

photo_thread = threading.Thread(target=eval_sky, name='eval_sky')

cloud_cover = 1.0
photo_thread.run()

while True:
    # ich kann mich nicht entscheiden, ob das genial, oder zum Kotzen ist - funktioniert aber
    with open(PIPE_IN_NAME, 'rb', 0): pass
    logging.log('Anfrage erhalten')

    with open(PIPE_OUT_NAME, 'wb', 0) as pipe_out:
        cc = cloud_cover # nur einzelne statements sind in Python atomic
        pipe_out.write( bytes([0, 0, 0, int(100 * cc)]) )

    logging.info('Cloudcover-Wert {} an Server geschickt'.format(100 * cc))
