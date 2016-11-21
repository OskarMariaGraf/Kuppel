#!/usr/bin/env python3
# coding=utf-8
#-------------------------------------------------------------------------------
# Name:       photographer
# Created:    21.10.16

__author__ = 'Carlos Esparza-Sanchez'
#-------------------------------------------------------------------------------

# das Programm macht jede Minute ein Bild vom Himmel und berechnet einen cloudcover-Wert
# Auf Anfrage des Servers wird der letzte ermittelte Cloudcover-Wert übergeben.
# Die logging-Befehle dokumentieren das Programm relativ gut

from stars import *
import numpy as np
import picamera
from time import sleep, time
from io import BytesIO
import PIL.Image as im
import os
import logging
import threading
import argparse

PIPE_IN_NAME = '/tmp/camin'
PIPE_OUT_NAME = '/tmp/camout'

BASE_SS = 4000000 # Belichtungszeit in microsekunden - und ja, der Name ist Zufall
ISO = 600
T = 60.0 # Zeitintervall, in dem Bilder gemacht werden

parser = argparse.ArgumentParser(description='Bestimmt cloudcover anhand der Anzahl an '
                                             'sichtbaren Sternen')
parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG,
                    default=logging.WARN, help='Debug-Informationen ausgeben')

parser.add_argument('-c', '--collect', action='store_const', const=True, default=False,
                    help='cloudcover-Werte speichern')
args = parser.parse_args()

LOGLEVEL = args.debug


def eval_sky():
    global cloud_cover # der cloudcover-Wert wird über diese Variable übermittelt

    # Logging
    logger = logging.getLogger('photographer')
    logger.setLevel(LOGLEVEL)

    fh = logging.FileHandler('cloudcover.log')
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s  %(name)s: %(levelname)s: %(message)s',
                            datefmt='%d. %m. %Y %I:%M:%S')
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    if args.collect:
        f = open('data.csv', 'w')

    logger.debug('Thread eval_sky gestartet')
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

        if (gray == 0).all() : continue # wir wollen keine schwarzen Bilder auswerten...
        cloud_cover = clouded(gray)
        logger.info('Cloudcover beträgt {}'.format(cloud_cover))

        if args.collect:
            f.write('{}\n'.format(cloud_cover))

        helligkeit = np.average(gray)
        logger.info('Helligkeit beträgt {:.3g}'.format(helligkeit))


        # falls das Bild zu hell ist wird die Belichtungszeit reduziert
        # helligkeitswerte zwischen 20 und 40 werden angepeilt
        if helligkeit > 100:
            shutter_speed *= 50 / helligkeit # Notbremse
        elif helligkeit > 45:
            shutter_speed = max(shutter_speed * 0.8, 1)
            logger.info('Beleuchtungszeit auf {} ms heruntergesetzt'.format(shutter_speed))
        elif helligkeit < 15 and shutter_speed < BASE_SS:
            shutter_speed = min(BASE_SS, shutter_speed * 1.2)
            logger.info('Beleuchtungszeit auf {} ms heraufgesetzt'.format(shutter_speed))


        sleep(T + t - time())  # jeder Durchgang der Schleife soll mindestens T sekunden dauern

logging.root.setLevel(LOGLEVEL)

if os.path.exists(PIPE_IN_NAME):
    os.remove(PIPE_IN_NAME)

if os.path.exists(PIPE_OUT_NAME):
    os.remove(PIPE_OUT_NAME)

os.mkfifo(PIPE_IN_NAME)
os.mkfifo(PIPE_OUT_NAME)
logging.debug('alte pipes gelöscht, neue erstellt')

photo_thread = threading.Thread(target=eval_sky, name='Thread-eval_sky')

cloud_cover = 1.0
photo_thread.start()

logging.debug('starte main loop')
while True:
    # ich kann mich nicht entscheiden, ob das genial, oder zum Kotzen ist - funktioniert aber
    with open(PIPE_IN_NAME, 'rb', 0): pass
    logging.debug('Anfrage erhalten')

    with open(PIPE_OUT_NAME, 'wb', 0) as pipe_out:
        cc = cloud_cover # nur einzelne statements sind in Python atomic
        pipe_out.write( bytes([0, 0, 0, int(100 * cc)]) )

    logging.info('Cloudcover-Wert {} an Server geschickt'.format(100 * cc))
