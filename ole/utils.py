import io
import itertools
import struct

from .constants import *


def bytes_to_ints(b):
    return [
        struct.unpack('I', bytes(x))[0]
        for x in itertools.zip_longest(*([iter(b)] * 4))]


def read_at(fp, offset, n):
    if fp.seek(offset) != offset:
        raise RuntimeError(f'seek({offset}) operation failed')
    b = fp.read(n)
    if len(b) < n:
        raise RuntimeError(f'read({n}) operation failed')
    return b


class SectorReader:
    def __init__(self, src, sector_size, sectors, offset_resolver, size=None):
        self.src = src
        self.sector_size = sector_size
        self.sectors = sectors
        self.offset_resolver = offset_resolver

        self.offset = 0
        self.max_offset = min(sector_size*len(sectors), size or float('inf'))

    def tell(self):
        return self.offset

    def seek(self, offset, whence=0):
        if whence == 0:
            new_offset = offset
        elif whence == 1:
            new_offset = self.offset + offset
        elif whence == 2:
            new_offset = self.max_offset + offset
        else:
            raise ValueError(f'whence value {whence} unsupported')

        if new_offset < 0:
            raise ValueError(f'invalid offset {new_offset}')

        self.offset = new_offset
        return self.offset

    def read(self, size=-1):
        if self.offset >= self.max_offset:
            return b''

        if size == -1 or size > self.max_offset - self.offset:
            size = self.max_offset - self.offset

        chunks = []
        read = 0
        while read < size:
            offset = self.offset_resolver(self.sectors[self.offset // self.sector_size])
            sector_offset = self.offset % self.sector_size

            to_read = min(size - read, self.sector_size - sector_offset)
            chunks.append(read_at(self.src, offset + sector_offset, to_read))
            read += to_read
            self.offset += to_read

        return b''.join(chunks)


def sector_chain(fat, starting_sector):
    sectors = []
    sector = starting_sector
    while sector != ENDOFCHAIN:
        sectors.append(sector)
        sector = fat[sector]
    return sectors
