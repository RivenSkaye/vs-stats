"""Module for probing video for data and returning statistics information."""

from functools import partial
from typing import Callable, List, Optional, Sequence, Tuple, Union

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
        n: int,
        f: vs.VideoFrame,
        res: Optional[Resolution] = None
    ) -> vs.VideoNode:
        """Function for use in a frame eval that splits chunks of clip by their resolution"""
        nonlocal reslist
        nonlocal curclip
        nonlocal clip

        if res is not None and (f.width != res.width or f.height != res.height):
            if curclip is not None:
                reslist.append(curclip)
                curclip = None
            return clip

        if curclip is None:
            curclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n + 1,
                Resolution(f.width, f.height)
            )
            return clip

        if f.width != curclip.width or f.height != curclip.height:
            curclip.end = n
            reslist.append(curclip)
            curclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n + 1,
                Resolution(f.width, f.height)
            )
        else:
            curclip.end = n
        if n == clip.num_frames:
            reslist.append(curclip)

        return clip

    evalfunc = partial(_eval, res=resolution)
    clip.std.FrameEval(evalfunc, clip)

    if filterfunc is not None:
        filtered: List[vs.VideoNode] = []
        for sc in reslist:
            filtered.append(filterfunc(sc.trim))
        fclip = core.std.Splice(filtered, mismatch=True)
        for sc in reslist:
            sc.clip = fclip

    return None if len(reslist) == 0 else reslist


def split_formats(
    clip: vs.VideoNode,
    videoformat: Union[vs.VideoFormat, vs.VideoNode, int, None] = None,
    filterfunc: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None
) -> Tuple[Optional[List[Subclip]], vs.VideoNode]:
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
        if videoformat is None:
            raise TypeError("Passed a variable format clip as reference for format!")

    formatlist: List[Subclip] = []
    storeclip: Optional[Subclip] = None
    print(clip)

    def _eval(
        n: int,
        f: vs.VideoFrame,
        fmt: Optional[vs.VideoFormat]
    ) -> vs.VideoNode:
        """Eval function for splitting clips by format"""
        nonlocal formatlist
        nonlocal storeclip
        nonlocal clip
        print(f)
        print(n)

        if fmt is not None and f.format != fmt:
            if storeclip is not None:
                formatlist.append(storeclip)
                storeclip = None
            return clip

        if storeclip is None:
            storeclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n+1,
                Resolution(f.width, f.height)
            )
            return clip

        if storeclip.fmt != f.format.id:
            storeclip.end = n
            formatlist.append(storeclip)
            storeclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n + 1,
                Resolution(f.width, f.height)
            )
        else:
            storeclip.end = n
        if n == clip.num_frames:
            formatlist.append(storeclip)

        return clip

    evalfunc = partial(_eval, fmt=videoformat)
    clip = clip.std.FrameEval(evalfunc, clip)

    if filterfunc is not None:
        filtered: List[vs.VideoNode] = []
        for fmt in formatlist:
            filtered.append(filterfunc(fmt.trim))
        clip = core.std.Splice(filtered, mismatch=True)
        for fmt in formatlist:
            fmt.clip = clip
    return (None if len(formatlist) == 0 else formatlist), clip


def split_mismatch(
    clip: vs.VideoNode,
    filterfunc: Optional[Callable[[vs.VideoNode], vs.VideoNode]] = None
) -> List[Subclip]:
    """
    Splits a clip with any variable properties.

    Splits clips with **any** of its properties into a ``list`` of ``Subclip`` instances
    and optionally applies a filtering function to all resulting clips.
    This function makes a ``Subclip`` instance for every change in the source clip that would
    require splicing to use the ``mismatch`` argument. For more information about this, please
    refer to `the relevant documentation <http://vapoursynth.com/doc/functions/video/splice.html>`_
    which, at the time of writing, only specifies the ``format`` and ``width`` and ``height``
    properties as the source of a mismatch.
    Also look at the documentation and implementation of :py:class:`Subclip` for its the way it
    checks using the :py:meth:`Subclip.is_mismatch` method.

    :param clip:        The clip to split.
    :param filterfunc:  The function to apply to all clips resulting from the split.
    """
    splitlist: List[Subclip] = []
    storeclip: Optional[Subclip] = None

    def _eval(n: int, f: vs.VideoFrame) -> vs.VideoNode:
        nonlocal splitlist
        nonlocal storeclip
        nonlocal clip

        if storeclip is None:
            storeclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n+1,
                Resolution(f.width, f.height)
            )
        if storeclip.is_mismatch(f):
            storeclip.end = n
            splitlist.append(storeclip)
            storeclip = Subclip(
                clip,
                f.format.id,
                f.props.get("_DurationNum", 0),  # type: ignore  # always an int
                f.props.get("_DurationDen", 1),  # type: ignore  # always an int
                n,
                n+1,
                Resolution(f.width, f.height)
            )
        else:
            storeclip.end = n
        if n == clip.num_frames:
            splitlist.append(storeclip)
        return clip

    clip = clip.std.FrameEval(_eval, clip)

    if filterfunc is not None:
        filtered: List[vs.VideoNode] = []
        for split in splitlist:
            filtered.append(filterfunc(split.trim))
        clip = core.std.Splice(filtered, mismatch=True)
        for split in splitlist:
            split.clip = clip
    return splitlist
