import os

def W_Expno(root: str):
    Temp = os.listdir(root)
    Expno = [int(item) for item in Temp if item.isdigit()]
    Expno.sort(reverse=True)
    return Expno

def W_ParaWrite(dir: str, Para: dict):
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