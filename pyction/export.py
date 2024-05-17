from os import PathLike
from pathlib import Path

import cv2

from pyction.canvas import Canvas
from pyction.canvas_utils import report_renders


def export_frames_to_folder(canvas: Canvas, folder: PathLike, filename_format: str = 'frame.{:04d}.png') -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(report_renders(canvas)):
        cv2.imwrite(str(folder / filename_format.format(i)), frame)