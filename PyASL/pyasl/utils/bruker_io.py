import os, struct, re
import numpy as np

def read_nmr_par(filename: str):
    # Reads BRUKER parameter files to a dictionary
    try:
        with open(filename, "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not open file: {filename}")

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
    method_file = os.path.join(fname, str(expno), "method")
    acqp_file = os.path.join(fname, str(expno), "acqp")
    reco_file = os.path.join(fname, str(expno), "pdata", "1", "reco")
    img_name = os.path.join(fname, str(expno), "pdata", str(procno), "2dseq")

    method_par = read_nmr_par(method_file)
    acqp_par = read_nmr_par(acqp_file)
    reco_par = read_nmr_par(reco_file)

    NI = int(acqp_par["NI"])
    NR = int(acqp_par["NR"])
    NSLICES = int(acqp_par["NSLICES"])

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

    type_mapping = {
        "int16": "h",
        "uint16": "H",
        "int32": "i",
        "uint32": "I",
        "float32": "f",
        "float64": "d",
    }

    try:
        with open(img_name, "rb") as bruker_recon:
            sizeD3 = NSLICES
            sizeD4 = NR
            sizeD5 = 1
            img = np.zeros([Nrows, Ncolumns, sizeD3, sizeD4, sizeD5], dtype=np.dtype(f"{BIT}"))
            for ii in range(sizeD5):
                for jj in range(sizeD4):
                    for kk in range(sizeD3):
                        num_elements = Nrows * Ncolumns
                        BIT_sign = type_mapping[BIT]
                        struct_format = f"{BYTEORDER}{num_elements}{BIT_sign}"
                        data_size = struct.calcsize(struct_format)
                        data = bruker_recon.read(data_size)
                        unpacked_data = struct.unpack(struct_format, data)
                        img[:, :, kk, jj, ii] = np.array(unpacked_data).reshape(Nrows, Ncolumns)
    except FileNotFoundError:
        raise FileNotFoundError("Could not open 2dseq file")

    img = img / RECOMAPSLOPE + RECOMAPOFFSET
    img = np.transpose(img, (1, 0, 2, 3, 4))
    return img, Ncolumns, Nrows, NI, NR, RecoNumInputChan