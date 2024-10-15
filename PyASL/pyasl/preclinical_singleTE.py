import os
import numpy as np
import struct
import re
import scipy.io
import matplotlib.pyplot as plt
from pyasl.asl_mricloud import mricloud_inbrain


def read_nmr_par(filename: str):
    # Reads BRUKER parameter files to a dictionary
    #
    # IN: filename: Name of parameter file, e.g., 'acqus'
    # OUT: Dictionary with parameter/value pairs

    # Read file
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not open file: {filename}")

    # Define the kind of entry
    regex_patterns = [
        (r"^##\$*(.+)=\ ?\([\ \d\.]+\)(.+)", "ParVecVal"),
        (r"^##\$*(.+)=\ ?\([\ \d\.]+\)$", "ParVec"),
        (r"^##\$*(.+)=\ ?(.+)", "ParVal"),
        (r"^([^\$#].*)", "Val"),
        (r"^\$\$(.*)", "Stamp"),
        (r"^##\$*(.+)=$", "EmptyPar"),
        (r"^(.+)", "Anything"),
    ]

    type_of_row = []
    for line in lines:
        for pattern, type_name in regex_patterns:
            match = re.match(pattern, line)
            if match:
                type_of_row.append((type_name, match.groups()))
                break

    # Set up the dictionary
    p = {}
    last_parameter_name = None
    for type_name, tokens in type_of_row:
        if type_name == "ParVal":
            last_parameter_name = tokens[0]
            p[last_parameter_name] = tokens[1]
        elif type_name == "ParVec" or type_name == "EmptyPar":
            last_parameter_name = tokens[0]
            p[last_parameter_name] = []
        elif type_name == "ParVecVal":
            last_parameter_name = tokens[0]
            p[last_parameter_name] = tokens[1]
        elif type_name == "Val":
            if last_parameter_name:
                if p[last_parameter_name] == []:
                    p[last_parameter_name] = tokens[0]
                else:
                    p[last_parameter_name] += " " + tokens[0]
        elif type_name == "Stamp":
            if "Stamp" not in p:
                p["Stamp"] = tokens[0]
            else:
                p["Stamp"] += " ## " + tokens[0]

    # Convert strings to values
    for field in p:
        if isinstance(p[field], str):
            if re.match(r"^-?\d+(\.\d+)?$", p[field]):
                p[field] = float(p[field])
            elif re.match(r"^(-?\d+(\.\d+)?\s+)+-?\d+(\.\d+)?$", p[field]):
                p[field] = list(map(float, p[field].split()))

    return p


def read_2dseq_v3(fname: str, expno: int, procno: int):
    # read image data in file "2dseq" reconstructed from Bruker ParaVision 5
    # the file is in the directory <fname>/<expno>/pdata/<procno>/2dseq

    # certain acquision and reconstruction parameters are stored in the
    # following files:
    #  <fname>/<expno>/acqp:    acquisition parameter
    #  <fname>/<expno>/fid:     raw data
    #  <fname>/<expno>/method:  PVM method paramter
    #  <fname>/<expno>/pdata/<procno>/reco:  reconstruction parameter

    #   Image Size = sizeof(word)*NR*NI*RECO_size
    #       where
    #   NR: repetition time (dynamics)
    #   NI: slice number X echo number
    #   RECO_size: Nx*Ny*Nz

    #   parameters extracted from 'method': READDIRECTION
    #   parameters extracted from 'acqp':   NI, NR, NSLICES, NECHOES
    #   parameters extracted from 'reco':   RECOSIZE, WordType, ByteOrder,
    #                                       MapMode, MapOffset, MapSlope
    #   img array:  [Nrow, Ncolum, NI NR, RecoNumInputChan]

    method_file = os.path.join(fname, str(expno), "method")
    acqp_file = os.path.join(fname, str(expno), "acqp")
    reco_file = os.path.join(fname, str(expno), "pdata", "1", "reco")
    img_name = os.path.join(fname, str(expno), "pdata", str(procno), "2dseq")

    method_par = read_nmr_par(method_file)
    acqp_par = read_nmr_par(acqp_file)
    reco_par = read_nmr_par(reco_file)

    READDIRECTION = method_par["PVM_SPackArrReadOrient"]

    NI = int(acqp_par["NI"])
    NR = int(acqp_par["NR"])
    NSLICES = int(acqp_par["NSLICES"])
    NECHOES = acqp_par["NECHOES"]

    RECOSIZE = reco_par["RECO_size"]
    Nrows = int(RECOSIZE[0])
    Ncolumns = int(RECOSIZE[1])
    if len(RECOSIZE) > 2:
        NSLICES = int(RECOSIZE[2])  # for 3D sequence

    WORDTYPE = reco_par["RECO_wordtype"]
    BIT = f"int{WORDTYPE[1:3]}"
    BYTEORDER = ">" if reco_par["RECO_byte_order"] == "bigEndian" else "<"
    RECOMAPMODE = reco_par["RECO_map_mode"]
    RECOMAPOFFSET = reco_par["RECO_map_offset"][0]
    RECOMAPSLOPE = reco_par["RECO_map_slope"][0]
    RecoNumInputChan = 1
    # RecoNumInputChan=reco_par["RecoNumInputChan"]
    RecoCombineMode = "Sum"
    # RecoCombineMode=reco_par["RecoCombineMode"]

    type_mapping = {
        "int16": "h",
        "uint16": "H",
        "int32": "i",
        "uint32": "I",
        "float32": "f",
        "float64": "d",
    }

    # Read image data
    try:
        with open(img_name, "rb") as bruker_recon:
            sizeD3 = NSLICES
            sizeD4 = NR
            sizeD5 = 1
            if RecoCombineMode.lower() == "shuffleimages":
                sizeD5 = RecoNumInputChan
            sizeRecAll = [Nrows, Ncolumns, sizeD3, sizeD4, sizeD5]
            img = np.zeros(sizeRecAll, dtype=np.dtype(f"{BIT}"))

            for ii in range(sizeD5):
                for jj in range(sizeD4):
                    for kk in range(sizeD3):
                        num_elements = Nrows * Ncolumns
                        BIT_sign = type_mapping[BIT]
                        struct_format = f"{BYTEORDER}{num_elements}{BIT_sign}"
                        data_size = struct.calcsize(struct_format)
                        data = bruker_recon.read(data_size)
                        unpacked_data = struct.unpack(struct_format, data)
                        img[:, :, kk, jj, ii] = np.array(unpacked_data).reshape(
                            Nrows, Ncolumns
                        )

    except FileNotFoundError:
        raise FileNotFoundError("Could not open 2dseq file")

    img = img / RECOMAPSLOPE + RECOMAPOFFSET
    img = np.transpose(img, (1, 0, 2, 3, 4))

    return img, Ncolumns, Nrows, NI, NR, RecoNumInputChan


def W_Expno(root: str):
    """
    Automatic extracting the expno from a directory
    """
    Temp = os.listdir(root)
    Expno = []

    for item in Temp:
        if item.isdigit():
            Expno.append(int(item))

    Expno.sort(reverse=True)
    return Expno


def W_ImgParaAbs(path: str):
    """
    Abstracting imaging slice information from the BRUKER data
    """

    Slice = {
        "path": path,
        "slicenum": 0,
        "size": [],
        "thickness": 0,
        "tr": 0,
        "te": 0,
        "ROI": [],
        "Unit": [],
        "Protocol": "",
        "eTE": [],
        "EchoNum": [],
        "SlabMargin": 0,
        "PostLabelTime": 0,
        "Segment": 0,
        "Scan": "",
        "AcqSize": [],
        "NR": 0,
        "VENC": 0,
        "rep": 0,
        "asllabel": 0,
        "aslPLD": 0,
        "aslLD": 0,
    }

    # acqp
    acqp_path = os.path.join(path, "acqp")
    if os.path.exists(acqp_path):
        with open(acqp_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                # 1 for scan name
                if temp.startswith("##$ACQ_scan_name=("):
                    temp = filepath.readline().strip().split()[0]
                    Slice["Scan"] = temp[1:]
                # 2 for protocol
                elif temp.startswith("##$ACQ_protocol_name=("):
                    temp = filepath.readline().strip()
                    Slice["Protocol"] = temp
                # 3 ROI size
                elif temp.startswith("##$ACQ_fov=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["ROI"] = [float(temp[i]) for i in range(Cont)]
                # 4 Slice number
                elif temp.startswith("##$ACQ_slice_offset=("):
                    Slice["slicenum"] = int(temp.split()[1])
                # 5 Slice thickness
                elif temp.startswith("##$ACQ_slice_thick="):
                    Slice["thickness"] = float(temp[19:])
                # 6 Repetition time
                elif temp.startswith("##$ACQ_repetition_time=("):
                    temp = filepath.readline().strip()
                    Slice["tr"] = round(float(temp), 2)
                # 7 Echo time
                elif temp.startswith("##$ACQ_echo_time=("):
                    temp = filepath.readline().strip()
                    Slice["te"] = round(float(temp), 2)
                # 8 Matrix size
                elif temp.startswith("##$ACQ_size=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["AcqSize"] = [int(temp[i]) for i in range(Cont)]
                # 9 Number of repetitions
                elif temp.startswith("##$NR="):
                    Slice["NR"] = int(temp[6:])
                line = filepath.readline()

    else:
        raise FileNotFoundError(f"{acqp_path} not found")

    # method
    method_path = os.path.join(path, "method")
    if os.path.exists(method_path):
        with open(method_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                # 1 Effective echo time
                if temp.startswith("##$TotalEchoTime=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["eTE"] = [float(temp[i]) for i in range(Cont)]
                # 2 Number of echo
                elif temp.startswith("##$NEcho=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["EchoNum"] = [int(temp[i]) for i in range(Cont)]
                # 3 Experimental duration
                elif temp.startswith("##$PVM_ScanTimeStr=("):
                    temp = filepath.readline().strip()
                    Slice["ScanTime"] = temp[1:-1]
                # 4 Post labeling time
                elif temp.startswith("##$PostLabelTime="):
                    Slice["PostLabelTime"] = float(temp[17:])
                # 5 Slab margin
                elif temp.startswith("##$Slab_Margin="):
                    Slice["SlabMargin"] = float(temp[15:])
                # 6 Segments
                elif temp.startswith("##$NSegments"):
                    Slice["Segment"] = int(temp[13:])
                # 7 VENC
                elif temp.startswith("##$FlowRange="):
                    Slice["VENC"] = float(temp[13:])
                # 8 Number of repetition
                elif temp.startswith("##$PVM_NRepetitions="):
                    Slice["rep"] = int(temp[20:])
                # 9 Labeling duration
                elif temp.startswith("##$PCASL_LabelTime="):
                    Slice["asllabel"] = float(temp[19:])
                # 10 ASL PLD: Barbier's protocol
                elif temp.startswith("##$PCASL_PostLabelTime="):
                    Slice["aslPLD"] = float(temp[23:])
                # 11 ASL PLD: Wei's protocol
                elif temp.startswith("##$PCASL_PLD="):
                    Slice["aslPLD"] = float(temp[13:])
                # 12 ASL labeling duration: Wei's protocol
                elif temp.startswith("##$PCASL_Dur="):
                    Slice["aslLD"] = float(temp[13:])
                line = filepath.readline()

    else:
        raise FileNotFoundError(f"{method_path} not found")

    # visu_pars
    visu_path = os.path.join(path, "visu_pars")
    if os.path.exists(visu_path):
        with open(visu_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                # 1 Slice number
                if temp.startswith("##$VisuCoreSize=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["size"] = [int(temp[i]) for i in range(Cont)]
                # 2 for unit
                elif temp.startswith("##$VisuCoreUnits=("):
                    Cont = int(temp.split()[1][:-1])
                    temp = filepath.readline().strip().split()
                    Slice["Unit"] = [temp[i] for i in range(Cont)]

                line = filepath.readline()

    else:
        raise FileNotFoundError(f"{visu_path} not found")

    return Slice


def W_FindScan(root: str, keyword: str):
    """
    Finding the scan containing keyword
    """
    expno = W_Expno(root)
    rec = []

    for tempno in expno:
        filename = os.path.join(root, str(tempno))
        Para = W_ImgParaAbs(filename)

        if keyword in Para["Protocol"]:
            rec.append(tempno)

    return rec


def W_ParaWrite(dir: str, Para: dict):
    """
    Write dictionary parameters into a .txt file
    """
    file_path = os.path.join(dir, "Parameters.txt")
    with open(file_path, "w") as fp:
        fp.write(f"{Para['path']}\n")
        fp.write(f"{Para['Protocol']}\n")
        fp.write(f"ROI: {[round(x, 1) for x in Para['ROI']]}\n")
        fp.write(f"Thickness: {Para['thickness']}\n")
        fp.write(f"Size: {Para['size']}\n")
        fp.write(f"SliceNum: {Para['slicenum']}\n")
        fp.write(f"Unit: {Para['Unit'][0]} {Para['Unit'][1]}\n")
        fp.write(f"TR: {Para['tr']}\n")
        fp.write(f"TE: {Para['te']}\n")
        fp.write(f"eTE: {Para['eTE']}\n")
        fp.write(f"CPMG Num: {Para['EchoNum']}\n")
        fp.write(f"Post Label Time: {Para['PostLabelTime']}\n")
        fp.write(f"Slab: {Para['SlabMargin']} mm\n")
        fp.write(f"Segment: {Para['Segment']}\n")
        fp.write(f"Time: {Para['ScanTime']}\n")


def get_plot_array(data: np.ndarray, winf: list):
    scale = data.shape
    target = np.zeros((winf[0] * scale[0], winf[1] * scale[1]))
    for ni in range(scale[2]):
        pi = np.floor(ni / winf[1]).astype(int)
        qi = ni - pi * winf[1]
        target[
            pi * scale[0] : (pi + 1) * scale[0], qi * scale[1] : (qi + 1) * scale[1]
        ] = data[:, :, ni]
    return target


def plot_save_fig(data: np.ndarray, fig_title: str, fig_path: str, range=None):
    plt.figure()
    if not range:
        plt.imshow(data)
    else:
        plt.imshow(data, vmin=range[0], vmax=range[1])
    plt.title(fig_title)
    plt.colorbar()
    plt.savefig(fig_path)


def preclinical_singleTE_pipeline(
    root: str,
    keyword="asl",
    control_first=True,
    SGap=31,
    T1blood=2800,
    relCBF_vmax=10,
    mask_thres=0.2,
):
    print("Preclinical ASL: start processing...")
    # Locate the dataset
    if not os.path.exists(root):
        raise FileNotFoundError(f"Dataset path not exist: {root}")

    # Locate the pCASL scans
    pCASL_file = os.path.join(root, "pCASL.txt")
    if os.path.exists(pCASL_file):
        expno = np.loadtxt(pCASL_file, dtype=int)
        expno = np.atleast_1d(expno).tolist()
    else:
        expno = W_FindScan(root, keyword)
        if len(expno) == 0:
            raise ValueError("No pCASL scans are found!")
        np.savetxt(pCASL_file, expno, fmt="%d")

    # Choose the expno to process
    print("Select an expno to process:")
    for i, item in enumerate(expno):
        print(f"#{i + 1}: {str(item)}")
    while True:
        try:
            choice = int(input("Enter the index of your choice: "))
            if 1 <= choice <= len(expno):
                selected_expno = expno[choice - 1]
                print(f"Selected dataset: {selected_expno}")
                break
            else:
                raise ValueError("Invalid input, please enter again.")
        except ValueError:
            print("Invalid input, please enter again.")
    expno = selected_expno

    # Results folder: Results_<dataset_name>/<expno>_number
    root_parent, root_name = os.path.split(root)
    savedir_parent = os.path.join(root_parent, f"Results_{root_name}")
    if not os.path.exists(savedir_parent):
        os.makedirs(savedir_parent)
    savedir = os.path.join(savedir_parent, str(expno))
    if not os.path.exists(savedir):
        os.makedirs(savedir)
    else:
        counter = 1
        savedir = os.path.join(savedir_parent, f"{expno}_{counter}")
        while os.path.exists(savedir):
            counter += 1
            savedir = os.path.join(savedir_parent, f"{expno}_{counter}")
        os.makedirs(savedir)

    # Parameter extractions
    print("Preclinical ASL: extracting parameters...")
    filename = os.path.join(root, str(expno))
    Para = W_ImgParaAbs(filename)
    Para["expno"] = expno

    # Exporting data
    Image, NX, NY, NI, _, _ = read_2dseq_v3(root, expno, 1)
    ImageSize = Image.shape
    W_ParaWrite(filename, Para)
    W_ParaWrite(savedir, Para)
    np.save(os.path.join(savedir, "Image.npy"), Image)

    # Check potential motion artefacts
    SFF = np.floor(np.sqrt(ImageSize[2])).astype(int)
    SFF1 = np.ceil(ImageSize[2] / SFF).astype(int)
    target = get_plot_array(np.average(Image[:, :, :, :, 0], 3), [SFF, SFF1])
    plot_save_fig(target, "Motion Checking", os.path.join(savedir, "MotionCheck.png"))

    # Exclude the first few scans to ensure magnetization steady state
    ImageNew = Image[:, :, :, 2:, 0]
    if control_first:
        ImageCtr = ImageNew[:, :, :, 0::2]
        ImageLab = ImageNew[:, :, :, 1::2]
    else:
        ImageCtr = ImageNew[:, :, :, 1::2]
        ImageLab = ImageNew[:, :, :, 0::2]
    ImageDif = np.mean(ImageCtr - ImageLab, axis=3)

    np.save(os.path.join(savedir, "ImageDif.npy"), ImageDif)
    target = get_plot_array(ImageDif, [SFF, SFF1])
    plot_save_fig(target, "Difference Images", os.path.join(savedir, "ImageDif.png"))

    # Display the M0 imagesc
    print("Preclinical ASL: calculating M0...")
    M0Calib = 1 - np.exp(-Para["tr"] / 1900)
    Mat0 = np.mean(ImageCtr, axis=3) / M0Calib

    np.save(os.path.join(savedir, "M0.npy"), Mat0)
    target = get_plot_array(Mat0, [SFF, SFF1])
    plot_save_fig(target, "M0 Image", os.path.join(savedir, "M0.png"))

    # Calculate the CBF images
    print("Preclinical ASL: calculating CBF...")
    relCBF = np.abs(ImageDif) / Mat0 * 100

    # Delay-time calibration for multislice acquisitions
    if ImageSize[2] > 1:
        if Para["slicenum"] % 2 == 1:
            AdjList = np.arange(Para["slicenum"] + 1)
            AdjList = AdjList.reshape(2, -1).T.ravel()[:-1]
        else:
            AdjList = np.arange(Para["slicenum"]).reshape(2, -1).T.ravel()
        AdjList = SGap * AdjList
        AdjF = np.exp(AdjList / T1blood)
        print("Across-slice PLD correction:")
        print(AdjF)

        # Rescale the slices
        for ni in range(ImageSize[2]):
            relCBF[:, :, ni] = AdjF[ni] * relCBF[:, :, ni]

    else:
        print("Inter-slice-PLD correction not required ...")
        print("Cross-talk correction not required ...")

    # Display the perfusion map
    np.save(os.path.join(savedir, "relCBF.npy"), relCBF)
    target = get_plot_array(relCBF, [SFF, SFF1])
    plot_save_fig(
        target,
        "Relative CBF (%)",
        os.path.join(savedir, "relCBF.png"),
        [0, relCBF_vmax],
    )

    # mask CBF and M0
    brain_mask = mricloud_inbrain(np.mean(ImageCtr, axis=3), mask_thres, 2, 2)
    target = get_plot_array(relCBF * brain_mask, [SFF, SFF1])
    plot_save_fig(
        target, "Masked CBF", os.path.join(savedir, "MaskedCBF.png"), [0, relCBF_vmax]
    )
    target = get_plot_array(Mat0 * brain_mask, [SFF, SFF1])
    plot_save_fig(
        target,
        "Masked M0",
        os.path.join(savedir, "MaskedM0.png"),
        [0, relCBF_vmax * 10],
    )

    aslave = np.sum(relCBF * brain_mask) / np.sum(brain_mask)
    print(f"The averaged ASL signal is: {aslave}%")

    with open(os.path.join(savedir, "config.txt"), "w") as f:
        f.write(
            f"preclinical_singleTE_pipeline(root='{root}', keyword='{keyword}', control_first={control_first}, SGap={SGap}, T1blood={T1blood}, relCBF_vmax={relCBF_vmax}, mask_thres={mask_thres})"
        )

    print("Processing complete!")
    print(f"Please see results under {savedir}.")
