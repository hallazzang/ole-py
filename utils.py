import math
import string
import struct

printables = string.ascii_letters + string.digits + string.punctuation + ' '

def hexdump(data, offset=0, size=None, *, group_by=16):
    if isinstance(data, str):
        data = data.encode()
    if size is None:
        size = len(data)

    start = math.floor(offset / group_by) * group_by
    end = math.ceil(min(len(data), offset + size) / group_by) * group_by

    print('┌' + '─'*10 + '┬' + '─'*(group_by*3+1) + '┬' + '─'*(group_by+2) + '┐')

    print('│' + 'offset'.rjust(10) + '│ ', end='')
    for i in range(group_by):
        print('%2x' % i, end=' ')
    print('│', end=' ')
    for i in range(group_by):
        print('%x' % i, end='')
    print(' │')

    print('├' + '─'*10 + '┼' + '─'*(group_by*3+1) + '┼' + '─'*(group_by+2) + '┤')

    for i in range(start, end):
        if i % group_by == 0:
            print('│ %8x' % i, end=' │ ')

        if i < offset + size and i < len(data):
            print('%02x' % data[i], end=' ')
        else:
            print('  ', end=' ')

        if (i - start + 1) % group_by == 0:
            print('│ ', end='')

            for j in range(i - group_by + 1, i + 1):
                if chr(data[j]) in printables:
                    print('%c' % chr(data[j]), end='')
                else:
                    print('.', end='')
            print(' │')

    print('└' + '─'*10 + '┴' + '─'*(group_by*3+1) + '┴' + '─'*(group_by+2) + '┘')

def bytes_to_ints(data):
    return [struct.unpack('<I', data[x*4:(x+1)*4])[0] for x in range(len(data)//4)]

class StructureMeta(type):
    def __new__(cls, clsname, bases, clsdict):
        if '_fields' not in clsdict:
            raise RuntimeError('Structure must provide its _fields')
        return super().__new__(cls, clsname, bases, clsdict)

class Structure(metaclass=StructureMeta):
    _fields = ()

    @classmethod
    def make(cls, data):
        s = cls()

        offset = 0
        for name, fmt in cls._fields:
            if fmt[0] != '<':
                fmt = '<' + fmt
            val = struct.unpack_from(fmt, data, offset)
            if len(val) == 1:
                val = val[0]
            setattr(s, name, val)
            offset += struct.calcsize(fmt)

        return s

    def __repr__(self):
        fields = ', '.join(
            '%s=%r' % (name, getattr(self, name)) for name, _ in self._fields)
        return '%s(%s)' % (self.__class__.__name__, fields)

