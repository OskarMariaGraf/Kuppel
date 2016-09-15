#!/ust/bin/env python3
# coding: utf-8
import cv2 as cv
import numpy as np

def find_stars(image, b=6.0, s=3):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    gnorm = gray / np.average(gray)
    delta = gnorm.copy()
    delta[s:, :]  -= gnorm[:-s, :] / 4
    delta[:-s, :] -= gnorm[s:, :]  / 4
    delta[:, s:]  -= gnorm[:, :-s] / 4
    delta[:, :-s] -= gnorm[:, s:]  / 4
    
    delta = delta[s : -s, s : -s]
    
    stars = zip(*np.where(delta > b))
    return list(stars)
    
    
def aggregate(points, dist=7.5):
    if len(points) == 0:
        return []

    stars = [ [points[0]], ]
    for x in points[1:]:
        if np.linalg.norm(x - np.average(stars[-1], 0)) < 7.5:
            stars[-1].append(x)
        else:
            stars.append([x])
    return stars
    
    
def mark(image, centers, s=25):
    for c in centers:
        y, x = int(c[0]), int(c[1])
        cv.rectangle(image, (x - s, y - s), (x + s, y + s), (255, 50, 50), 4)
        

if __name__ == '__main__':
    for i in range(10):
        image = cv.imread('sky/{}.jpg'.format(i))
        
        points = find_stars(image)
        stars = aggregate(points)
        centers = [np.average(st, 0) for st in stars]
        
        mark(image, centers)
        
        cv.namedWindow('stars.py', cv.WINDOW_NORMAL)
        cv.imshow('stars.py', image)
        cv.imwrite('sky/{}-parsed.jpg'.format(i), image)
        cv.resizeWindow('stars.py', 1000, 1180)
        cv.waitKey()
        
        
        
