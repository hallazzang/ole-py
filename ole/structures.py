import struct


class StructureBase(type):
    def  __new__(cls, name, bases, attrs):
        size = 0
        for _, format in attrs['_fields']:
            size += struct.calcsize(format)
        attrs['_size'] = size
        return super().__new__(cls, name, bases, attrs)


class Structure(metaclass=StructureBase):
    _fields = ()

    def __init__(self):
        super().__setattr__('_values', {})

    @classmethod
    def from_bytes(cls, bytes):
        result = cls()

        offset = 0
        for name, format in cls._fields:
            value = struct.unpack_from(format, bytes, offset)
            if len(value) == 1:
                value = value[0]
            result._values[name] = value

            offset += struct.calcsize(format)

        return result

    def to_bytes(self):
        buf = bytearray(self._size)

        offset = 0
        for name, format in self._fields:
            value = self._values[name]
            if not isinstance(value, (tuple, list)):
                value = (value,)

            struct.pack_into(format, buf, offset, *value)
            offset += struct.calcsize(format)

        return bytes(buf)

    def __getattr__(self, name):
        if name in self._values:
            return self._values[name]
        raise AttributeError(
            f"'{self.__class__.__qualname__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in self._values:
            self._values[name] = value
        else:
            super().__setattr__(name, value)


class FileHeader(Structure):
    _fields = (
        ('_signature', '8s'),
        ('_clsid', '16s'),
        ('_minor_ver', 'H'),
        ('_major_ver', 'H'),
        ('_byte_order', 'H'),
        ('_sector_shift', 'H'),
        ('_mini_sector_shift', 'H'),
        ('_reserved', '6s'),
        ('_num_dir_sectors', 'I'),
        ('_num_fat_sectors', 'I'),
        ('_first_dir_sector', 'I'),
        ('_tx_signature_no', 'I'),
        ('_mini_stream_cutoff_size', 'I'),
        ('_first_minifat_sector', 'I'),
        ('_num_minifat_sectors', 'I'),
        ('_first_difat_sector', 'I'),
        ('_num_difat_sectors', 'I'),
        ('_difat', '109I'),
    )

    @property
    def sector_size(self):
        return 1 << self._sector_shift

    @property
    def mini_sector_size(self):
        return 1 << self._mini_sector_shift


class DirectoryEntry(Structure):
    _fields = (
        ('_name', '64s'),
        ('_name_len', 'H'),
        ('_type', 'B'),
        ('_color_flag', 'B'),
        ('_left_sibling_id', 'I'),
        ('_right_sibling_id', 'I'),
        ('_child_id', 'I'),
        ('_clsid', '16s'),
        ('_state_bits', 'I'),
        ('_creation_time', 'Q'),
        ('_modified_time', 'Q'),
        ('_starting_sector', 'I'),
        ('_stream_size', 'Q'),
    )

    @property
    def name(self):
        return self._name.decode('utf-16le').rstrip('\x00')
