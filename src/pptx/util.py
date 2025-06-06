"""Utility functions and classes."""

from __future__ import annotations

import functools
from typing import Any, Callable, Generic, TypeVar, cast

from pptx.enum.text import MSO_NUMBERED_BULLET_STYLE, BulletStyleType


class Length(int):
    """Base class for length classes Inches, Emu, Cm, Mm, and Pt.

    Provides properties for converting length values to convenient units.
    """

    _EMUS_PER_INCH = 914400
    _EMUS_PER_CENTIPOINT = 127
    _EMUS_PER_CM = 360000
    _EMUS_PER_MM = 36000
    _EMUS_PER_PT = 12700

    def __new__(cls, emu: int):
        return int.__new__(cls, emu)

    @property
    def inches(self) -> float:
        """Floating point length in inches."""
        return self / float(self._EMUS_PER_INCH)

    @property
    def centipoints(self) -> int:
        """Integer length in hundredths of a point (1/7200 inch).

        Used internally because PowerPoint stores font size in centipoints.
        """
        return self // self._EMUS_PER_CENTIPOINT

    @property
    def cm(self) -> float:
        """Floating point length in centimeters."""
        return self / float(self._EMUS_PER_CM)

    @property
    def emu(self) -> int:
        """Integer length in English Metric Units."""
        return self

    @property
    def mm(self) -> float:
        """Floating point length in millimeters."""
        return self / float(self._EMUS_PER_MM)

    @property
    def pt(self) -> float:
        """Floating point length in points."""
        return self / float(self._EMUS_PER_PT)


class Inches(Length):
    """Convenience constructor for length in inches."""

    def __new__(cls, inches: float):
        emu = int(inches * Length._EMUS_PER_INCH)
        return Length.__new__(cls, emu)


class Centipoints(Length):
    """Convenience constructor for length in hundredths of a point."""

    def __new__(cls, centipoints: int):
        emu = int(centipoints * Length._EMUS_PER_CENTIPOINT)
        return Length.__new__(cls, emu)


class Cm(Length):
    """Convenience constructor for length in centimeters."""

    def __new__(cls, cm: float):
        emu = int(cm * Length._EMUS_PER_CM)
        return Length.__new__(cls, emu)


class Emu(Length):
    """Convenience constructor for length in english metric units."""

    def __new__(cls, emu: int):
        return Length.__new__(cls, int(emu))


class Mm(Length):
    """Convenience constructor for length in millimeters."""

    def __new__(cls, mm: float):
        emu = int(mm * Length._EMUS_PER_MM)
        return Length.__new__(cls, emu)


class Pt(Length):
    """Convenience value class for specifying a length in points."""

    def __new__(cls, points: float):
        emu = int(points * Length._EMUS_PER_PT)
        return Length.__new__(cls, emu)


class BulletStyle:
    """Convenience value class for styling unnumbered bullets.
    
    ``BulletStyle.NO_BULLET`` indicates that bullets are explicitly disabled
    a paragraph. ``BulletStyle.DEFAULT`` indicates that whether the paragraph
    is rendered as a bullet is defined in the slide master or layout.
    
    The methods ``BulletStyle.custom`` and ``BulletStyle.numbered`` can be
    used to create ``BulletStyle``s that control what kind of bullet is used
    for the paragraph.
    """

    NO_BULLET: BulletStyle = None
    DEFAULT: BulletStyle = None

    def __init__(self, style: BulletStyleType, value: str | MSO_NUMBERED_BULLET_STYLE | None = None):
        self._style = style
        self._value = value

    def __eq__(self, other: object):
        if isinstance(other, BulletStyle) and self._style == other._style:
            return self._value == other._value
        else:
            return False

    @property
    def value(self) -> str | MSO_NUMBERED_BULLET_STYLE | None:
        return self._value
    
    @property
    def style(self) -> BulletStyleType:
        return self._style

    @classmethod
    def custom(cls, bullet_string: str):
        """Defines a bullet that is rendered as ``bullet_string``."""
        return BulletStyle(BulletStyleType.CUSTOM, bullet_string)

    @classmethod
    def numbered(cls, style: MSO_NUMBERED_BULLET_STYLE):
        """Defines a bullet that is numbered.
        
        The style of the enumeration is controlled by the ``style`` and
        is a ``MSO_NUMBERED_BULLET_STYLE``.
        """
        return BulletStyle(BulletStyleType.NUMBERED, style)

BulletStyle.NO_BULLET = BulletStyle(BulletStyleType.NO_BULLET)
BulletStyle.DEFAULT = BulletStyle(BulletStyleType.DEFAULT)


_T = TypeVar("_T")


class lazyproperty(Generic[_T]):
    """Decorator like @property, but evaluated only on first access.

    Like @property, this can only be used to decorate methods having only a `self` parameter, and
    is accessed like an attribute on an instance, i.e. trailing parentheses are not used. Unlike
    @property, the decorated method is only evaluated on first access; the resulting value is
    cached and that same value returned on second and later access without re-evaluation of the
    method.

    Like @property, this class produces a *data descriptor* object, which is stored in the __dict__
    of the *class* under the name of the decorated method ('fget' nominally). The cached value is
    stored in the __dict__ of the *instance* under that same name.

    Because it is a data descriptor (as opposed to a *non-data descriptor*), its `__get__()` method
    is executed on each access of the decorated attribute; the __dict__ item of the same name is
    "shadowed" by the descriptor.

    While this may represent a performance improvement over a property, its greater benefit may be
    its other characteristics. One common use is to construct collaborator objects, removing that
    "real work" from the constructor, while still only executing once. It also de-couples client
    code from any sequencing considerations; if it's accessed from more than one location, it's
    assured it will be ready whenever needed.

    Loosely based on: https://stackoverflow.com/a/6849299/1902513.

    A lazyproperty is read-only. There is no counterpart to the optional "setter" (or deleter)
    behavior of an @property. This is critically important to maintaining its immutability and
    idempotence guarantees. Attempting to assign to a lazyproperty raises AttributeError
    unconditionally.

    The parameter names in the methods below correspond to this usage example::

        class Obj(object)

            @lazyproperty
            def fget(self):
                return 'some result'

        obj = Obj()

    Not suitable for wrapping a function (as opposed to a method) because it is not callable.
    """

    def __init__(self, fget: Callable[..., _T]) -> None:
        """*fget* is the decorated method (a "getter" function).

        A lazyproperty is read-only, so there is only an *fget* function (a regular
        @property can also have an fset and fdel function). This name was chosen for
        consistency with Python's `property` class which uses this name for the
        corresponding parameter.
        """
        # --- maintain a reference to the wrapped getter method
        self._fget = fget
        # --- and store the name of that decorated method
        self._name = fget.__name__
        # --- adopt fget's __name__, __doc__, and other attributes
        functools.update_wrapper(self, fget)  # pyright: ignore

    def __get__(self, obj: Any, type: Any = None) -> _T:
        """Called on each access of 'fget' attribute on class or instance.

        *self* is this instance of a lazyproperty descriptor "wrapping" the property
        method it decorates (`fget`, nominally).

        *obj* is the "host" object instance when the attribute is accessed from an
        object instance, e.g. `obj = Obj(); obj.fget`. *obj* is None when accessed on
        the class, e.g. `Obj.fget`.

        *type* is the class hosting the decorated getter method (`fget`) on both class
        and instance attribute access.
        """
        # --- when accessed on class, e.g. Obj.fget, just return this descriptor
        # --- instance (patched above to look like fget).
        if obj is None:
            return self  # type: ignore

        # --- when accessed on instance, start by checking instance __dict__ for
        # --- item with key matching the wrapped function's name
        value = obj.__dict__.get(self._name)
        if value is None:
            # --- on first access, the __dict__ item will be absent. Evaluate fget()
            # --- and store that value in the (otherwise unused) host-object
            # --- __dict__ value of same name ('fget' nominally)
            value = self._fget(obj)
            obj.__dict__[self._name] = value
        return cast(_T, value)

    def __set__(self, obj: Any, value: Any) -> None:
        """Raises unconditionally, to preserve read-only behavior.

        This decorator is intended to implement immutable (and idempotent) object
        attributes. For that reason, assignment to this property must be explicitly
        prevented.

        If this __set__ method was not present, this descriptor would become a
        *non-data descriptor*. That would be nice because the cached value would be
        accessed directly once set (__dict__ attrs have precedence over non-data
        descriptors on instance attribute lookup). The problem is, there would be
        nothing to stop assignment to the cached value, which would overwrite the result
        of `fget()` and break both the immutability and idempotence guarantees of this
        decorator.

        The performance with this __set__() method in place was roughly 0.4 usec per
        access when measured on a 2.8GHz development machine; so quite snappy and
        probably not a rich target for optimization efforts.
        """
        raise AttributeError("can't set attribute")
