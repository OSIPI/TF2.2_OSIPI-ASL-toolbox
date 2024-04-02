import re
import numpy as np
from tqdm import trange
import make_nii
import gc


# PAR File lines (0-indexed):
# 0-10 = Data Description
# 11-46 = General Information
# 47-51 = Pixel Values
# 52-96 = Image Information Definition
# 97-99 = Header von "Image Information"
# 100-end = real Image part

def MIP_reader(filename):
    # Read image parameter from PAR file
    with open(filename + '.PAR', 'r') as parfile:
        pardata = parfile.readlines()

    # Read relevant image acquisition parameters
    for curr_line in range(11, 47):
        temp = re.split(r':', pardata[curr_line])
        temp2 = temp[0].strip()
        if temp2.startswith('#'):
            continue  # Ignore comments
        if 'Max. number of slices/locations' in temp2:
            NSlices = int(temp[1])
        if 'Number of label types   <0=no ASL>' in temp2:
            NDynamics = int(temp[1])
        if 'Max. number of cardiac phases' in temp2:
            NPhases = int(temp[1])

    # Choose line where the slice information starts
    curr_line = 100
    last_line = len(pardata)

    # read out the important values
    # counting begins after the header (line 100)
    for curr_line in range(100, last_line):
        param = list(map(float, pardata[curr_line].split()))
        RI = param[11]
        RS = param[12]
        SS = param[13]
        xRes = param[9]
        yRes = param[10]

    Itype = 4
    del(pardata)
    gc.collect() 

    # Read full data
    recdata = open(filename + '.REC', 'r')

    # Create a progress bar for separating image types
    for x in trange(Itype + 1):
        if x == 0:
            # Example data loading and reshaping, replace with actual code
            recdata = np.random.randint(0, 100, size=(xRes * yRes * NDynamics * NSlices * NPhases), dtype=np.int16)
            ASLdatamag = np.reshape(recdata, (xRes, yRes, 2, NDynamics // 2, NSlices, NPhases))

    # Clear recdata
    del recdata
    gc.collect() 

    # Separate even and odd numbered Labels
    even = ASLdatamag[:, :, 1, :, :, :]
    odd = ASLdatamag[:, :, 0, :, :, :]

    # Recalculate values as described in PAR file
    PV_odd = odd * RS + RI
    PV_even = even * RS + RI
    FP_odd = PV_odd / (RS * SS)
    FP_even = PV_even / (RS * SS)

    # Add up all even and odd images
    even_acc = np.zeros((xRes, yRes, NSlices, NPhases))
    odd_acc = np.zeros((xRes, yRes, NSlices, NPhases))

    for x in range(xRes):
        for y in range(yRes):
            for z in range(NSlices):
                for t in range(NDynamics//2):
                    for u in range(NPhases):
                        even_acc[x, y, z, u] += FP_even[x, y, t, 1, z, u]
                        odd_acc[x, y, z, u] += FP_odd[x, y, t, 1, z, u]


    sub = odd_acc - even_acc

    #Create progress bar 
    for x in trange(NPhases):
        datatype = np.int64
        origin = [1, 1, 1]
        if x == 1:
            MIP1 = np.max(sub[:,:,:,0], axis=2)
            origin = [4, 4, 4]
            nii = make_nii(MIP1, None, origin, datatype)
            save_nii(nii,'MIP1.nii')
        if x == 2:
            MIP2 = np.max(sub[:,:,:,1], axis=2)
            nii = make_nii(MIP2, None, origin, datatype)
            save_nii(nii,'MIP2.nii')
        if x == 3:
            MIP3 = np.max(sub[:,:,:,2], axis=2)
            nii = make_nii(MIP3, None, origin, datatype)
            save_nii(nii,'MIP3.nii')
        if x == 4:
            MIP4 = np.max(sub[:,:,:,3], axis=2)
            nii = make_nii(MIP4, None, origin, datatype)
            save_nii(nii,'MIP4.nii')
        if x == 5:
            MIP5 = np.max(sub[:,:,:,4], axis=2)
            nii = make_nii(MIP5, None, origin, datatype)
            save_nii(nii,'MIP5.nii')
        if x == 6:
            MIP6 = np.max(sub[:,:,:,5], axis=2)
            nii = make_nii(MIP6, None, origin, datatype)
            save_nii(nii,'MIP6.nii')
            
