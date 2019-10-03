class Storage:
    def __init__(self, path):
        self._path = path
        self._children = []

    def __repr__(self):
        return f'<Storage path={path}>'

    @property
    def path(self):
        return '/'.join(self._path)
