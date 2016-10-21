#!/usr/bin/env python3
# coding: utf-8

__author__ = "Carlos Esparza"

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


def find_points(gray: np.array, b=4.8, s=3) -> List[Pixel]:
    """"
    gibt eine Liste von Pixel zurück, die viel heller als ihre unmittelbare Umgebung sind

    :param gray: Array mit dem Graustufen der Pixel
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
    stars = zip(*np.where(delta > b)) # dark python magic

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


def aggregate(points: List[Pixel], dist=7.5) -> List[Pixel]:
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


def filter_stars(stars: List[Pixel], n=3, ab_min=60, rb_min=8.0, db_min=5.0):
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


#def mark(image, centers, s=25, col=(50, 255, 50), thick=4):
#    for c in centers:
#        y, x = int(c[0]), int(c[1])
#        cv.rectangle(image, (x - s, y - s), (x + s, y + s), col, thick)


def num_stars(gray):
    S = 3
    points = find_points(gray, S)
    gray = gray[S:-S, S:-S]
    candidates = aggregate(points)

    stars = filter_stars(candidates)
    centers = filter_lone([avg_pos(st) for st in stars], gray)

    return len(centers)

def clouded(gray):
    x2, y2 = gray.shape[0] // 2, gray.shape[1] // 2

    a, b, c, d = ( num_stars(gray[:x2+3, :y2+3]), num_stars(gray[x2-3:, :y2+3]),
                   num_stars(gray[:x2+3, y2-3:]), num_stars(gray[x2-3:, y2-3:]) )

    return 1 - ((a > 0) + (b > 0) + (c > 0) + (d > 0)) / 4


if __name__ == '__main__':
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
        
