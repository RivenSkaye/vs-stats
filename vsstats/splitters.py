"""Module for probing video for data and returning statistics information."""

from functools import partial
from typing import Callable, List, Optional, Sequence, Union
from vsutil import frame2clip

import vapoursynth as vs

from .types import Resolution
from ._helpers import _get_res

core = vs.core

__all__ = [
    "split_resolutions", "split_formats"
]


def split_resolutions(
    clip: vs.VideoNode,
    resolution: Union[Resolution, Sequence[int], None] = None,
    filterfunc: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None, *,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Optional[List[vs.VideoNode]]:
    """
    Splits a variable resolution clip by resolution.

    Splits a variable resolution input clip into a list of each of its resolutions.
    Optionally filters the results to only match a certain resolution.
    Optionally applies a function on the resulting constant resolution clips.
    When supplying a resolution to match, this function returns ``None`` if no
    matching clips were found

    :param clip:            The variable resolution clip to split.
    :param resolution:      None to return all clips, or a :py:class:`Resolution` or another
                            ``Sequence`` that contains integers describing the desired width
                            or height, alternatively provide the ``width`` and ``height`` kwargs.
    :param filterfunc:      Optional function to apply to all clips before returning.
    :param width:           Keyword-only argument, specify the width of the resolution to return.
    :param height:          Keyword-only argument, specify the height of the resolution to return.
    """
    resolution = _get_res(resolution, width, height, "split_resolutions")
    # If the clip matches, return it
    if resolution is not None:
        if clip.width == resolution.width and clip.height == resolution.height:
            return [clip]
        # :kekw:
        elif clip.width == resolution.height and clip.height == resolution.width:
            return[clip.std.Transpose()]
    elif clip.width and clip.height:
        return [clip]

    reslist: List[vs.VideoNode] = []
    storeclip: Optional[vs.VideoNode] = None

    def _eval(
        f: vs.VideoFrame, n: int,
        res: Optional[Resolution] = None
    ) -> vs.VideoFrame:
        """Function for use in a frame eval that splits chunks of clip by their resolution"""
        nonlocal reslist
        nonlocal storeclip

        if res is not None and (f.width != res.width or f.height != res.height):
            if storeclip is not None:
                reslist.append(storeclip)
            storeclip = None
            return f

        fc = frame2clip(f)
        if storeclip is None:
            storeclip = fc
            return f

        if f.width != storeclip.width or f.height != storeclip.height:
            reslist.append(storeclip)
            storeclip = fc
        else:
            storeclip += fc

        return f

    evalfunc = partial(_eval, res=resolution)
    clip.std.FrameEval(evalfunc)

    reslist = [filterfunc(res) for res in reslist] if filterfunc is not None else reslist
    return None if len(reslist) == 0 else reslist


def split_formats(
    clip: vs.VideoNode,
    videoformat: Union[vs.VideoFormat, vs.VideoNode, None],
    filterfunc: Optional[Callable[[vs.VideoNode], vs.VideoNode]]
) -> Optional[List[vs.VideoNode]]:
    """
    Split a variable format clip by format.

    Splits a variable format input clip into a list of each of its formats.
    Optionally filters the results to only match a certain format.
    Optionally applies a function on the resulting constant format clips.
    When supplying a format to match, this function returns ``None`` if no matching
    formats were found.

    :param clip:            the clip to split
    :param videoformat:     Optional, the format to match, will return only matching clips.
                            This can be gotten from either a clip or a frame, the ``format``
                            property. It's easiest to get this off a reference clip or off
                            a single-frame splice, e.g. ``(clip[20]).format`` should work.
                            You can also pass an entire clip for extraction, but that might
                            yield None, causing the function to return all clips.
    :param filterfunc:      A function to apply to all filtered clips before returning.
    """
    if isinstance(videoformat, vs.VideoNode):
        videoformat = videoformat.format

    formatlist: List[vs.VideoNode] = []
    storeclip: Optional[vs.VideoNode] = None

    def _eval(
        f: vs.VideoFrame, n: int,
        fmt: Optional[vs.VideoFormat]
    ) -> vs.VideoFrame:
        """Eval function for splitting things by format"""
        nonlocal formatlist
        nonlocal storeclip

        if fmt is not None and f.format != fmt:
            if storeclip is not None:
                formatlist.append(storeclip)
                storeclip = None
            return f

        fc = frame2clip(f)
        if storeclip is None:
            storeclip = fc
            return f

        if storeclip.format != f.format:
            formatlist.append(storeclip)
            storeclip = fc
        else:
            storeclip += fc

        return f

    evalfunc = partial(_eval, fmt=videoformat)
    clip.std.FrameEval(evalfunc)

    formatlist = [filterfunc(fmt) for fmt in formatlist] if filterfunc is not None else formatlist
    return None if len(formatlist) == 0 else formatlist
