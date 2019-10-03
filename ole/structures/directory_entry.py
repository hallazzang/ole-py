from .structure import Structure


class DirectoryEntry(Structure):
    entry_name = Field('64s')
    entry_name_len = Field('H')
    object_type = Field('B')
    color_flag = Field('B')
    left_sibling_id = Field('I')
    right_sibling_id = Field('I')
    child_id = Field('I')
    clsid = Field('16s')
    state_bits = Field('I')
    creation_time = Field('Q')
    modified_time = Field('Q')
    starting_sector_loc = Field('I')
    stream_size = Field('Q')

    @property
    def name(self):
        return self.entry_name.decode('utf-16le').rstrip('\x00')
