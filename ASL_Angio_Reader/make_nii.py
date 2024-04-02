"""
Make nii structure specified by 3D matrix [x y z]. It also takes
4D matrix like [x y z t]. Optional features can also be included, 
such as: voxel_size, origin, datatype, and description.
 
Usage: nii = make_nii(img, [voxel_size], [origin], [datatype], ...
[description])

Where:

img:			3D matrix [x y z], or 4D matrix that
				includes all the images along the
				time course [x y z t]

voxel_size (optional):	Voxel size in millimeter for each
				dimension. Default is [1 1 1].

origin (optional):	The AC origin. Default is [0 0 0].

datatype (optional):	Storage data type. Default is float32 [16]:
		2 - uint8,  4 - int16,  8 - int32,  16 - float32,
		32 - complex64,  64 - float64,  128 - RGB24,
		256 - int8,  512 - uint16,  768 - uint32, 1792 - complex128
        
description (optional):	Description of data. Default is ''.

e.g.:
     origin = [33 44 13]; datatype = 64;
     nii = make_nii(img, [], origin, datatype);    % default voxel_size

  NIFTI data format can be found on: http://nifti.nimh.nih.gov

  - Jimmy Shen (pls@rotman-baycrest.on.ca)

"""
import numpy as np

def make_nii(*args):
    
    nii = {'img': args[0]}
    dims = nii['img'].shape
    dims = (len(dims),) + dims + (1,) * 8
    dims = dims[:8] #Limit dims to 8 elements

    voxel_size = (0,) + (1,) * 7
    origin = (0,) * 5
    datatype = 16
    descrip = ''

    #Processing variable argument number
    if len(args) > 1 and args[1] is not None:
        voxel_size = (voxel_size[0],) + tuple(float(v) for v in args[1]) + voxel_size[4:]
    if len(args) > 2 and args[2] is not None:
        origin = tuple(float(o) for o in args[2]) + origin[3:]
    if len(args) > 3 and args[3] is not None:
        datatype = int(args[3])
    if len(args) > 4 and args[4] is not None:
        descrip = args[4]

    # Fix dims in the case of RGB datatype
    if datatype == 128:
        dims = (dims[0]-1,) + dims[1:4] + dims[5:8] + (1,)

    maxval = np.round(np.max(nii['img'])).astype(int)
    minval = np.round(np.min(nii['img'])).astype(int)

    nii['hdr'] = make_header(dims, voxel_size, origin, datatype, descrip, maxval, minval)

    dtype_mapping = {
        2: np.uint8,
        4: np.int16,
        8: np.int32,
        16: np.float32,
        32: np.float32,
        64: np.float64,
        128: np.uint8,
        256: np.int8,
        512: np.uint16,
        768: np.uint32,
        1792: np.float64
    }

    #Check if provided datatype is supported
    if nii['hdr']['dime']['datatype'] in dtype_mapping:
        nii['img'] = nii['img'].astype(dtype_mapping[nii['hdr']['dime']['datatype']])
    else:
        raise ValueError('Datatype is not supported by make_nii.')
    
    return nii

def make_header(dims, voxel_size, origin, datatype, descrip, maxval, minval):
    hdr = {}
    hdr['hk'] = header_key()
    hdr['dime'] = image_dimension(dims, voxel_size, datatype, maxval, minval)
    hdr['hist'] = data_history(origin, descrip)
    return hdr

def header_key():
    hk = {}
    hk['sizeof_hdr'] = 348  # must be 348!
    hk['data_type'] = ''
    hk['db_name'] = ''
    hk['extents'] = 0
    hk['session_error'] = 0
    hk['regular'] = 'r'
    hk['dim_info'] = 0
    return hk

def image_dimension(dims, voxel_size, datatype, maxval, minval):
    dime = {}
    dime['dim'] = dims
    dime['intent_p1'] = 0
    dime['intent_p2'] = 0
    dime['intent_p3'] = 0
    dime['intent_code'] = 0
    dime['datatype'] = datatype

    bitpix_map = {
    2: 8,
    4: 16,
    8: 32,
    16: 32,
    32: 64,
    64: 64,
    128: 24,
    256: 8,
    512: 16,
    768: 32,
    1792: 128
    }

    if datatype in bitpix_map:
        dime['bitpix'] = bitpix_map[datatype]
    else:
        raise ValueError('Datatype is not supported by make_nii.')

    
    dime['slice_start'] = 0
    dime['pixdim'] = voxel_size
    dime['vox_offset'] = 0
    dime['scl_slope'] = 0
    dime['scl_inter'] = 0
    dime['slice_end'] = 0
    dime['slice_code'] = 0
    dime['xyzt_units'] = 0
    dime['cal_max'] = 0
    dime['cal_min'] = 0
    dime['slice_duration'] = 0
    dime['toffset'] = 0
    dime['glmax'] = maxval
    dime['glmin'] = minval

    return dime


def data_history(origin, descrip):
    hist = {
        'descrip': descrip,
        'aux_file': 'none',
        'qform_code': 0,
        'sform_code': 0,
        'quatern_b': 0,
        'quatern_c': 0,
        'quatern_d': 0,
        'qoffset_x': 0,
        'qoffset_y': 0,
        'qoffset_z': 0,
        'srow_x': [0, 0, 0, 0],
        'srow_y': [0, 0, 0, 0],
        'srow_z': [0, 0, 0, 0],
        'intent_name': '',
        'magic': '',
        'originator': origin
    }

    return hist








