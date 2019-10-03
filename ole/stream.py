class Stream:
    def __init__(self, path, size, reader):
        self._path = path
        self.size = size
        self._reader = reader

    def __repr__(self):
        return f'<Stream path={self.path} size={self.size}>'

    @property
    def path(self):
        return '/'.join(self._path)

    def tell(self):
        return self._reader.tell()

    def seek(self, offset, whence=0):
        return self._reader.seek(offset, whence)

    def read(self, size=-1):
        return self._reader.read(size)
