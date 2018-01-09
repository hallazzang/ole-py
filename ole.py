import io

from utils import *

SIGNATURE = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'

MAXREGSECT = 0xfffffffa
DIFSECT = 0xfffffffc
FATSECT = 0xfffffffd
ENDOFCHAIN = 0xfffffffe
FREESECT = 0xffffffff

MAXREGSID = 0xfffffffa
NOSTREAM = 0xffffffff

OBJECT_ROOT_STORAGE = 0x05
OBJECT_STORAGE = 0x01
OBJECT_STREAM = 0x02

class Header(Structure):
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

    def validate(self):
        if self._HeaderSignature != SIGNATURE:
            raise RuntimeError('invalid header signature')
        if self._HeaderCLSID != b'\x00' * 16:
            raise RuntimeError('invalid header CLSID')
        if self._MinorVersion != 0x003e:
            raise RuntimeError('invalid minor version')
        if self._MajorVersion not in (0x0003, 0x0004):
            raise RuntimeError('invalid major version')
        if self._ByteOrder != 0xfffe:
            raise RuntimeError('invalid byte order')
        if self._SectorShift not in (0x0009, 0x000c):
            raise RuntimeError('invalid sector shift')
        if self._MiniSectorShift != 0x0006:
            raise RuntimeError('invalid mini sector shift')
        if self._Reserved != b'\x00' * 6:
            raise RuntimeError('invalid reserved')
        if (self._MajorVersion == 3
                and self._NumberOfDirectorySectors != 0):
            raise RuntimeError('invalid number of directory sectors')
        if self._MiniStreamCutoffSize != 0x00001000:
            raise RuntimeError('invalid mini stream cutoff size')

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
    def id(self):
        return self._id

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
        if self.type not in(OBJECT_ROOT_STORAGE, OBJECT_STREAM):
            return None
        return self._StartingSectorLocation

    @property
    def stream_size(self):
        return self._StreamSize

    @property
    def children(self):
        return self._children

    def validate(self):
        try:
            for invalid_char in '/\:!':
                if invalid_char in self.name:
                    raise RuntimeError('invalid character in name')
        except UnicodeDecodeError:
            raise RuntimeError('invalid directory entry name')

        if (self._DirectoryEntryNameLength != 0
                and self._DirectoryEntryNameLength != (len(self.name)+1)*2):
            raise RuntimeError('invalid directory entry name length')
        if self._ObjectType not in (0x00, 0x01, 0x02, 0x05):
            raise RuntimeError('invalid object type')
        if self._ColorFlag not in (0x00, 0x01):
            raise RuntimeError('invalid color flag')
        if self._LeftSiblingID != NOSTREAM and self._LeftSiblingID >= MAXREGSID:
            raise RuntimeError('invalid left sibling id')
        if self._RightSiblingID != NOSTREAM and self._RightSiblingID >= MAXREGSID:
            raise RuntimeError('invalid right sibling id')
        if self._ChildID != NOSTREAM and self._ChildID >= MAXREGSID:
            raise RuntimeError('invalid child id')
        if self._ObjectType == 0x02 and self._CLSID != b'\x00' * 16:
            raise RuntimeError('invalid CLSID')
        if self._ObjectType == 0x05 and self._CreationTime != 0:
            raise RuntimeError('invalid creation time')
        # if self._ObjectType == 0x05 and self._ModifiedTime != 0:
        #     raise RuntimeError('invalid modified time')

class OleFile:
    def __init__(self, fp):
        if isinstance(fp, str):
            fp = open(fp, 'rb')
        elif isinstance(fp, bytes):
            if len(fp) < 512:  # Minimum OLE file size
                raise RuntimeError('data is too small')
            fp = io.BytesIO(fp)
        elif not hasattr(fp, 'read'):
            raise RuntimeError('fp must be opened file object or str, or bytes')
        elif not fp.mode.startswith('rb'):
            raise RuntimeError('file must be opened with mode rb')
        self.fp = fp

    @property
    def header(self):
        if not hasattr(self, '_header'):
            self.fp.seek(0)
            self._header = Header.make(self.fp.read(512))
            self._header.validate()

        return self._header

    @property
    def sector_size(self):
        return 1 << self.header._SectorShift

    @property
    def mini_sector_size(self):
        return 1 << self.header._MiniSectorShift

    @property
    def FAT(self):
        if not hasattr(self, '_FAT'):
            FAT_sectors = self.header._DIFAT[:self.header._NumberOfFATSectors]

            sector = self.header._FirstDIFATSectorLocation
            for i in range(self.header._NumberOfDIFATSectors):
                DIFAT = bytes_to_ints(self._read_sector(sector))
                FAT_sectors += DIFAT[:-1]
                sector = DIFAT[-1]

            self._FAT = bytes_to_ints(
                b''.join(self._read_sector(x) for x in FAT_sectors))

        return self._FAT

    @property
    def miniFAT(self):
        if not hasattr(self, '_miniFAT'):
            self._miniFAT = bytes_to_ints(self._read_stream(
                self.header._FirstMiniFATSectorLocation))

        return self._miniFAT

    @property
    def directory_entries(self):
        if not hasattr(self, '_directory_entries'):
            b = self._read_stream(
                self.header._FirstDirectorySectorLocation)
            self._directory_entries = [
                DirectoryEntry.make(b[x*128:(x+1)*128])
                for x in range(len(b)//128)]
            for i, entry in enumerate(self._directory_entries):
                entry._id = i
                entry.validate()
            self._build_directory_tree()

        return self._directory_entries

    @property
    def root_storage(self):
        return self.directory_entries[0]

    def list_entries(self, *, include_storages=True, include_streams=True):
        r = []

        def walk(entry, prefixes):
            for child in entry.children:
                if (child.type == OBJECT_STORAGE and include_storages
                        or child.type == OBJECT_STREAM and include_streams):
                    r.append(prefixes + (child.name,))
                walk(child, prefixes + (child.name,))

        walk(self.root_storage, ())

        return sorted(r)

    def get_entry(self, path):
        if isinstance(path, str):
            path = path.split('/')

        entry = self.root_storage
        for name in path:
            for child in entry.children:
                if child.name == name:
                    break
            else:
                return None
            entry = child

        return entry

    def get_stream(self, path):
        if isinstance(path, (tuple, list)):
            path = '/'.join(path)

        entry = self.get_entry(path)
        if entry.type != 0x02:
            raise RuntimeError('entry type is not stream')

        if entry.stream_size < self.header._MiniStreamCutoffSize:
            return self._read_mini_stream(entry.start_sector)
        else:
            return self._read_stream(entry.start_sector)

    def _read_sector(self, sector):
        self.fp.seek((sector+1) * self.sector_size)
        return self.fp.read(self.sector_size)

    def _read_stream(self, sector):
        chunks = []
        while sector != ENDOFCHAIN:
            chunks.append(self._read_sector(sector))
            sector = self.FAT[sector]
        return b''.join(chunks)

    def _read_mini_sector(self, sector):
        b = self._read_stream(self.root_storage.start_sector)
        return b[sector*self.mini_sector_size:(sector+1)*self.mini_sector_size]

    def _read_mini_stream(self, sector):
        chunks = []
        while sector != ENDOFCHAIN:
            chunks.append(self._read_mini_sector(sector))
            sector = self.miniFAT[sector]
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

        walk(self._directory_entries[0]._ChildID, self._directory_entries[0])

