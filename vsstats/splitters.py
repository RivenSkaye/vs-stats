"""Module for probing video for data and returning statistics information."""

from functools import partial
from typing import List, Optional, Sequence, Union
from vsutil import frame2clip

import vapoursynth as vs

from .types import Resolution

core = vs.core


def split_resolutions(
    clip: vs.VideoNode,
    resolution: Union[Resolution, Sequence[int], None] = None
) -> Optional[List[vs.VideoNode]]:
    """
    Splits a variable resolution clip by resolution.

    Splits a variable resolution input clip into a list of each of its resolutions.
    Optionally filters the results to only match a certain resolution.

    :param clip;        The variable resolution clip to split.
    :param resolution:  None to return all clips, or a :py:class:`Resolution` or other ``Sequence``
                        that contains integers describing the desired width or height
    """
    if resolution is not None:
        if not isinstance(resolution, Resolution):
            resolution = Resolution(resolution[0], resolution[1])

    reslist: List[vs.VideoNode] = []
    storeclip: Optional[vs.VideoNode] = None

    def _eval(
        f: vs.VideoFrame, n: int,
        res: Optional[Resolution] = None
    ) -> vs.VideoFrame:
        """Function for use in a frame eval that sorts chunks of clip by their resolution"""
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

    return None if len(reslist) == 0 else reslist


def split_formats(clip: vs.VideoNode) -> None: return
