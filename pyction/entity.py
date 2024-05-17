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