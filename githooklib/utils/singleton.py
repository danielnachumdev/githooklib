from typing import TypeVar, Type, Dict, Any

T = TypeVar("T")


def singleton(cls: Type[T]) -> Type[T]:
    _instances: Dict[Type[T], T] = {}
    _initialized: Dict[Type[T], bool] = {}
    original_new = getattr(cls, "__new__", object.__new__)
    original_init = getattr(cls, "__init__", object.__init__)

    def __new__(cls_instance: Type[T], *args: Any, **kwargs: Any) -> T:
        if cls not in _instances:
            if original_new is object.__new__:
                _instances[cls] = original_new(cls_instance)
            else:
                _instances[cls] = original_new(cls_instance, *args, **kwargs)
        return _instances[cls]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if cls not in _initialized:
            if original_init is not object.__init__:
                original_init(self, *args, **kwargs)
            _initialized[cls] = True

    setattr(cls, "__new__", __new__)
    setattr(cls, "__init__", __init__)

    return cls


__all__ = ["singleton"]
