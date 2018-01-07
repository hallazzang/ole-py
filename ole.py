from utils import *

MAXREGSECT = 0xfffffffa
DIFSECT = 0xfffffffc
FATSECT = 0xfffffffd
ENDOFCHAIN = 0xfffffffe
FREESECT = 0xffffffff

MAXREGSID = 0xfffffffa
NOSTREAM = 0xffffffff

OBJECT_STORAGE = 0x01
OBJECT_STREAM = 0x02

class FileHeader(Structure):
    _fields = (
        ('_HeaderSignature', '8s'),
        ('_HeaderCLSID', '16s'),
        ('_MinorVersion', 'H'),
        ('_MajorVersion', 'H'),
        ('_ByteOrder', 'H'),
        ('_SectorShift', 'H'),
        ('_MiniSectorShift', 'H'),
        ('_Reserved', '6s'),
        ('_NumberOfDirectorySectors', 'I'),
        ('_NumberOfFATSectors', 'I'),
        ('_FirstDirectorySectorLocation', 'I'),
        ('_TransactionSignatureNumber', 'I'),
        ('_MiniStreamCutoffSize', 'I'),
        ('_FirstMiniFATSectorLocation', 'I'),
        ('_NumberOfMiniFATSectors', 'I'),
        ('_FirstDIFATSectorLocation', 'I'),
        ('_NumberOfDIFATSectors', 'I'),
        ('_DIFAT', '109I'),
    )

class DirectoryEntry(Structure):
    _fields = (
        ('_DirectoryEntryName', '64s'),
        ('_DirectoryEntryNameLength', 'H'),
        ('_ObjectType', 'B'),
        ('_ColorFlag', 'B'),
        ('_LeftSiblingID', 'I'),
        ('_RightSiblingID', 'I'),
        ('_ChildID', 'I'),
        ('_CLSID', '16s'),
        ('_StateBits', 'I'),
        ('_CreationTime', 'Q'),
        ('_ModifiedTime', 'Q'),
        ('_StartingSectorLocation', 'I'),
        ('_StreamSize', 'Q'),
    )

    def __init__(self):
        self._children = set()

    @property
    def name(self):
        return self._DirectoryEntryName.decode('utf-16le').rstrip('\x00')

    @property
    def type(self):
        return self._ObjectType

    @property
    def CLSID(self):
        return self._CLSID

    @property
    def start_sector(self):
        if self.type != OBJECT_STREAM:
            return None
        return self._StartingSectorLocation

    @property
    def children(self):
        return self._children

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
        return 1 << self.header._SectorShift

    @property
    def FAT(self):
        if not hasattr(self, '_FAT'):
            FAT_sectors = self.header._DIFAT[:self.header._NumberOfFATSectors]

            sector = self.header._FirstDIFATSectorLocation
            for i in range(self.header._NumberOfDIFATSectors):
                DIFAT = bytes_to_ints(self.read_sector(sector))
                FAT_sectors += DIFAT[:-1]
                sector = DIFAT[-1]

            self._FAT = bytes_to_ints(
                b''.join(self.read_sector(x) for x in FAT_sectors))

        return self._FAT

    @property
    def directory_entries(self):
        if not hasattr(self, '_directory_entries'):
            b = self.read_stream(self.header._FirstDirectorySectorLocation)
            self._directory_entries = [
                DirectoryEntry.make(b[x*128:(x+1)*128])
                for x in range(len(b)//128)]
            self._build_directory_tree()

        return self._directory_entries

    @property
    def root_storage(self):
        return self.directory_entries[0]

    def read_sector(self, sector):
        self.fp.seek((sector+1) * self.sector_size)
        return self.fp.read(self.sector_size)

    def read_stream(self, sector):
        chunks = []
        while sector != ENDOFCHAIN:
            chunks.append(self.read_sector(sector))
            sector = self.FAT[sector]
        return b''.join(chunks)

    def _build_directory_tree(self):
        def walk(entry_id, parent):
            if entry_id == NOSTREAM:
                return
            entry = self._directory_entries[entry_id]

            if parent:
                parent._children.add(entry)

            walk(entry._LeftSiblingID, parent)
            walk(entry._RightSiblingID, parent)

            walk(entry._ChildID, entry)

        root = self._directory_entries[0]
        walk(root._ChildID, root)

    def list_entries(self, *, include_storages=True, include_streams=True):
        r = []

        def walk(entry, prefixes):
            for child in entry.children:
                if (child.type == OBJECT_STORAGE and include_storages
                    or child.type == OBJECT_STREAM and include_streams):
                    r.append(prefixes + (child.name,))
                walk(child, prefixes + (child.name,))

        walk(self.root_storage, ())

        return r

if __name__ == '__main__':
    f = OleFile('testfile.hwp')

    for x in f.list_entries(include_storages=False):
        print('/'.join(x))
