from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Sequence, TypeAlias

import numpy as np

from pyction.type_aliases import Vec2

Pixel: TypeAlias = Sequence[int]  # BGRA

@dataclass
class Entity:
    shape: Shape
    blend: Blend

    def render(self, image: np.ndarray)->None:
        x, y, width, height = self.shape.range()
        
        x = max(0, int(x))
        y = max(0, int(y))
        width = min(image.shape[1] - x, int(width))
        height = min(image.shape[0] - y, int(height))

        for i in range(x, x+width):
            for j in range(y, y+height):
                if self.shape.contains(i, j):
                    image[j, i] = self.blend.apply(image[j, i])

Envelope: TypeAlias = tuple[int, int, int, int]  # x, y, width, height

class Shape(ABC):
    def range(self) -> Envelope:
        pass

    def contains(self, x: int, y: int) -> bool:
        # X,is guaranteed to be within the range of the shape
        pass

class Blend(ABC):
    def apply(self, pixel: Pixel) -> Pixel:
        pass

@dataclass
class Rectangle(Shape):
    top_left: Vec2
    size: Vec2

    def range(self) -> Envelope:
        return (*self.top_left, *self.size)

    def contains(self, x: int, y: int) -> bool:
        return True
    
@dataclass
class Circle(Shape):
    center: Vec2
    radius: int

    def range(self) -> Envelope:
        x, y = self.center
        return (x - self.radius, y - self.radius, 2*self.radius, 2*self.radius)

    def contains(self, x: int, y: int) -> bool:
        cx, cy = self.center
        return (x - cx)**2 + (y - cy)**2 <= self.radius**2

@dataclass
class Solid(Blend):
    color: Pixel

    def apply(self, pixel: Pixel) -> Pixel:
        return self.color
    
@dataclass
class Eye(Shape):
    first_edge: Vec2
    second_edge: Vec2
    peak_fraction: float
    peak_height: float

    def range(self) -> Envelope:
        x1, y1 = self.first_edge
        x2, y2 = self.second_edge
        x = min(x1, x2)-self.peak_height
        y = min(y1, y2)-self.peak_height
        width = abs(x1 - x2)+2*self.peak_height
        height = abs(y1 - y2)+2*self.peak_height
        return (x, y, width, height)
    
    def contains(self, x: int, y: int) -> bool:
        # first we find the projection of our point on the line defined by the two edges
        # stolen from https://stackoverflow.com/a/64330724/2636095
        ab = self.second_edge - self.first_edge
        if np.count_nonzero(ab) == 0:
            return False
        ac = np.array([x,y]) - self.first_edge
        ad = ab * ac.dot(ab) / ab.dot(ab)

        prog_vec = ad/ab
        assert prog_vec[0] == prog_vec[1], f"{prog_vec=} ({ad=}, {ab=})"
        prog = prog_vec[0]

        if prog > 1 or prog < 0:
            return False
        
        dist = np.linalg.norm(ac-ad)
        if dist > self.peak_height:
            return False
        return dist <= self.height_allowed(prog)
    
    def curv(self, d: float)->float:
        return 4*self.peak_height*d*(1-d)

    def height_allowed(self, prog: float)->float:
        if prog < self.peak_fraction:
            return self.curv(prog/(2*self.peak_fraction))
        else:
            return self.curv(0.5 + (prog-self.peak_fraction)/(2*(1-self.peak_fraction)))

