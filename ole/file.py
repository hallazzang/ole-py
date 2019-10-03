import io

from .constants import *
from .structures import FileHeader, DirectoryEntry
from .storage import Storage
from .stream import Stream
from .utils import (
    SectorReader,
    read_at,
    bytes_to_ints,
    sector_chain,
)


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
            sector = self.header._first_difat_sector
            for i in range(self.header._num_difat_sectors):
                b = self.read_sector(sector)
                difat = bytes_to_ints(b)
                sectors.extend(difat[:-1])
                sector = difat[-1]

        self.fat = sum((bytes_to_ints(self.read_sector(sector)) for sector in sectors), [])

    def build_minifat(self):
        reader = SectorReader(
            self.fp,
            self.header.sector_size,
            sector_chain(self.fat, self.header._first_minifat_sector),
            lambda sector: (sector+1) * self.header.sector_size,
        )
        self.minifat = bytes_to_ints(reader.read())

    def build_dir_tree(self):
        dir_entries = []

        reader = SectorReader(
            self.fp,
            self.header.sector_size,
            sector_chain(self.fat, self.header._first_dir_sector),
            lambda sector: (sector+1) * self.header.sector_size,
        )

        while True:
            bytes = reader.read(128)
            if not bytes:
                break

            dir_entry = DirectoryEntry.from_bytes(bytes)
            if dir_entry._type == 0:
                continue
            dir_entry._children = []

            dir_entries.append(dir_entry)

        def walk(id, parent, path):
            if id == NOSTREAM:
                return

            dir_entry = dir_entries[id]
            new_path = path + (dir_entry.name,)
            dir_entry._path = new_path

            if parent:
                parent._children.append(dir_entry)

            walk(dir_entry._left_sibling_id, parent, path)
            walk(dir_entry._right_sibling_id, parent, path)
            walk(dir_entry._child_id, dir_entry, new_path)

        walk(dir_entries[0]._child_id, dir_entries[0], ())
        self.dir_entries = dir_entries

    def get_stream(self, path):
        if isinstance(path, str):
            path = path.split('/')

        entry = self.dir_entries[0]
        for name in path:
            for child in entry._children:
                if child.name == name:
                    entry = child
                    break
            else:
                raise KeyError(f'cannot find path {path}')

        if entry._type != OBJECT_STREAM:
            raise TypeError('entry is not a stream')

        if entry._stream_size < self.header._mini_stream_cutoff_size:
            reader = SectorReader(
                SectorReader(
                    self.fp,
                    self.header.sector_size,
                    sector_chain(self.fat, self.dir_entries[0]._starting_sector),
                    lambda sector: (sector+1) * self.header.sector_size,
                ),
                self.header.mini_sector_size,
                sector_chain(self.minifat, entry._starting_sector),
                lambda sector: sector * self.header.mini_sector_size,
                entry._stream_size,
            )
        else:
            reader = SectorReader(
                self.fp,
                self.header.sector_size,
                sector_chain(self.fat, entry._starting_sector),
                lambda sector: (sector+1) * self.header.sector_size,
                entry._stream_size,
            )

        return Stream(entry._path, entry._stream_size, reader)


def open(fp):
    return File(fp)
