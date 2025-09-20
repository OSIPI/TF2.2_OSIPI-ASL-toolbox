import os

def W_ImgParaAbs(path: str):
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

    acqp_path = os.path.join(path, "acqp")
    if os.path.exists(acqp_path):
        with open(acqp_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                if temp.startswith("##$ACQ_scan_name=("):
                    temp = filepath.readline().strip().split()[0]
                    Slice["Scan"] = temp[1:]
                elif temp.startswith("##$ACQ_protocol_name=("):
                    temp = filepath.readline().strip()
                    Slice["Protocol"] = temp
                elif temp.startswith("##$ACQ_fov=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["ROI"] = [float(temp[i]) for i in range(Cont)]
                elif temp.startswith("##$ACQ_slice_offset=("):
                    Slice["slicenum"] = int(temp.split()[1])
                elif temp.startswith("##$ACQ_slice_thick="):
                    Slice["thickness"] = float(temp[19:])
                elif temp.startswith("##$ACQ_repetition_time=("):
                    temp = filepath.readline().strip()
                    Slice["tr"] = round(float(temp), 2)
                elif temp.startswith("##$ACQ_echo_time=("):
                    temp = filepath.readline().strip()
                    Slice["te"] = round(float(temp), 2)
                elif temp.startswith("##$ACQ_size=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["AcqSize"] = [int(temp[i]) for i in range(Cont)]
                elif temp.startswith("##$NR="):
                    Slice["NR"] = int(temp[6:])
                line = filepath.readline()
    else:
        raise FileNotFoundError(f"{acqp_path} not found")

    method_path = os.path.join(path, "method")
    if os.path.exists(method_path):
        with open(method_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                if temp.startswith("##$TotalEchoTime=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["eTE"] = [float(temp[i]) for i in range(Cont)]
                elif temp.startswith("##$NEcho=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["EchoNum"] = [int(temp[i]) for i in range(Cont)]
                elif temp.startswith("##$PVM_ScanTimeStr=("):
                    temp = filepath.readline().strip()
                    Slice["ScanTime"] = temp[1:-1]
                elif temp.startswith("##$PostLabelTime="):
                    Slice["PostLabelTime"] = float(temp[17:])
                elif temp.startswith("##$Slab_Margin="):
                    Slice["SlabMargin"] = float(temp[15:])
                elif temp.startswith("##$NSegments"):
                    Slice["Segment"] = int(temp[13:])
                elif temp.startswith("##$FlowRange="):
                    Slice["VENC"] = float(temp[13:])
                elif temp.startswith("##$PVM_NRepetitions="):
                    Slice["rep"] = int(temp[20:])
                elif temp.startswith("##$PCASL_LabelTime="):
                    Slice["asllabel"] = float(temp[19:])
                elif temp.startswith("##$PCASL_PostLabelTime="):
                    Slice["aslPLD"] = float(temp[23:])
                elif temp.startswith("##$PCASL_PLD="):
                    Slice["aslPLD"] = float(temp[13:])
                elif temp.startswith("##$PCASL_Dur="):
                    Slice["aslLD"] = float(temp[13:])
                line = filepath.readline()
    else:
        raise FileNotFoundError(f"{method_path} not found")

    visu_path = os.path.join(path, "visu_pars")
    if os.path.exists(visu_path):
        with open(visu_path, "r") as filepath:
            line = filepath.readline()
            while line:
                temp = line.strip()
                if temp.startswith("##$VisuCoreSize=("):
                    Cont = int(temp.split()[1])
                    temp = filepath.readline().strip().split()
                    Slice["size"] = [int(temp[i]) for i in range(Cont)]
                elif temp.startswith("##$VisuCoreUnits=("):
                    Cont = int(temp.split()[1][:-1])
                    temp = filepath.readline().strip().split()
                    Slice["Unit"] = [temp[i] for i in range(Cont)]
                line = filepath.readline()
    else:
        raise FileNotFoundError(f"{visu_path} not found")

    return Slice