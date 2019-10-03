class Stream:
    fp = None
    name = None
    path = None
    size = None
    children = None

    @staticmethod
    def from_dir_entry(dir_entry):
        stream = Stream()
        stream.name = dir_entry.name
        stream.size = dir_entry._stream_size
        stream.children = []

        return stream

    def __repr__(self):
        return f'<Stream name={self.name} path={self.path}>'
