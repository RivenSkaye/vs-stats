"""Module for probing video for data and returning statistics information."""

from functools import partial
from typing import Callable, List, Optional, Sequence, Union

import vapoursynth as vs

from .types import Resolution, Subclip
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
) -> Optional[List[Subclip]]:
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
        # :kekw:
        if clip.width == resolution.height and clip.height == resolution.width:
            clip = clip.std.Transpose()
        if clip.width == resolution.width and clip.height == resolution.height:
            return [Subclip(
                clip,
                clip.get_frame(0).format.id,
                clip.fps_num,
                clip.fps_den,
                0,
                clip.num_frames,
                Resolution(clip.width, clip.height)
            )]
        elif clip.width and clip.height:
            return None
    # If no resolution was requested and the clip is constant res, return it
    elif clip.width and clip.height:
        return [Subclip(
            clip,
            clip.get_frame(0).format.id,
            clip.fps_num,
            clip.fps_den,
            0,
            clip.num_frames,
            Resolution(clip.width, clip.height)
        )]

    reslist: List[Subclip] = []
    curclip: Optional[Subclip] = None

    def _eval(
        f: vs.VideoFrame,
        n: int,
        res: Optional[Resolution] = None
    ) -> vs.VideoFrame:
        """Function for use in a frame eval that splits chunks of clip by their resolution"""
        nonlocal reslist
        nonlocal curclip
        nonlocal clip

        if res is not None and (f.width != res.width or f.height != res.height):
            if curclip is not None:
                reslist.append(curclip)
                curclip = None
            return f

        if curclip is None:
            curclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n + 1,
                _get_res(resolution)
            )
            return f

        if f.width != curclip.width or f.height != curclip.height:
            curclip.end = n
        if n == clip.num_frames:
            curclip.end = n

        return f

    evalfunc = partial(_eval, res=resolution)
    clip.std.FrameEval(evalfunc)

    if filterfunc is not None:
        filtered = []
        for sc in reslist:
            filtered.append(filterfunc(sc.trim))
        fclip = core.std.Splice(filtered, None)
        for sc in reslist:
            sc.clip = fclip

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

    formatlist: List[Subclip] = []
    storeclip: Optional[Subclip] = None

    def _eval(
        f: vs.VideoFrame,
        n: int,
        fmt: Optional[vs.VideoFormat]
    ) -> vs.VideoFrame:
        """Eval function for splitting clips by format"""
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

        if storeclip.fmt != f.format.id:
            formatlist.append(storeclip)
            storeclip = fc
        else:
            storeclip += fc

        return f

    evalfunc = partial(_eval, fmt=videoformat)
    clip.std.FrameEval(evalfunc)

    formatlist = [filterfunc(fmt.trim) for fmt in formatlist] if filterfunc is not None else formatlist
    return None if len(formatlist) == 0 else formatlist
