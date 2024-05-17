from os import PathLike
from pathlib import Path
from time import perf_counter
from typing import Sequence
import cv2
import numpy as np
from pyction.canvas import Canvas
from pyction.canvas_utils import RenderedFrame, report_renders


def show_canvas(canvas: Canvas, window_name: str = 'Pyction', duration: float | None = None, fps: int | None = None)->Sequence[RenderedFrame]:
    if duration is None and fps is None:
        wait = 1
    elif duration is not None:
        wait = int((duration*1000) / canvas.n_frames)
    elif fps is not None:
        wait = int(1000 / fps)

    frames = report_renders(canvas)
    ret = []
    def render():
        rendered = next(frames)
        ret.append(rendered)
        cv2.imshow(window_name, rendered.frame)
        cv2.setTrackbarPos('Frame', window_name, rendered.index)
        return rendered
    cv2.namedWindow(window_name)
    cv2.createTrackbar('Frame', window_name, 0, canvas.n_frames-1, lambda x: None)
    print("press any key to start rendering")
    while True:
        key = cv2.waitKey(1000)
        if key != -1:
            break
    while cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) >= 1:
        try:
            t = render().time_to_render
            key = cv2.waitKey(max(wait - int(t*1000), 1))
        except StopIteration:
            break
        if key != -1:
            raise KeyboardInterrupt
    
    cv2.destroyAllWindows()
    return ret

def show_canvas_with_save_opt(canvas: Canvas, window_name: str = 'Pyction', duration: float | None = None, fps: int | None = None, *,
                              folder: PathLike, filename_format: str = 'frame.{:04d}.png'):
    frames = show_canvas(canvas, window_name, duration, fps)
    resp = input("Do you want to save the frames? ([y]/n): ") or "y"
    if resp.lower() == 'y':
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        for rendered in frames:
            cv2.imwrite(str(folder / filename_format.format(rendered.index)), rendered.frame)