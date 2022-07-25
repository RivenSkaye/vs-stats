from typing import Any, NamedTuple, Type, TypeVar, get_args


class EnforceTypes:
    """A class for use as class decorator. Enforces types in ``init``"""
    class _MISSING:
        pass
    MISSING = _MISSING()
    T = TypeVar("T")

    def __init__(self, cls: Type[T]):
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
