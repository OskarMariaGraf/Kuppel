#!/usr/bin/env python3
# coding=utf-8
#-------------------------------------------------------------------------------
# Name:       photographer
# Created:    21.10.16

__author__ = 'Carlos Esparza-Sanchez'
#-------------------------------------------------------------------------------

from .stars import *
import picamera
from time import sleep, time
from io import BytesIO
import PIL.Image as im
import os
import logging
import threading

PIPE_IN_NAME = '/tmp/camin'
PIPE_OUT_NAME = '/tmp/camout'

T = 1.0 # Zeitintervall, in dem Bilder gemacht werden

def eval_sky():
    global cloud_cover
    logger = logging.Logger('photographer', logging.INFO)

    while True:
        t = time()
        stream = BytesIO()  # wir emulieren eine Datei

        # das with-statement sagt Python es soll sich um das schließen von devices etc. kümmern
        with picamera.PiCamera() as camera:
            # einstellungen für Photographie mit wenig Licht
            camera.framerate = 1 / 4
            camera.shutter_speed = 4000000
            camera.exposure_mode = 'off'
            camera.iso = 600
            camera.capture(stream, format='jpeg')  # Photo schießen

        logger.info('Bild gemacht')
        image = im.open(BytesIO(stream.getvalue()))
        gray = np.asarray(image.convert('LA'))[..., 0]
        cloud_cover = clouded(gray)
        logging.debug('Cloudcover beträgt {}')

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
