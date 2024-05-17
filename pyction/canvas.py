from __future__ import annotations

from typing import Iterator, TypeAlias, TypeVar

import numpy as np

from pyction.entity import Entity
from pyction.script import Script
from pyction.type_aliases import Vec2Inp, Vec2

def vec2(x: Vec2Inp) -> Vec2:
    if isinstance(x, tuple):
        return x
    elif isinstance(x, (float, int)):
        return (x, x)
    else:
        return tuple(x)

S = TypeVar('S', bound=Script[Entity])

class Canvas:
    def __init__(self, dimensions: Vec2Inp, n_frames: int) -> None:
        self.dimensions = vec2(dimensions)
        self.n_frames = n_frames
        self.scripts: list[Script[Entity]] = []  # order is important!

    def script(self) -> Script[Entity]:
        return self.add_script(Script())
    
    def add_script(self, script: S) -> S:
        self.scripts.append(script)
        return script

    def runner(self) -> CanvasRunner:
        return CanvasRunner(self)

class CanvasRunner:
    def __init__(self, canvas: Canvas) -> None:
        self.canvas = canvas
        self.runners = [script.runner() for script in canvas.scripts]
        self.frame = -1

    def frames(self) -> Iterator[np.ndarray]:
        for _ in range(self.canvas.n_frames+1):
            yield self._next_frame()
    
    def _next_frame(self) -> np.ndarray:
        self.frame += 1
        for runner in self.runners:
            runner.enter_frame(self.frame)
        
        image = np.zeros((self.canvas.dimensions[1], self.canvas.dimensions[0], 4), dtype=np.uint8)

        for runner in self.runners:
            if not runner.is_initialized():
                continue
            entity = runner.entity
            entity.render(image)

        return image