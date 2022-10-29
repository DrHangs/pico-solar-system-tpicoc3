from random import getrandbits, uniform
import math
from micropython import const
from st7789 import color565 as PEN


class Pluto:
    MAX_TIME = const(2000)
    R = const(3)
    BOUNCE = 0.98

    def __init__(self, display):
        self.display = display
        self.x = 240.0
        self.y = 0
        self.px = self.x
        self.py = self.y
        self.vel_x = -3.0
        self.y_max = 135 - Pluto.R
        self.x_min = 140 + Pluto.R
        self.x_max = 240 - Pluto.R

    def step(self, seconds, diff):
        self.px = self.x
        self.py = self.y
        if diff > 1000:
            diff = 1000
        invertedSeconds = 60 - seconds
        time = (invertedSeconds * 1000 - diff)
        amplitude = time / 60_000.0
        x_fun = time % Pluto.MAX_TIME / float(Pluto.MAX_TIME)
        sway = 1 - (math.pow(((x_fun / 0.5) - 1), 2) * (-1) + 1)
        add = (self.y_max - (self.y_max * amplitude))
        self.y = ((self.y_max * amplitude) * sway) + add

        self.x += self.vel_x
        if self.x >= self.x_max:
            self.vel_x *= -Pluto.BOUNCE
            self.x = self.x_max
        elif self.x <= self.x_min:
            self.vel_x *= -Pluto.BOUNCE
            self.x = self.x_min

    def draw(self):
        #self.display.set_pen(self.display.create_pen(156, 166, 183))
        self.display.circle(int(self.px), int(self.py), Pluto.R, PEN(0, 0, 0)) #delete previous draw
        self.display.circle(int(self.x), int(self.y), Pluto.R, PEN(156, 166, 183))

    def reset(self):
        vel = uniform(3, 7)
        if bool(getrandbits(1)):
            vel *= -1
        self.vel_x = vel
        self.display.circle(int(self.x), int(self.y), Pluto.R, PEN(0, 0, 0))
