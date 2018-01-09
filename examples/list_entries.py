from ole import OleFile

if __name__ == '__main__':
    f = OleFile('testfile.hwp')

    print('ID   SIZE      PATH')
    print('-' * 50)
    for path in f.list_entries(include_storages=False):
        entry = f.get_entry(path)
        name = b'/'.join(x.encode('unicode-escape') for x in path).decode()
        print('%-3d  %-8d  %s' % (entry.id, entry.stream_size, name))

