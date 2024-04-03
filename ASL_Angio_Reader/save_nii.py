import numpy as np
"""
save_nii(nii, filename, old_RGB=False):
Save NIFTI dataset. Support both *.nii and .hdr / .img file extension.
If file extension is not provided, *.hdr/ .img will be used as default.

Parameters:
    nii: nii data in dictionary form (containing fields 'hdr' and 'img')
        for more details in nii structure, see function make_nii.

    filename: NIFTI file name 

    old_RGB: an optional boolean variable to handle special RGB data 
        sequence [R1 R2 ... G1 G2 ... B1 B2 ...] that is used only by 
        AnalyzeDirect (Analyze Software). Since both NIfTI and Analyze
        file format use RGB triple [R1 G1 B1 R2 G2 B2 ...] sequentially
        for each voxel, this variable is set to FALSE by default. If you
        would like the saved image only to be opened by AnalyzeDirect 
        Software, set old_RGB to TRUE (or 1).

"""
def save_nii(nii, filename, old_RGB=False):

    #checking the validity of nii data
    if nii is None or not hasattr(nii, 'hdr') or not hasattr(nii, 'img') or filename is None:
        raise ValueError('Usage: save_nii(nii, filename, [old_RGB])')
      
    filetype = 1
    
    if '.nii' in filename:
        filetype = 2
        filename = filename.replace('.nii', '')
    
    if '.hdr' in filename:
        filename = filename.replace('.hdr', '')
    
    if '.img' in filename:
        filename = filename.replace('.img', '')
    
    write_nii(nii, filetype, filename, old_RGB)
    
    if filetype == 1:
        # So earlier versions of SPM can also open it with correct originator
        M = np.array([[np.diag(nii.hdr.dime.pixdim[1:4]), 
                       -nii.hdr.hist.originator[0:3] * nii.hdr.dime.pixdim[1:4]], 
                      [0, 0, 0, 1]])
        np.save(filename, M)

import numpy as np

def write_nii(nii, filetype, filename, old_RGB):
    hdr = nii['hdr']

    # Define datatype to precision mapping
    datatype_precision = {
        1: ('ubit1', np.uint8),
        2: ('uint8', np.uint8),
        4: ('int16', np.int16),
        8: ('int32', np.int32),
        16: ('float32', np.float32),
        32: ('float32', np.float32),
        64: ('float64', np.float64),
        128: ('uint8', np.uint8),
        256: ('int8', np.int8),
        512: ('uint16', np.uint16),
        768: ('uint32', np.uint32),
        1024: ('int64', np.int64),
        1280: ('uint64', np.uint64),
        1792: ('float64', np.float64)
    }

    if hdr['dime']['datatype'] not in datatype_precision:
        raise ValueError('This datatype is not supported')

    dtype = datatype_precision[hdr['dime']['datatype']]

    hdr['dime']['glmax'] = np.round(np.max(nii['img']))
    hdr['dime']['glmin'] = np.round(np.min(nii['img']))

    if filetype == 2:
        with open(f'{filename}.nii', 'wb') as fid:
            hdr['dime']['vox_offset'] = 352
            hdr['hist']['magic'] = b'n+1'
            save_nii_hdr(hdr, fid)
        skip_bytes = hdr['dime']['vox_offset'] - 348
    else:
        with open(f'{filename}.hdr', 'wb') as fid:
            hdr['dime']['vox_offset'] = 0
            hdr['hist']['magic'] = b'ni1'
            save_nii_hdr(hdr, fid)
            fid.close()
            fid = open(f'{filename}.img', 'wb')
        skip_bytes = 0


    if hdr['dime']['datatype'] == 128:
        if nii['img'].shape[3] != 3:
            raise ValueError('The NII structure does not appear to have 3 RGB color planes in the 4th dimension')

        if old_RGB:
            nii['img'] = np.transpose(nii['img'], (0, 1, 3, 2, 4))
        else:
            nii['img'] = np.transpose(nii['img'], (3, 0, 1, 2, 4))

    if hdr['dime']['datatype'] == 32 or hdr['dime']['datatype'] == 1792:
        real_img = np.real(nii['img']).flatten()
        imag_img = np.imag(nii['img']).flatten()
        nii['img'] = np.concatenate((real_img, imag_img))

    if skip_bytes:
        fid.write(b'\x00' * skip_bytes)

    nii['img'].flatten().astype(dtype).tofile(fid)

    fid.close()

    return


