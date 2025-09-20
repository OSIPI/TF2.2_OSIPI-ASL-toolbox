"""
MRICloudT1ROICBFAverage
-----------------------
Calculate average CBF values within T1-based ROIs using MRICloud pipeline logic.
"""

import os
import re
import numpy as np
import nibabel as nib
from pyasl.utils.utils import load_img
from pyasl.utils.mricloud_helpers import (
    mricloud_read_roi_lookup_table,
    mricloud_read_roi_lists_info,
)
import logging
logger = logging.getLogger(__name__)

class MRICloudT1ROICBFAverage:
    """
    MRICloudT1ROICBFAverage
    -----------------------
    Calculate average CBF values within T1-based ROIs using MRICloud pipeline logic.
    """
    def run(self, data_descrip: dict, params: dict):
        """
        Calculate ROI average CBF values using the structural T1 segmentation.
        """
        logger.info("MRICloud: Calculate ROI average CBF...")

        for key, value in data_descrip["Images"].items():
            key = key.replace("rawdata", "derivatives")

            # Lookup table for ROI labels
            roi_lookup_file = os.path.join(
                key, "anat", value["mpr_folder"], "multilevel_lookup_table.txt"
            )
            roi_lookup_all = mricloud_read_roi_lookup_table(roi_lookup_file)
            label_num = len(roi_lookup_all)

            # Locate ROI stats file
            regex = re.compile(rf'^{value["mpr_name"]}.*{label_num}.*MNI_stats\.txt$')
            files = [
                f
                for f in os.listdir(os.path.join(key, "anat", value["mpr_folder"]))
                if re.match(regex, f)
            ]
            roi_stats_file = files[0]

            # ROI types and mapping
            roitypes = ["Type1-L2", "Type1-L3", "Type1-L5"]
            roi_lookup_tbl = [4, 3, 1]
            roi_lists_info = mricloud_read_roi_lists_info(
                os.path.join(key, "anat", value["mpr_folder"], roi_stats_file),
                roitypes,
            )
            roi_lists_info[2]["count"] = label_num
            roi_lists_info[2]["list"] = roi_lookup_all

            # Load ROI mask file
            regex = re.compile(rf'^{value["mpr_name"]}.*{label_num}.*(?<!MNI)\.img$')
            files = [
                f
                for f in os.listdir(os.path.join(key, "anat", value["mpr_folder"]))
                if re.match(regex, f)
            ]
            roimaskfile = files[0]
            V0, mskv = load_img(os.path.join(key, "anat", value["mpr_folder"], roimaskfile))

            # Process each ASL file
            for asl_file in value["asl"]:
                V1, acbf = load_img(os.path.join(key, "perf", f"{asl_file}_aCBF_mpr.nii"))
                V2, rcbf = load_img(os.path.join(key, "perf", f"{asl_file}_rCBF_mpr.nii"))
                V3, msk1 = load_img(os.path.join(key, "perf", "brnmsk_clcu_mpr.nii"))

                fresult = os.path.join(key, "perf", f"{asl_file}_CBF_T1segmented_ROIs.txt")
                with open(fresult, "w") as fid:
                    coltitle = "ROI analysis by {} major tissue types\n"
                    colnames = (
                        "Index\tMask_name\tRegional_CBF(ml/100g/min)\tRegional_relative_CBF\tNumber_of_voxels\n"
                    )

                    # Process hierarchical ROI levels (Type1-L2, L3, L5)
                    for tt in range(len(roi_lists_info) - 1):
                        roi_tbl = roi_lookup_tbl[tt]
                        roi_lst = roi_lists_info[tt]["list"]
                        seg_num = roi_lists_info[tt]["count"]
                        segmask = np.zeros_like(mskv)

                        for ii in range(seg_num):
                            for kk in range(label_num):
                                if len(roi_lookup_all[kk]) <= roi_tbl:
                                    continue
                                if roi_lst[ii] == roi_lookup_all[kk][roi_tbl]:
                                    segmask[mskv == (kk + 1)] = ii + 1

                        # Save segmentation mask
                        segmask_img = nib.Nifti1Image(segmask, V0.affine, V0.header)
                        segmask_img.header["descrip"] = b"mricloud_pipeline"
                        segmask_img.header.set_data_dtype(np.int32)
                        segmask_img.to_filename(
                            os.path.join(
                                key,
                                "anat",
                                value["mpr_folder"],
                                f"{value['mpr_name']}_{seg_num}_segments.nii",
                            )
                        )

                        fid.write(coltitle.format(seg_num))
                        fid.write(colnames)
                        for ii in range(seg_num):
                            idxvox_seg = np.squeeze(segmask == (ii + 1)) & (msk1 > 0.5)
                            seg_acbf = np.mean(acbf[idxvox_seg])
                            seg_rcbf = np.mean(rcbf[idxvox_seg])
                            seg_nvox = np.sum(idxvox_seg)
                            seg_name = roi_lst[ii]
                            fid.write(
                                f"{ii+1}\t{seg_name}\t{seg_acbf:.2f}\t{seg_rcbf:.2f}\t{seg_nvox}\n"
                            )
                        fid.write("\n\n")

                    # Process all ROIs (full list)
                    fid.write(coltitle.format(label_num))
                    fid.write(colnames)
                    for ii in range(label_num):
                        idxvox_seg = np.squeeze(mskv == (ii + 1)) & (msk1 > 0.5)
                        seg_acbf = np.mean(acbf[idxvox_seg])
                        seg_rcbf = np.mean(rcbf[idxvox_seg])
                        seg_nvox = np.sum(idxvox_seg)
                        seg_name = roi_lists_info[2]["list"][ii][1]
                        fid.write(
                            f"{ii+1}\t{seg_name}\t{seg_acbf:.2f}\t{seg_rcbf:.2f}\t{seg_nvox}\n"
                        )
