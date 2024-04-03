"""
File: save_nii_hdr.py
Save NIFTI dataset header. Supports both *.nii and *.hdr/*.img
file extension.
Usage: save_nii_hdr(hdr, filename)
Translated from Matlab by Lúcio Moreira (luciomdm@outlook.com)
"""

def save_nii_hdr(hdr, filename):
    """
    Parameters:
    - hdr: Dictionary with NIFTI header fields
    - filename: NIFTI filename without extension
    Output:
    Saves header to filename.
    """
    if hdr['hk']['sizeof_hdr'] != 348:
        raise Exception("hdr['hk']['sizeof_hdr'] must be 348.")
    
    if hdr['hist']['qform_code'] == 0 and hdr['hist']['sform_code'] == 0:
        hdr['hist']['sform_code'] = 1
        hdr['hist']['srow_x'][0] = hdr['dime']['pixdim'][1]
        hdr['hist']['srow_x'][1] = 0 
        hdr['hist']['srow_x'][2] = 0
        hdr['hist']['srow_x'][3] = (1 - hdr['hist']['originator'][0])*hdr['dime']['pixdim'][1]

        hdr['hist']['srow_y'][0] = hdr['dime']['pixdim'][2]
        hdr['hist']['srow_y'][1] = 0 
        hdr['hist']['srow_y'][2] = 0
        hdr['hist']['srow_y'][3] = (1 - hdr['hist']['originator'][1])*hdr['dime']['pixdim'][2]

        hdr['hist']['srow_z'][0] = hdr['dime']['pixdim'][3]
        hdr['hist']['srow_z'][1] = 0 
        hdr['hist']['srow_z'][2] = 0
        hdr['hist']['srow_z'][3] = (1 - hdr['hist']['originator'][2])*hdr['dime']['pixdim'][3]

    write_header(hdr, filename)

    return
        
        