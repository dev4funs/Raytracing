import numpy as np
from PIL import Image
from math import sqrt

MAXITER = 6
SAVE = True
WIDTH = 320
HEIGHT = 240
SCREENDIS = 1
PICLEN = 0.001
FPFIXER = 1e-11
ENABLEREFLECT = False


class Position:
    def __init__(self, x, y, z):
        self.arr = np.array([x, y, z], dtype=float)

    def __add__(self, other):
        arr = self.arr + other.arr
        return Position(arr[0], arr[1], arr[2])

    def __sub__(self, other):
        arr = self.arr - other.arr
        return Position(arr[0], arr[1], arr[2])

    def __mul__(self, other):
        arr = np.multiply(self.arr, other)
        return Position(arr[0], arr[1], arr[2])

    def dot(self, other):
        return np.dot(self.arr, other.arr)

    def length(self):
        return sqrt(np.dot(self.arr, self.arr))

    def cosine(self, other):
        return self.dot(other) / (self.length() * other.length())

    def reflect(self, axis):
        L = self.arr
        N = axis.arr
        arr = (2 * self.dot(axis)) * N - L
        return Position(arr[0], arr[1], arr[2])


class color:
    def __init__(self, r, g, b):
        self.arr = np.array([r, g, b], dtype=int)

    def __add__(self, other):
        arr = self.arr + other.arr
        for i in range(3):
            if arr[i] > 255:
                arr[i] = 255
        return color(arr[0], arr[1], arr[2])

    def dimm(self, other):
        arr = np.array([0, 0, 0], dtype=int)
        for i in range(3):
            arr[i] = int(self.arr[i] * other.arr[i] / 255)
        return color(arr[0], arr[1], arr[2])

    def __mul__(self, other):
        arr = np.multiply(self.arr, other)
        for i in range(3):
            if arr[i] < 0:
                arr[i] = 0
        return color(arr[0], arr[1], arr[2])

    def __eq__(self, other):
        return self.arr.all() == other.arr.all()


class instance:
    def __init__(self, x, y, z):
        self.position = Position(x, y, z)


class light(instance):
    def __init__(self, x, y, z, r, g, b):
        super().__init__(x, y, z)
        self.color = color(r, g, b)


class sphere(instance):
    def __init__(self, x, y, z,
                 r, g, b,
                 rad=1, shine=8,
                 kar=200, kag=200, kab=200,
                 kdr=150, kdg=150, kdb=150,
                 ksr=30, ksg=30, ksb=30, reflect=0):
        super().__init__(x, y, z)
        self.color = color(r, g, b)
        self.radius = rad
        self.shine = shine
        self.ka = color(kar, kag, kab)
        self.kd = color(kdr, kdg, kdb)
        self.ks = color(ksr, ksg, ksb)
        self.reflect = reflect

    def normal(self, pos):
        return pos - self.position

    def intersect(self, o, d):  # find t for o + td
        a = d.dot(d)
        tmp = o - self.position
        b = (tmp * 2).dot(d)
        c = tmp.dot(tmp) - self.radius ** 2

        det = b ** 2 - 4 * a * c
        if det < 0:
            return
        t1 = (-sqrt(det) - b) / (2 * a)
        t2 = (sqrt(det) - b) / (2 * a)

        if t2 < 0:
            return
        if t1 < 0:
            return t2
        return min(t1, t2)


BLACK = color(0, 0, 0)
Ia = color(20, 20, 20)


def finddir(w, h, e):
    m_x = int(WIDTH / 2)
    m_y = int(HEIGHT / 2)
    p = Position((w - m_x) * PICLEN, SCREENDIS, (m_y - h) * PICLEN)
    p = p - e.position
    return (p)


def max3(a, b, c):
    if a > b:
        if a > c:
            return a
        return c
    elif b > c:
        return b
    return c


def hits(source, dir, spheres):
    if spheres is None:
        return False
    for s in spheres:
        if s.intersect(source, dir):
            return True
    return False


def raycast(source, dir, spheres, lights, n=0):
    if n == MAXITER:
        return BLACK

    c = BLACK
    min = float("inf")
    sph = None

    if spheres is None:
        return BLACK

    for s in spheres:
        position = s.intersect(source, dir)
        if position is not None and position < min:
            min = position
            sph = s

    if sph is not None:
        intersection = source + dir * (min - FPFIXER)
        norm = sph.normal(intersection)
        Illu = BLACK
        for li in lights:
            ldir = li.position - intersection

            if hits(intersection, ldir, spheres):
                Ie = BLACK
            else:
                Ie = li.color

            Illa = Ia.dimm(sph.ka)
            Illd = Ie.dimm(sph.kd) * ldir.cosine(norm)
            ref = ldir.reflect(norm)
            cos_value = (dir * -1).cosine(ref)
            if cos_value < 0:
                cos_value = 0
            Ills = Ie.dimm(sph.ks) * (cos_value ** sph.shine)
            Illu = Illu + Illa + Illd + Ills
        reflection = BLACK

        reflection = raycast(intersection, dir.reflect(
            norm) * -1, spheres, lights, n + 1)

        c = sph.color.dimm(Illu) + reflection * sph.reflect
    return (c)


def drawpix(p, w, h, c):
    p[w, h] = tuple(c.arr)


if __name__ == "__main__":
    img = Image.new('RGB', (WIDTH, HEIGHT))
    pixels = img.load()
    eye = instance(0, 0, 0)
    spheres = []
    lights = []
    if ENABLEREFLECT:
        spheres.append(sphere(-1.3, 20, 1, 255, 0, 0, 1, reflect=0.7))
        spheres.append(sphere(1.3, 20, 1, 0, 0, 255, 1, reflect=0.7))
        spheres.append(sphere(0, 20, -1, 0, 255, 0, 1, reflect=0.7))
        lights.append(light(0, 0, 0, 255, 255, 255))
    else:
        spheres.append(sphere(-1, 20, 0, 255, 255, 255, 1))
        spheres.append(sphere(0.3, 19, 1, 0, 0, 255, 0.5))
        lights.append(light(70, -50, 30, 255, 255, 255))

    # spheres.append(sphere(0, 20, 0, 0, 0, 255, 1))
    # lights.append(light(0, -25, 0, 30, 30, 30))
    for h in range(HEIGHT):
        for w in range(WIDTH):
            direction = finddir(w, h, eye)
            c = raycast(eye.position, direction, spheres, lights)
            drawpix(pixels, w, h, c)
    img.show()
    if SAVE:
        if ENABLEREFLECT:
            img.save("ratcast_ref.png")
        else:
            img.save("ratcast.png")
