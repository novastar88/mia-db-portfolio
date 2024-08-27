from .exceptions import *


def not_empty(obj):
    try:
        a = len(obj)
        if a == 0:
            raise ObjectEmpty()
    except TypeError:
        ObjectWrongType()


def not_none(obj):
    if obj == None:
        raise ObjectIsNone()


def is_type(obj, typee):
    if not isinstance(obj, typee):
        raise ObjectWrongType()
