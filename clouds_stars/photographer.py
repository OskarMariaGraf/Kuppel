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
TERMINATED = False


def eval_sky():
    global cloud_cover # der cloudcover-Wert wird über diese Variable übermittelt

    # Logging
    logger = logging.getLogger('photographer')
    logger.setLevel(LOGLEVEL)

    # logs werden in die Datei cloudcover.log geschrieben, das Format ist relativ
    # selbsterklärend
    fh = logging.FileHandler('cloudcover.log')
    fh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s  %(name)s: %(levelname)s: %(message)s',
                            datefmt='%d.%m.%Y %I:%M:%S')
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
        # aus irgendeinem Grund kann man nicht aus dem Stream in den geschrieben wurde
        # lesen, also wird ein neuer Stream mit dem gleich Inhalt erstellt und an im.open
        # übergeben wie wenn er ein Datei-objekt wäre
        image = im.open(BytesIO(stream.getvalue()))
        gray = np.asarray(image.convert('LA'))[..., 0] # in Graustufen-Array konvertieren

        # es ist ein Paar mal passiert, dass die Bilder vollkommen schwarz waren - in
        # diesem Fall machen wir einfach ein neues
        if (gray == 0).all() : continue

        cloud_cover = clouded(gray)
        logger.info('Cloudcover beträgt {}'.format(cloud_cover))

        if args.collect:
            f.write('{} '.format(cloud_cover))
            f.flush()

        helligkeit = np.average(gray) # mittlere Helligekeit des Bildes
        logger.info('Helligkeit beträgt {:.3g}'.format(helligkeit))


        # falls das Bild zu hell ist wird die Belichtungszeit reduziert
        # helligkeitswerte zwischen 20 und 40 werden angepeilt - die Regeln zur
        # Reduzierung der Belichtungszeit sind relativ willkürlich
        if helligkeit > 100:
            shutter_speed = int(shutter_speed * 50 / helligkeit) # Notbremse
            logger.info('Beleuchtungszeit auf {:.4g} ms heruntergesetzt'
                        .format(shutter_speed / 1000))
        elif helligkeit > 45:
            shutter_speed = max(int(shutter_speed * 0.8), 1)
            logger.info('Beleuchtungszeit auf {:.4g} ms heruntergesetzt'
                        .format(shutter_speed / 1000))
        elif helligkeit < 15 and shutter_speed < BASE_SS:
            shutter_speed = min(BASE_SS, int(shutter_speed * 1.2))
            logger.info('Beleuchtungszeit auf {:.4g} ms heraufgesetzt'
                        .format(shutter_speed / 1000))

        if not TERMINATED:
            # jeder Durchgang der Schleife soll T sekunden dauern
            sleep(T + t - time())
        else: # anscheinend wurden wir beendet...
            f.close()
            return


logging.root.setLevel(LOGLEVEL)

if os.path.exists(PIPE_IN_NAME): # lösche eventuell noch vorhandene alte pipes
    os.remove(PIPE_IN_NAME)

if os.path.exists(PIPE_OUT_NAME):
    os.remove(PIPE_OUT_NAME)

os.mkfifo(PIPE_IN_NAME) # erstelle neue pipes
os.mkfifo(PIPE_OUT_NAME)
logging.debug('alte pipes gelöscht, neue erstellt')

# erstelle Thread, der jede Minute ein Bild von Himmel auswertet und den cloudcover-Wert
# in die variable cloud_cover schreibt
photo_thread = threading.Thread(target=eval_sky, name='Thread-eval_sky')

cloud_cover = 1.0
photo_thread.start()

logging.debug('starte main loop')

# normale (blocking) pipes haben aus irgendeinem Grund nicht Funktioniert
# fin = os.open(PIPE_IN_NAME, os.O_NONBLOCK)
pipe_out = os.open(PIPE_OUT_NAME, os.O_NONBLOCK)

while True:
    try:
        logging.debug('warte auf Anfrage...')
        # while not os.read(fin, 1):
        #    sleep(0.2) # 5x pro Sekunde sollte reichen...
        with open(PIPE_IN_NAME, 'rb', 0) as f: f.read(1)
        logging.debug('Anfrage erhalten')

        # with open(PIPE_OUT_NAME, 'wb', 0) as pipe_out:
        cc = cloud_cover # nur einzelne statements sind in Python atomic
        os.write(pipe_out, bytes([int(100 * cc), 0, 0, 0, 0, 0, 0, 0]) ) # raspbian ist little-endian

        logging.info('Cloudcover-Wert {} an Server geschickt'.format(100 * cc))
    except:
        TERMINATED = True
        logging.exception('Programm wird Beendet')
        photo_thread.join()
        raise #re-raise
