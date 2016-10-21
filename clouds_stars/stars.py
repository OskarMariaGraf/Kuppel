#!/ust/bin/env python3
# coding: utf-8
import PIL.Image as im
import numpy as np
from collections import namedtuple as NT


Pixel = NT('Pixel', ('pos', 'ab', 'rb', 'db')) #absolute brightness, relative brightness, delta-brightness


def find_stars(gray, b=4.8, s=3):
    gnorm = gray / np.average(gray)
    delta = gnorm.copy()
    delta[s:, :]  -= gnorm[:-s, :] / 4
    delta[:-s, :] -= gnorm[s:, :]  / 4
    delta[:, s:]  -= gnorm[:, :-s] / 4
    delta[:, :-s] -= gnorm[:, s:]  / 4
    
    delta = delta[s : -s, s : -s]
    gnorm = gnorm[s : -s, s : -s]
    gray = gray[s : -s, s : -s]
    stars = list(zip(*np.where(delta > b)))

    return [Pixel(st, gray[st], gnorm[st], delta[st]) for st in stars]

def avg_pos(star):
    poss = np.array([px[0] for px in star])
    return tuple(np.average(poss, 0))

def star_dist(x, star):
    return np.linalg.norm(np.array(x) - np.array(avg_pos(star)))


def aggregate(points, dist=7.5):
    if len(points) == 0:
        return []

    stars = [ [points[0]], ]
    for x, *b in points[1:]:
        if np.linalg.norm(star_dist(x, stars[-1])) < dist:
            stars[-1].append(Pixel(x, *b))
        else:
            stars.append([Pixel(x, *b)])
    return stars


def filter_stars(stars, n=3, abmin=60, rbmin=8.0, dbmin=5.0):
    lst = []
    for st in stars:
        if max(pix.db for pix in st) > dbmin and \
           max(pix.rb for pix in st) > rbmin and \
           max(pix.ab for pix in st) > abmin and \
           len(st) >= n:
              lst.append(st)
    return lst


def filter_lone(centers, gray, s=10, avgb=3.0): #testet ob die Umgebung der Sterne dunkel ist
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
    points = find_stars(gray, S)
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
        
        # points = find_stars(gray, S)

        # gray = gray[S:-S, S:-S]

        # candidates = aggregate(points)

        # stars = filter_stars(candidates)
        # centers = filter_lone([avg_pos(st) for st in stars], gray)


        print('image', i, 'clouded:', clouded(gray))

        imgarr = imgarr[S:-S, S:-S]

        # mark(imgarr, centers)

        # excands = []
        # for star in candidates:
        #     if star in stars: continue
        #     pt = avg_pos(star)
        #     pt = (int(pt[0]), int(pt[1]))
        #     #if pt in centers: continue
        #     excands.append(pt)

        # exstars = []
        # for star in stars:
        #     pt = avg_pos(star)
        #     pt = (int(pt[0]), int(pt[1]))
        #     if pt in centers: continue
        #     exstars.append(pt)

        # #mark(imgarr, excands, s=16, col=(45, 45, 230), thick=2)
        # mark(imgarr, exstars, s=20, col=(50, 220, 220), thick=3)


        # cv.namedWindow('stars.py', cv.WINDOW_NORMAL)
        # cv.imshow('stars.py', imgarr)
        # cv.imwrite('{}/{}-parsed.jpg'.format(folder, i), imgarr)
        # cv.resizeWindow('stars.py', 1000, 1180)
        # cv.waitKey()

        
