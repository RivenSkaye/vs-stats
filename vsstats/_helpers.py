from typing import Optional, Sequence, Union

from .types import Resolution


def _get_res(
    res: Optional[Union[Resolution, Sequence]], width: Optional[int], height: Optional[int],
    func: str
) -> Optional[Resolution]:
    if res is None and width is None and height is None:
        return None
    if res is not None:
        return res if isinstance(res, Resolution) else Resolution(res[0], res[1])
    if width is not None and height is not None:
        return Resolution(width, height)
    raise ValueError(f"{func}: When selecting only a single resolution, provide"
                     "a Resolution or both width AND height!")
