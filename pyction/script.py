from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeAlias, TypeVar

from sortedcontainers import SortedDict, SortedList

E = TypeVar('E')

@dataclass
class ScriptAttr:
    name: str
    value: Any

@dataclass
class ScriptInitialize(Generic[E]):
    entity: E

PointAction: TypeAlias = ScriptAttr | ScriptInitialize[E]

class TrackRunner(Generic[E]):
    def __init__(self, track: ScriptTrack) -> None:
        self.track = track
        self.values = track.values.copy()
    
    def enter_frame(self, frame: int, entity: E) -> None:
        if frame == self.track.start:
            # we're live, replace ... with the current value
            current = ...
            for (k,v) in self.values.items():
                if v is ...:
                    if current is ...:
                        current = get_property(entity, self.track.prop)
                    self.values[k] = current
        elif frame == self.track.end:
            raise StopIteration
            
        if frame in self.values:
            new_value = self.values[frame]
        else:
            new_value = self.track.interpolation.interpolate(self.values, frame)
        set_property(entity, self.track.prop, new_value)

class Script(Generic[E]):
    def __init__(self) -> None:
        super().__init__()
        self.points: dict[int, list[PointAction]] = {}
        self.tracks_by_start: SortedDict[int, list[ScriptTrack[E]]] = {}

    def runner(self) -> ScriptRunner[E]:
        return ScriptRunner(self)
    
    def add_point(self, frame: int, point: PointAction[E]) -> PointAction[E]:
        if frame not in self.points:
            self.points[frame] = []
        self.points[frame].append(point)
    
    def add_track(self, track: ScriptTrack[E]) -> ScriptTrack[E]:
        if track.start not in self.tracks_by_start:
            self.tracks_by_start[track.start] = []
        self.tracks_by_start[track.start].append(track)


uninitialized = object()

def set_property(entity: Any, name: str, value: Any) -> None:
    p, _, rest = name.partition('.')
    if rest:
        set_property(getattr(entity, p), rest, value)
    else:
        setattr(entity, p, value)

def get_property(entity: Any, name: str) -> Any:
    p, _, rest = name.partition('.')
    if rest:
        return get_property(getattr(entity, p), rest)
    else:
        return getattr(entity, p)

class ScriptRunner(Generic[E]):
    def __init__(self, script: Script[E]) -> None:
        self.script = script
        self.entity = uninitialized
        self.active_tracks: set[TrackRunner[E]] = set()

    def _apply_point(self, point: PointAction) -> None:
        if isinstance(point, ScriptInitialize):
            self.entity = point.entity
        else:
            set_property(self.entity, point.name, point.value)

    def is_initialized(self) -> bool:
        return self.entity is not uninitialized

    def enter_frame(self, frame: int) -> None:
        # first we apply all the points in the new frame
        for point in self.script.points.get(frame, ()):
            self._apply_point(point)

        # then we check if any tracks need to be activated
        for track in self.script.tracks_by_start.get(frame, ()):
            self.active_tracks.add(track.runner())

        # now we apply all the tracks
        tracks_to_remove = []
        for active_track in self.active_tracks:
            try:
                active_track.enter_frame(frame, self.entity)
            except StopIteration:
                tracks_to_remove.append(active_track)
                
        for track in tracks_to_remove:
            self.active_tracks.remove(track)

class Interpolation(Protocol):
    def interpolate(self, points: SortedDict[int, Any], time: int) -> Any:
        ...

class _LinearInterpolation(Interpolation):
    def interpolate(self, points: SortedDict[int, Any], time: int) -> Any:
        prev_idx = points.bisect_left(time)-1
        next_idx = prev_idx + 1
        prev_time, prev_value = points.peekitem(prev_idx)
        next_time, next_value = points.peekitem(next_idx)
        return prev_value + (next_value - prev_value) * (time - prev_time) / (next_time - prev_time)

LinearInterpolation: Interpolation = _LinearInterpolation()

class _StepInterpolation(Interpolation):
    def interpolate(self, points: SortedDict[int, Any], time: int) -> Any:
        return points[points.bisect_left(time)]

StepInterpolation: Interpolation = _StepInterpolation()

@dataclass
class ScriptTrack(Generic[E]):
    prop: str
    values: SortedDict[int, Any]
    interpolation: Interpolation = LinearInterpolation

    @property
    def start(self) -> int:
        return self.values.keys()[0]
    
    @property
    def end(self) -> int:
        return self.values.keys()[-1]
    
    def runner(self) -> TrackRunner[E]:
        return TrackRunner(self)