from typing import Optional, Sequence, Union

from .types import Resolution

__all__ = [
    "_get_res"
]


def _get_res(
    res: Union[Resolution, Sequence, None] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    func: str = "User-defined function"
) -> Optional[Resolution]:
    if res is None and width is None and height is None:
        return None
    if res is not None:
        return res if isinstance(res, Resolution) else Resolution(res[0], res[1])
    if width is not None and height is not None:
        return Resolution(width, height) if width > 0 and height > 0 else None
    raise ValueError(f"{func}: When selecting only a single resolution, provide"
                     "a Resolution or both width AND height!")
