import struct


class Field:
    _name = None
    _format = None
    _offset = None

    def __init__(self, format):
        self._format = format

    def __get__(self, obj, type):
        return obj._values[self._name]

    def __set__(self, obj, value):
        obj._values[self._name] = value


class StructureBase(type):
    @classmethod
    def __prepare__(meta, name, bases):
        return {'Field': Field}

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        new_class._fields = []
        new_class._size = 0
        for name, attr in attrs.items():
            if isinstance(attr, Field):
                attr._name = name
                attr._offset = new_class._size
                new_class._fields.append(attr)
                new_class._size += struct.calcsize(attr._format)

        return new_class


class Structure(metaclass=StructureBase):
    def __init__(self):
        self._values = {}

    @classmethod
    def decode(cls, data):
        if len(data) != cls._size:
            raise ValueError('wrong data size')

        instance = cls()
        for field in cls._fields:
            value = struct.unpack_from(field._format, data, field._offset)
            if len(value) == 1:
                value = value[0]
            instance._values[field._name] = value

        return instance
