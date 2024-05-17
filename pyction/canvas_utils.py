from dataclasses import dataclass
from time import perf_counter
from typing import Iterator

import numpy as np

from pyction.canvas import Canvas

@dataclass
class RenderedFrame:
    frame: np.ndarray
    index: int
    time_to_render: float

def report_renders(canvas: Canvas)->Iterator[RenderedFrame]:
    frames = enumerate(canvas.runner().frames())
    total_start = perf_counter()
    while True:
        start_time = perf_counter()
        try:
            i, frame = next(frames)
        except StopIteration:
            return
        end_time = perf_counter()
        total_duration = end_time - total_start
        eta = total_duration * (canvas.n_frames - i) / (i + 1)
        print(f"rendered frame {i}/{canvas.n_frames} ({(end_time - start_time)*1000:.2f}ms) (ETA: {eta:.2f}s)")
        yield RenderedFrame(frame, i, end_time - start_time)