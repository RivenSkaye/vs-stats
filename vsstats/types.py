from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, NamedTuple, Type, TypeVar, Union, get_args

import vapoursynth as vs


class EnforceTypes:
    """A class for use as class decorator. Enforces types in ``init``"""
    class _MISSING:
        pass
    MISSING = _MISSING()
    T = TypeVar("T")

    def __init__(self, cls: Union[Type[T], Callable]):
        self.cls = cls
        self.keywords = cls.__annotations__

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        arglist = list(args)
        for kw in self.keywords:
            argval = arglist.pop(0) if len(arglist) > 0 else ...
            kw_val = kwargs.get(kw, self.MISSING)
            if argval is not ... and kw_val is not self.MISSING:
                raise TypeError(f"{kw} was given as both a positional and a keyword argument!")
            if kw_val is self.MISSING:
                if argval is ...:
                    continue
                kw_val = argval
                kwargs[kw] = kw_val
            argtype = self.keywords[kw]
            argtuple = get_args(argtype)
            if not isinstance(kw_val, argtype) and not isinstance(kw_val, argtuple):
                raise TypeError(f"Argument {kw} was passed a value of type `"
                                f"{type(kw_val).__name__}`, but only accepts values of "
                                f"type `{argtype.__name__}`")
        return self.cls(*arglist, **kwargs)


@EnforceTypes
class Resolution(NamedTuple):
    """A simple object representing a frame or video resolution."""
    width: int
    height: int

    def __repr__(self) -> str:
        return f"{self.width}x{self.height}"


@EnforceTypes
@dataclass
class Subclip:
    """A class to define a constant format and/or framerate subclip.

    This dataclass exposes a simple API to store the information about a constant format and/or
    framerate section of a clip, and an easy way to retrieve that section of video with the
    proper values set.
    """
    clip: vs.VideoNode
    fmt: int
    fps_num: int
    fps_den: int
    start: int
    end: int
    _w: int = 0
    _h: int = 0

    def __init__(
        self,
        clip: vs.VideoNode,
        fmt: Union[vs.VideoFormat, int],
        fps_num: int,
        fps_den: int,
        start: int,
        end: int
    ):
        """
        :param clip:        The ``vs.VideoNode`` this Subclip is a part of.
        :param fmt:         The ``vs.VideoFormat`` or its ``id`` to apply to the subclip.
                            This cannot be retrieved from ``clip`` as that's supposed to be
                            variable format, thus presenting the format as ``None`` when checked.
        :param fpsnum:      fps numerator (24000 for 23.976).
        :param fpsden:      fps denominator (1001 for 23.976).
        :param start:       The index where this section starts. Zero-indexed like slice notation.
        :param end:         The index where this section ends. One-indexed liked slice notation.
        """
        if start >= end:
            raise ValueError("The start of a subclip cannot be after its end!")
        self.clip = clip
        self.fmt = fmt.id if isinstance(fmt, vs.VideoFormat) else fmt
        self.fps_num = fps_num
        self.fps_den = fps_den
        self.start = start
        self.end = end

    @property
    def trim(self) -> vs.VideoNode:
        """Trims the videonode and sets the specified framerate and format."""
        c = self.clip[self.start:self.end]
        c = c.std.AssumeFPS(fpsnum=self.fps_num, fpsden=self.fps_den)
        return c.resize.Bicubic(format=self.fmt)

    @property
    def width(self) -> int:
        self._w = self.clip.width
        return self._w if self._w > 0 else self.clip.get_frame(self.start).width

    @property
    def height(self) -> int:
        self._h = self.clip.height
        return self._h if self._h > 0 else self.clip.get_frame(self.start).height

    @property
    def fps(self) -> float:
        return self.fps_num / self.fps_den

    @property
    def fps_fraction(self) -> Fraction:
        return Fraction(self.fps_num, self.fps_den)
