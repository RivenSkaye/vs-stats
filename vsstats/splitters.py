"""Module for probing video for data and returning statistics information."""

from functools import partial
from typing import Callable, List, Optional, Sequence, Union
from vsutil import frame2clip

import vapoursynth as vs

from .types import Resolution

core = vs.core


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

    :param clip:            The variable resolution clip to split.
    :param resolution:      None to return all clips, or a :py:class:`Resolution` or another
                            ``Sequence`` that contains integers describing the desired width
                            or height, alternatively provide the ``width`` and ``height`` kwargs.
    :param width:           Keyword-only argument, specify the width of the resolution to return.
    :param height:          Keyword-only argument, specify the height of the resolution to return.
    """
    if resolution is not None or (width is not None or height is not None):
        if resolution is None:
            if (width is None or height is None):
                raise ValueError("split_resolutions: When selecting only a single resolution, "
                                 "provide either a Resolution or both width AND height!")
            else:
                resolution = Resolution(width, height)
        if not isinstance(resolution, Resolution):
            resolution = Resolution(resolution[0], resolution[1])
        if clip.width == resolution.width and clip.height == resolution.height:
            return [clip]
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


def split_formats(clip: vs.VideoNode, format: vs.VideoFormat) -> Optional[List[vs.VideoNode]]:
    """
    Split a variable format clip by format.

    Splits a variable format input clip into a list of each of its formats.
    Optionally filters the results to only match a certain resolution.
    """
