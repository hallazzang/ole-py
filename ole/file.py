import io

from .constants import *
from .structures import FileHeader, DirectoryEntry
from .storage import Storage
from .stream import Stream
from .utils import read_at, bytes_to_ints, SectorReader


def is_binary_file(fp):
    return (
        hasattr(fp, 'read')
        and hasattr(fp, 'seek')
        and hasattr(fp, 'mode')
        and fp.mode == 'rb')


class File:
    def __init__(self, fp):
        if isinstance(fp, str):
            fp = io.open(fp, 'rb')
        elif isinstance(fp, bytes):
            fp = io.BytesIO(fp)
        elif not is_binary_file(fp):
            raise TypeError('fp must be a binary file-like object')

        self.fp = fp

        self.header = FileHeader.from_bytes(read_at(self.fp, 0, 512))

        self.build_fat()
        self.build_minifat()
        self.build_dir_tree()

    def close(self):
        if hasattr(self.fp, 'close'):
            self.fp.close()

    def read_sector(self, sector):
        return read_at(
            self.fp,
            (sector+1) * self.header.sector_size,
            self.header.sector_size)

    def build_fat(self):
        sectors = self.header._difat[:self.header._num_fat_sectors]

        if self.header._num_difat_sectors > 0:
            sector = self.header._first_difat_sector_loc
            for i in range(self.header._num_difat_sectors):
                b = self.read_sector(sector)
                difat = bytes_to_ints(b)
                sectors.extend(difat[:-1])
                sector = difat[-1]

        self.fat = []
        for sector in sectors:
            self.fat.extend(bytes_to_ints(self.read_sector(sector)))

    def build_minifat(self):
        r = SectorReader(
            self.fp,
            self.header.sector_size,
            self.header._first_minifat_sector_loc,
            self.fat,
            lambda sector: (sector+1) * self.header.sector_size)
        self.minifat = bytes_to_ints(r.read())

    def build_dir_tree(self):
        dir_entries = []

        r = SectorReader(
            self.fp,
            self.header.sector_size,
            self.header._first_dir_sector_loc,
            self.fat,
            lambda sector: (sector+1) * self.header.sector_size)

        while True:
            b = r.read(128)
            if not b:
                break

            dir_entry = DirectoryEntry.from_bytes(b)
            if dir_entry._type == 0:
                continue

            dir_entries.append(dir_entry)

        def walk(id, parent, path):
            dir_entry = dir_entries[id]

            if dir_entry._left_sibling_id != NOSTREAM:
                walk(dir_entry._left_sibling_id, parent, path)
            if dir_entry._right_sibling_id != NOSTREAM:
                walk(dir_entry._right_sibling_id, parent, path)

            if dir_entry._type in (OBJECT_ROOT_STORAGE, OBJECT_STORAGE):
                obj = Storage.from_dir_entry(dir_entry)
            else:
                obj = Stream.from_dir_entry(dir_entry)
                obj.fp = self.fp

            if parent:
                parent.children.append(obj)

            new_path = path + (obj.name,)
            obj.path = new_path

            if dir_entry._child_id != NOSTREAM:
                walk(dir_entry._child_id, obj, new_path)

            return obj

        self.dir_tree_root = walk(0, None, ())


def open(fp):
    return File(fp)
