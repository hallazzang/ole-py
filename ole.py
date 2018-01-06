from utils import *

MAXREGSECT = 0xfffffffa
DIFSECT = 0xfffffffc
FATSECT = 0xfffffffd
ENDOFCHAIN = 0xfffffffe
FREESECT = 0xffffffff

UNALLOCATED = 0x00
STORAGE = 0x01
STREAM = 0x02
ROOT_STORAGE = 0x05

MAXREGSID = 0xfffffffa
NOSTREAM = 0xffffffff

class FileHeader(Structure):
    _fields = (
        ('HeaderSignature', '8s'),
        ('HeaderCLSID', '16s'),
        ('MinorVersion', 'H'),
        ('MajorVersion', 'H'),
        ('ByteOrder', 'H'),
        ('SectorShift', 'H'),
        ('MiniSectorShift', 'H'),
        ('Reserved', '6s'),
        ('NumberOfDirectorySectors', 'I'),
        ('NumberOfFATSectors', 'I'),
        ('FirstDirectorySectorLocation', 'I'),
        ('TransactionSignatureNumber', 'I'),
        ('MiniStreamCutoffSize', 'I'),
        ('FirstMiniFATSectorLocation', 'I'),
        ('NumberOfMiniFATSectors', 'I'),
        ('FirstDIFATSectorLocation', 'I'),
        ('NumberOfDIFATSectors', 'I'),
        ('DIFAT', '109I'),
    )

class DirectoryEntry(Structure):
    _fields = (
        ('DirectoryEntryName', '64s'),
        ('DirectoryEntryNameLength', 'H'),
        ('ObjectType', 'B'),
        ('ColorFlag', 'B'),
        ('LeftSiblingID', 'I'),
        ('RightSiblingID', 'I'),
        ('ChildID', 'I'),
        ('CLSID', '16s'),
        ('StateBits', 'I'),
        ('CreationTime', 'Q'),
        ('ModifiedTime', 'Q'),
        ('StartingSectorLocation', 'I'),
        ('StreamSize', 'Q'),
    )

class OleFile:
    def __init__(self, fp):
        if isinstance(fp, str):
            fp = open(fp, 'rb')
        elif not isinstance(fp, file):
            raise RuntimeError('fp must be opened file object or string')
        elif not fp.mode.startswith('rb'):
            raise RuntimeError('file must be opened with mode rb')
        self.fp = fp

    @property
    def header(self):
        if not hasattr(self, '_header'):
            self.fp.seek(0)
            self._header = FileHeader.make(self.fp.read(512))

        return self._header

    @property
    def sector_size(self):
        return 1 << self.header.SectorShift

    @property
    def FAT(self):
        if not hasattr(self, '_FAT'):
            FAT_sectors = self.header.DIFAT[:self.header.NumberOfFATSectors]

            sector = self.header.FirstDIFATSectorLocation
            for i in range(self.header.NumberOfDIFATSectors):
                DIFAT = bytes_to_ints(self.read_sector(sector))
                FAT_sectors += DIFAT[:-1]
                sector = DIFAT[-1]

            self._FAT = bytes_to_ints(
                b''.join(self.read_sector(x) for x in FAT_sectors))

        return self._FAT

    @property
    def directory_entries(self):
        if not hasattr(self, '_directory_entries'):
            b = self.read_stream(self.header.FirstDirectorySectorLocation)
            self._directory_entries = [
                DirectoryEntry.make(b[x*128:(x+1)*128])
                for x in range(len(b)//128)]

        return self._directory_entries

    def read_sector(self, sector):
        self.fp.seek((sector+1) * self.sector_size)
        return self.fp.read(self.sector_size)

    def read_stream(self, sector):
        chunks = []
        while sector != ENDOFCHAIN:
            chunks.append(self.read_sector(sector))
            sector = self.FAT[sector]
        return b''.join(chunks)

if __name__ == '__main__':
    f = OleFile('testfile.hwp')
    for d in f.directory_entries:
        if d.ObjectType == STORAGE:
            print('storage:', end='')
        elif d.ObjectType == STREAM:
            print('stream:', end='')
        print(repr(d.DirectoryEntryName.decode('utf-16-le').rstrip('\x00')))
        print(d.ChildID)
