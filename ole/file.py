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

        self._fp = fp

        self._header = FileHeader.from_bytes(read_at(self._fp, 0, 512))

        self._build_fat()
        self._build_minifat()
        self._build_dir_tree()

    def close(self):
        if hasattr(self._fp, 'close'):
            self._fp.close()

    def _read_sector(self, sector):
        return read_at(
            self._fp,
            (sector+1) * self._header.sector_size,
            self._header.sector_size)

    def _build_fat(self):
        sectors = self._header._difat[:self._header._num_fat_sectors]

        if self._header._num_difat_sectors > 0:
            sector = self._header._first_difat_sector
            for i in range(self._header._num_difat_sectors):
                b = self._read_sector(sector)
                difat = bytes_to_ints(b)
                sectors.extend(difat[:-1])
                sector = difat[-1]

        self._fat = sum((bytes_to_ints(self._read_sector(sector)) for sector in sectors), [])

    def _build_minifat(self):
        reader = SectorReader(
            self._fp,
            self._header.sector_size,
            sector_chain(self._fat, self._header._first_minifat_sector),
            lambda sector: (sector+1) * self._header.sector_size,
        )
        self._minifat = bytes_to_ints(reader.read())

    def _build_dir_tree(self):
        dir_entries = []

        reader = SectorReader(
            self._fp,
            self._header.sector_size,
            sector_chain(self._fat, self._header._first_dir_sector),
            lambda sector: (sector+1) * self._header.sector_size,
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
        self._dir_entries = dir_entries

    def get_stream(self, path):
        if isinstance(path, str):
            path = path.split('/')

        entry = self._dir_entries[0]
        for name in path:
            for child in entry._children:
                if child.name == name:
                    entry = child
                    break
            else:
                raise KeyError(f'cannot find path {path}')

        if entry._type != OBJECT_STREAM:
            raise TypeError('entry is not a stream')

        if entry._stream_size < self._header._mini_stream_cutoff_size:
            reader = SectorReader(
                SectorReader(
                    self._fp,
                    self._header.sector_size,
                    sector_chain(self._fat, self._dir_entries[0]._starting_sector),
                    lambda sector: (sector+1) * self._header.sector_size,
                ),
                self._header.mini_sector_size,
                sector_chain(self._minifat, entry._starting_sector),
                lambda sector: sector * self._header.mini_sector_size,
                entry._stream_size,
            )
        else:
            reader = SectorReader(
                self._fp,
                self._header.sector_size,
                sector_chain(self.fat, entry._starting_sector),
                lambda sector: (sector+1) * self._header.sector_size,
                entry._stream_size,
            )

        return Stream(entry._path, entry._stream_size, reader)


def open(fp):
    return File(fp)
