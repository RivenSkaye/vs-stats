from fractions import Fraction
from functools import cached_property
from typing import NamedTuple, Optional, TypeVar, Union
from EnforceTypes import classtypes

import vapoursynth as vs

__all__ = [
    "Resolution", "Subclip"
]

SC = TypeVar("SC", bound="Subclip")


@classtypes
class Resolution(NamedTuple):
    """A simple object representing a frame or video resolution."""
    width: int
    height: int

    def __repr__(self) -> str:
        return f"{self.width}x{self.height}"


@classtypes
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
    resolution: Resolution

    def __init__(
        self,
        clip: vs.VideoNode,
        fmt: Union[vs.VideoFormat, int],
        fps_num: int,
        fps_den: int,
        start: int,
        end: int,
        resolution: Optional[Resolution] = None
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
        self.resolution = resolution or Resolution(0, 0)

    def get_frame(self, n: int = 0) -> vs.VideoFrame:
        """
        Gets a frame from this Subclip.

        The offset ``n`` is translated from ``start`` and an error will be raised if the result
        is higher than or equal to ``end`` as this represents an out-of-bounds index.

        :param n:   The frame to get, fetched as ``self.start + n`` and defaults to 0.
        """
        n = self.start + n
        if n >= self.end:
            framecount = self.end - self.start
            raise IndexError(f"Frame {n} is out of bounds, this Subclip only has {framecount} "
                             f"frames! Provide a number between {self.start} and "
                             f"{self.start + framecount - 1}")
        return self.clip.get_frame(n)

    def is_mismatch(self, other: Union[vs.VideoNode, vs.VideoFrame, "Subclip"]) -> bool:
        """
        Compare this :py:class:`Subclip` with a ``VideoNode`` or ``VideoFrame`` for mismatches.

        Compares this :py:class:`Subclip` with ``other`` to check if the format and framerate match.
        This provides a way to check if two frames or clips can be safely spliced together.
        This also provides a way of checking if the format or framerate has changed between previous
        and current frames within a frame eval.

        :param other:   The ``VideoNode`` or ``VideoFrame`` to compare this subclip with.
        """
        if isinstance(other, self.__class__):
            other = other.get_frame()
        # When comparing against a variable clip, it's never a match.
        if isinstance(other, vs.VideoNode):
            if (
                None in [other.format, other.width, other.height, other.fps] or
                0 in [other.width, other.height, other.fps.numerator]
            ):
                return False
            # If it's a match, any frame will work. We'll grab 0 as that's always there.
            other = other.get_frame(0)
        assert isinstance(other, vs.VideoFrame)

        otherfps: float = other.props.get("_DurationNum", 0) / other.props.get("_DurationDen", 1)  # type: ignore  # noqa: E501
        return (
            self.fps == otherfps and
            self.fmt == other.format.id and
            self.width == other.width and
            self.height == other.height
        )

    @property
    def trim(self) -> vs.VideoNode:
        """Trims the videonode and sets the specified framerate and format."""
        c = self.clip[self.start:self.end]
        c = c.std.AssumeFPS(fpsnum=self.fps_num, fpsden=self.fps_den)
        return c.resize.Bicubic(format=self.fmt)

    @cached_property
    def width(self) -> int:
        if self.resolution.width == 0:
            rh = self.resolution.height
            ch = self.clip.height
            f = self.clip.get_frame(self.start)
            if self.clip.width != 0:
                height = rh if rh > 0 else ch if ch > 0 else f.height
                self.resolution = Resolution(self.clip.width, height)
            else:
                height = rh if rh > 0 else ch if ch > 0 else f.height
                self.resolution = Resolution(f.width, height)
            f.close()
        return self.resolution.width

    @cached_property
    def height(self) -> int:
        if self.resolution.height == 0:
            rw = self.resolution.width
            cw = self.clip.width
            f = self.clip.get_frame(self.start)
            if self.clip.height != 0:
                width = rw if rw > 0 else cw if cw > 0 else f.width
                self.resolution = Resolution(width, self.clip.height)
            else:
                width = rw if rw > 0 else cw if cw > 0 else f.width
                self.resolution = Resolution(width, f.height)
            f.close()
        return self.resolution.width

    @cached_property
    def fps(self) -> float:
        return self.fps_num / self.fps_den

    @cached_property
    def fps_fraction(self) -> Fraction:
        return Fraction(self.fps_num, self.fps_den)
