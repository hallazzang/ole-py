from .structure import Structure


class FileHeader(Structure):
    header_signature = Field('8s')
    header_clsid = Field('16s')
    minor_version = Field('H')
    major_version = Field('H')
    byte_order = Field('H')
    sector_shift = Field('H')
    mini_sector_shift = Field('H')
    reserved = Field('6s')
    num_dir_sectors = Field('I')
    num_difat_sectors = Field('I')
    first_dir_sector_loc = Field('I')
    tx_signature_no = Field('I')
    mini_stream_cutoff_size = Field('I')
    first_minifat_sector_loc = Field('I')
    num_minifat_sectors = Field('I')
    first_difat_sector_loc = Field('I')
    num_difat_sectors = Field('I')
    difat = Field('109I')
