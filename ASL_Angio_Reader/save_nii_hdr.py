"""
File: save_nii_hdr.py
Save NIFTI dataset header. Supports both *.nii and *.hdr/*.img
file extension.
Usage: save_nii_hdr(hdr, filename)
Translated from Matlab by Lúcio Moreira (luciomdm@outlook.com)
"""
import os
import struct

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

    write_header_key(filename, hdr['hk'])
    write_image_dimension(filename, hdr['dime'])
    write_data_history(filename, hdr['hist'])

    byte_size =  os.path.getsize(filename)

    if byte_size != 348:
        raise(Exception('Header size is not 348 bytes.'))
    
    return

def write_header_key(filename, hk):
     """

     """
     f = open(filename, "w")
       
     f.write(struct.pack('i', hk['sizeof_hdr']))  # must be 348.
    
     data_type_padded = (hk['data_type'] + '\0'*10)[:10]  # Padding data_type to 10 characters
     f.write(data_type_padded.encode('utf-8'))
    
     db_name_padded = (hk['db_name'] + '\0'*18)[:18]  # Padding db_name to 18 characters
     f.write(db_name_padded.encode('utf-8'))
    
     f.write(struct.pack('i', hk['extents'])) #int32
     f.write(struct.pack('h', hk['session_error'])) #int16
     f.write(struct.pack('B', hk['regular']))  # might be uint8
    
     f.write(struct.pack('B', hk['dim_info'])) #uchar

     f.close()
    
     return

def write_image_dimension(filename, dime):
    """


    """
    f = open(filename, 'w')

    # Writing data to the file using struct module
    f.write(struct.pack('8h', *dime['dim'][:8]))                  # int16
    f.write(struct.pack('f', dime['intent_p1'][0]))              # float32
    f.write(struct.pack('f', dime['intent_p2'][0]))              # float32
    f.write(struct.pack('f', dime['intent_p3'][0]))              # float32
    f.write(struct.pack('h', dime['intent_code'][0]))            # int16
    f.write(struct.pack('h', dime['datatype'][0]))               # int16
    f.write(struct.pack('h', dime['bitpix'][0]))                 # int16
    f.write(struct.pack('h', dime['slice_start'][0]))            # int16
    f.write(struct.pack('8f', *dime['pixdim'][:8]))              # float32
    f.write(struct.pack('f', dime['vox_offset'][0]))             # float32
    f.write(struct.pack('f', dime['scl_slope'][0]))              # float32
    f.write(struct.pack('f', dime['scl_inter'][0]))              # float32
    f.write(struct.pack('h', dime['slice_end'][0]))              # int16
    f.write(struct.pack('B', dime['slice_code'][0]))             # uchar
    f.write(struct.pack('B', dime['xyzt_units'][0]))             # uchar
    f.write(struct.pack('f', dime['cal_max'][0]))                # float32
    f.write(struct.pack('f', dime['cal_min'][0]))                # float32
    f.write(struct.pack('f', dime['slice_duration'][0]))         # float32
    f.write(struct.pack('f', dime['toffset'][0]))                # float32
    f.write(struct.pack('i', dime['glmax'][0]))                  # int32
    f.write(struct.pack('i', dime['glmin'][0]))                  # int32
    f.close()

    return  # image_dimension

def write_data_history(filename, hist):
    """
	  
    """
    # Pad descrip field to 80 characters
    f = open(filename)
    pad_descrip = b'\0' * (80 - len(hist['descrip']))
    hist_descrip_padded = (hist['descrip'] + pad_descrip)[:80]
    f.write(hist_descrip_padded.encode('utf-8'))  # uchar
    
    # Pad aux_file field to 24 characters
    pad_aux_file = b'\0' * (24 - len(hist['aux_file']))
    hist_aux_file_padded = (hist['aux_file'] + pad_aux_file)[:24]
    f.write(hist_aux_file_padded.encode('utf-8'))  # uchar
    
    # Write remaining fields
    f.write(struct.pack('h', hist['qform_code']))  # int16
    f.write(struct.pack('h', hist['sform_code']))  # int16
    f.write(struct.pack('f', hist['quatern_b']))  # float32
    f.write(struct.pack('f', hist['quatern_c']))  # float32
    f.write(struct.pack('f', hist['quatern_d']))  # float32
    f.write(struct.pack('f', hist['qoffset_x']))  # float32
    f.write(struct.pack('f', hist['qoffset_y']))  # float32
    f.write(struct.pack('f', hist['qoffset_z']))  # float32
    f.write(struct.pack('4f', *hist['srow_x'][:4]))  # float32 (4 elements)
    f.write(struct.pack('4f', *hist['srow_y'][:4]))  # float32 (4 elements)
    f.write(struct.pack('4f', *hist['srow_z'][:4]))  # float32 (4 elements)
    
    # Pad intent_name field to 16 characters
    pad_intent_name = b'\0' * (16 - len(hist['intent_name']))
    hist_intent_name_padded = (hist['intent_name'] + pad_intent_name)[:16]
    f.write(hist_intent_name_padded.encode('utf-8'))  # uchar
    
    # Pad magic field to 4 characters
    pad_magic = b'\0' * (4 - len(hist['magic']))
    hist_magic_padded = (hist['magic'] + pad_magic)[:4]
    f.write(hist_magic_padded.encode('utf-8'))  # uchar

    f.close()
    
    return

    
        
        