#!/usr/bin/env python3
# coding: utf-8
__author__ = "Carlos Esparza"

# um das Programm zu verstehen sollte man mit Python und insbesondere mit NumPy vertraut
# sein. Wahrscheinlich fängt man am besten mit der Methode num_stars an und schaut sich
# dann die von num_stars aufgerufenen Methode an

from typing import List
import PIL.Image as im
import numpy as np
from collections import namedtuple as NT

Pixel = NT('Pixel', ('pos', 'ab', 'rb', 'db'))
# ab = absolute brightness
#    der Graustufen-Wert des Pixels im Bild

# rb = relative brightness
#    die Helligkeit des Pixels wenn man nach der durchschnittlichen Helligkeit des Bildes
#    normalisiert

# db = delta-brightness
#    um wie viel der Punkt heller ist als seine Umgebung


#------------ relevante Parameter ------------
# für find_points()
DB_MIN_POINT = 4.8
VERSCHIEBUNG = 3
# für aggregate()
AGGREGATE_DIST = 7.5
# für filter_stars() -- eigentlich brauche ich nicht alle diese Parameter
FILTER_AB_MIN = 60
FILTER_RB_MIN = 8.0
FILTER_DB_MIN = 5.0


def find_points(gray: np.array, db=DB_MIN_POINT, s=VERSCHIEBUNG) -> List[Pixel]:
    """"
    gibt eine Liste von Pixel zurück, die viel heller als ihre unmittelbare Umgebung sind

    :param gray: Array mit dem Graustufen der Pixel
    :param db: minimale delta-brightness
    :param s: verschiebung des Arrays
    """
    gnorm = gray / np.average(gray)

    # wir verschieben das Bild/Matrix um s pixel und ziehen 1/4 vom urpsrünglichen Bild ab
    delta = gnorm.copy()
    delta[s:, :]  -= gnorm[:-s, :] / 4
    delta[:-s, :] -= gnorm[s:, :]  / 4
    delta[:, s:]  -= gnorm[:, :-s] / 4
    delta[:, :-s] -= gnorm[:, s:]  / 4
    
    delta = delta[s : -s, s : -s]
    gnorm = gnorm[s : -s, s : -s]
    gray = gray[s : -s, s : -s]
    stars = zip(*np.where(delta > db)) # dark python magic

    return [Pixel(st, gray[st], gnorm[st], delta[st]) for st in stars]

def avg_pos(star):
    """
    der Mittelpunkt eines Sterns (= Liste von Pixel)
    """
    poss = np.array([px[0] for px in star])
    return tuple(np.average(poss, 0))

def star_dist(x, star) -> float:
    """
    gibt den Abstand vom Punkt x zu dem Stern star zurück
    """
    return np.linalg.norm(np.array(x) - np.array(avg_pos(star)))


def aggregate(points: List[Pixel], dist=AGGREGATE_DIST) -> List[Pixel]:
    """
    fasst (helle) Pixel, die näher als dist zusammen liegen zu einem Stern
    (= Liste von Pixel) zusammen
    """
    if len(points) == 0: # randfall
        return []

    stars = [ [points[0]], ]
    for x, *b in points[1:]:
        if star_dist(x, stars[-1]) < dist:
            stars[-1].append(Pixel(x, *b))
        else:
            stars.append([Pixel(x, *b)])
    return stars


def filter_stars(stars: List[Pixel], n=3, ab_min=FILTER_AB_MIN, rb_min=FILTER_RB_MIN,
                 db_min=FILTER_DB_MIN):
    """
    Filtert die sterne heraus, die nicht hell genug sind
    """
    lst = []
    for st in stars:
        if max(pix.db for pix in st) > db_min and \
           max(pix.rb for pix in st) > rb_min and \
           max(pix.ab for pix in st) > ab_min and \
           len(st) >= n:
              lst.append(st)
    return lst


def filter_lone(centers, gray, s=10, avgb=3.0):
    """
    Filtert die Sterne heraus, die eine zu helle umgebung haben
    """
    gnorm = gray / np.average(gray)
    
    lst = []

    for x in centers:
        x = int(round(x[0])), int(round(x[1]))

        neighborhood = gnorm[x[0] - s : x[0] + s, x[1] - s : x[1] + s] + 0.05

        if np.exp(np.average(np.log(neighborhood))) < avgb:
            lst.append(x)
    return lst


def num_stars(gray: np.array) -> int:
    """
    gibt zurück wie viele Sterne sich in dem übergebenen array befinden
    """
    S = 3
    points = find_points(gray, S) # helle Pixel finden
    gray = gray[S:-S, S:-S]
    candidates = aggregate(points) # nahe Pixel zu einem "Stern" zusammenfassen

    stars = filter_stars(candidates)
    centers = filter_lone([avg_pos(st) for st in stars], gray)

    return len(centers)

def clouded(gray: np.array) -> float:
    """
    gibt einen Cloud-cover Wert für das Bild zurück
    """
    x2, y2 = gray.shape[0] // 2, gray.shape[1] // 2 # Koordinaten des Mittelpunkts

    # Das bild (ein 2D-array aus Graustufenwerten) wird in 4 Quadranten eingeteilt
    a, b, c, d = ( num_stars(gray[:x2+3, :y2+3]), num_stars(gray[x2-3:, :y2+3]),
                   num_stars(gray[:x2+3, y2-3:]), num_stars(gray[x2-3:, y2-3:]) )

    # für jeden Quadranten, in dem kein Stern sichtbar ist beträgt der cloudcover-Wert 0.25
    return 1 - ((a > 0) +
                (b > 0) +
                (c > 0) +
                (d > 0))\
                / 4


if __name__ == '__main__': # test ... nicht weiter beachten
    import sys
    folder = 'sky'

    if len(sys.argv) > 1:
        folder = sys.argv[1]

    for i in range(10):
        S = 3

        image = im.open('{}/{}.jpg'.format(folder, i))
        gray = np.asarray(image.convert('LA'))[..., 0]
        imgarr = np.asarray(image)


        print('image', i, 'clouded:', clouded(gray))

        imgarr = imgarr[S:-S, S:-S]

