class Storage:
    name = None
    path = None
    children = None

    @staticmethod
    def from_dir_entry(dir_entry):
        storage = Storage()
        storage.name = dir_entry.name
        storage.children = []

        return storage

    def __repr__(self):
        return f'<Storage name={self.name} path={self.path}>'
