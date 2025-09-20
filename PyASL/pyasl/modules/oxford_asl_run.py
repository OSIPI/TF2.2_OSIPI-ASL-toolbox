"""
OxfordASLRun
------------
Run Oxford ASL pipeline.
"""
import os, subprocess
from typing import List, Tuple, Optional
import logging
logger = logging.getLogger(__name__)

def _first_images_entry(dd):
    """
    Return the (base_dir, entry) tuple for the first subject in the Images dict.

    Args:
        dd (dict): Data description dictionary containing an "Images" key.

    Returns:
        tuple: (base_dir, entry) where base_dir is the key and entry is the value from dd["Images"].
        
    Raises:
        ValueError: If dd["Images"] is empty, missing, or malformed.
    """
    if "Images" not in dd or not isinstance(dd["Images"], dict) or not dd["Images"]:
        raise ValueError("data_descrip['Images'] is empty or malformed.")
    base = next(iter(dd["Images"].keys()))
    entry = dd["Images"][base]
    return base, entry

def _guess_path(base_dir, subdir, name):
    """
    Attempt to find a file by trying different extensions if the exact path doesn't exist.
    
    This function first tries the exact path, then appends common NIfTI extensions
    (.nii.gz, .nii, .NII.GZ, .NII) if the file doesn't exist.
    
    Args:
        base_dir (str): Base directory path.
        subdir (str): Subdirectory within base_dir.
        name (str): Filename to search for.
        
    Returns:
        str: The found file path, or the original path if no variants exist.
    """
    p = os.path.join(base_dir, subdir, name)
    if os.path.exists(p): return p
    for ext in (".nii.gz", ".nii", ".NII.GZ", ".NII"):
        q = p + ext
        if os.path.exists(q): return q
    return p

def _plds_seq(dd):
    """
    Extract non-zero post-labeling delays from the data description.
    
    Args:
        dd (dict): Data description dictionary.
        
    Returns:
        list: List of non-zero PLD values from dd["PLDList"], or empty list if not present.
    """
    return [pld for pld in dd.get("PLDList", []) if pld != 0]

def _collapse_equal(vals: List[float], tol: float = 1e-6) -> List[float]:
    """
    Remove consecutive duplicate values and return unique values within tolerance.
    
    This function performs two operations:
    1. Removes consecutive values that are equal within tolerance
    2. Returns only unique values (no duplicates anywhere in the list)
    
    Args:
        vals (List[float]): Input list of float values.
        tol (float, optional): Tolerance for equality comparison. Defaults to 1e-6.
        
    Returns:
        List[float]: List of unique values with consecutive duplicates removed.
    """
    out: List[float] = []
    for v in vals:
        if not out or abs(v - out[-1]) > tol:
            out.append(v)
    uniq: List[float] = []
    for v in out:
        if not any(abs(v - u) <= tol for u in uniq):
            uniq.append(v)
    return uniq

def _compute_tis_bolus(dd) -> Tuple[List[float], float, bool]:
    """
    Compute inversion times, bolus duration, and ASL type from data description.
    
    Args:
        dd (dict): Data description dictionary containing ASL parameters.
        
    Returns:
        Tuple[List[float], float, bool]: A tuple containing:
            - tis: List of inversion times (PLD + bolus duration)
            - bolus: Bolus duration value
            - is_casl: True if CASL/PCASL, False if PASL
            
    Raises:
        ValueError: If ArterialSpinLabelingType is not supported (not CASL, PCASL, or PASL).
    """
    typ = dd["ArterialSpinLabelingType"]
    if typ in ("CASL", "PCASL"):
        bolus = float(dd["LabelingDuration"])
        tis_raw = [float(pld) + bolus for pld in _plds_seq(dd)]
        tis = _collapse_equal(tis_raw) if tis_raw else []
        return tis, bolus, True
    elif typ == "PASL":
        bolus = float(dd["BolusCutOffDelayTime"])
        tis_raw = [float(pld) + bolus for pld in _plds_seq(dd)]
        tis = _collapse_equal(tis_raw) if tis_raw else []
        return tis, bolus, False
    raise ValueError(f"Unsupported ASL type: {typ}")

class OxfordASLRun:
    """
    Class for running Oxford ASL pipeline with various configuration options.
    
    This class constructs and executes oxford_asl commands based on data description
    dictionaries and parameter configurations. It handles input/output paths,
    structural data, calibration, and various ASL-specific parameters.
    """
    
    def _base_args(self, dd, params):
        """
        Construct base oxford_asl command line arguments.
        
        Args:
            dd (dict): Data description dictionary.
            params (dict): Parameters dictionary with processing options.
            
        Returns:
            list: List of command line arguments for oxford_asl.
        """
        args = ["oxford_asl"]
        if params.get("wp"): args += ["--wp"]
        if params.get("mc"): args += ["--mc"]

        # iaf
        iaf = "tc" if dd["LabelControl"] else "ct"
        args += ["--iaf", iaf]

        ibf = params.get("ibf")
        if iaf in ("ct", "tc"):
            args += ["--ibf", ibf if ibf else "rpt"]

        # TIs / bolus / casl|pasl
        tis, bolus, is_casl = _compute_tis_bolus(dd)
        if is_casl:
            args += ["--casl"]
        if tis:
            args += ["--tis", ",".join(map(lambda x: f"{float(x):g}", tis))]
        args += ["--bolus", f"{float(bolus):g}"]

        if "SliceDuration" in dd:
            args += ["--slicedt", str(dd["SliceDuration"])]

        for k in ("bat", "t1", "t1b", "sliceband"):
            if params.get(k) is not None:
                args += [f"--{k}", str(params[k])]

        if params.get("inferart"):
            args += ["--inferart"]

        if params.get("debug"):
            args += ["--debug"]

        return args

    def _struct_args(self, dd, params):
        """
        Construct structural data arguments for oxford_asl.
        
        Args:
            dd (dict): Data description dictionary.
            params (dict): Parameters dictionary with useStructural flag.
            
        Returns:
            list: List of structural arguments, or empty list if not using structural data.
            
        Raises:
            ValueError: If useStructural=True but anatomical data is missing.
        """
        if not params.get("useStructural", False): return []
        base_dir, entry = _first_images_entry(dd)
        anat_name = entry.get("anat")
        if not anat_name:
            raise ValueError("useStructural=True but 'anat' missing in data_descrip['Images'][base].")
        anat_path = _guess_path(base_dir, "anat", anat_name)
        return ["-s", anat_path]

    def _input_args(self, dd, params):
        """
        Construct input file arguments for oxford_asl.
        
        Args:
            dd (dict): Data description dictionary.
            params (dict): Parameters dictionary with input options.
            
        Returns:
            list: List of input arguments including ASL data and optional calibration.
            
        Raises:
            ValueError: If useCalibration=True but M0 data is missing.
        """
        args = []
        ov = params.get("override_inputs") or {}
        use_cal = bool(params.get("useCalibration", False))

        if ov.get("asl_path"):
            args += ["-i", ov["asl_path"]]
        else:
            base_dir, entry = _first_images_entry(dd)
            asl_name = entry["asl"][0]
            asl_path = _guess_path(base_dir, "perf", asl_name)
            args += ["-i", asl_path]

        if use_cal:
            if ov.get("m0_path"):
                base_dd = dd
                args += ["-c", ov["m0_path"],
                         "--tr",   str(base_dd["M0"]["RepetitionTime"]),
                         "--alpha",str(base_dd["LabelingEfficiency"])]
            else:
                base_dir, entry = _first_images_entry(dd)
                m0_name = entry.get("M0")
                if not m0_name:
                    raise ValueError("useCalibration=True but M0 missing in data_descrip.")
                m0_path = _guess_path(base_dir, "perf", m0_name)
                args += ["-c", m0_path,
                         "--tr",   str(dd["M0"]["RepetitionTime"]),
                         "--alpha",str(dd["LabelingEfficiency"])]
        return args

    def _output_args(self, dd, params):
        """
        Construct output directory arguments for oxford_asl.
        
        Args:
            dd (dict): Data description dictionary.
            params (dict): Parameters dictionary with optional outdir.
            
        Returns:
            tuple: (output_args, outdir) where output_args is a list of arguments
                   and outdir is the output directory path.
        """
        base_dir, _ = _first_images_entry(dd)
        outdir = params.get("outdir", base_dir.replace("rawdata", "derivatives"))
        os.makedirs(outdir, exist_ok=True)
        return ["-o", outdir], outdir

    def _run_cli(self, cmd, env=None):
        """
        Execute oxford_asl command with appropriate environment variables.
        
        Sets up FSL and system environment variables for consistent execution,
        including output format, threading, and locale settings.
        
        Args:
            cmd (list): Command line arguments to execute.
            env (dict, optional): Additional environment variables to set.
            
        Raises:
            subprocess.CalledProcessError: If the oxford_asl command fails.
        """
        e = os.environ.copy()
        if env: e.update(env)

        e.setdefault("NO_COLOR", "1")
        e.setdefault("CLICOLOR", "0")
        e.setdefault("CLICOLOR_FORCE", "0")
        e.setdefault("TERM", "dumb")
        e.setdefault("LC_ALL", "C")
        e.setdefault("LANG", "C")

        e.setdefault("FSLOUTPUTTYPE", "NIFTI_GZ")
        e.setdefault("OMP_NUM_THREADS", "1")

        tmpdir = e.get("TMPDIR") or os.path.expanduser("~/tmp_oxasl")
        os.makedirs(tmpdir, exist_ok=True)
        e["TMPDIR"] = tmpdir

        print("[oxford_asl]", " ".join(cmd))
        subprocess.run(cmd, check=True, env=e)

    def run(self, data_descrip: dict, params: dict):
        """
        Run the complete Oxford ASL pipeline.
        
        This is the main entry point that combines all argument construction
        and executes the oxford_asl command with the specified configuration.
        
        Args:
            data_descrip (dict): Data description dictionary containing ASL parameters,
                                file paths, and acquisition details.
            params (dict): Processing parameters dictionary with options like:
                          - wp: White paper mode
                          - mc: Motion correction
                          - useStructural: Use structural data
                          - useCalibration: Use M0 calibration
                          - outdir: Output directory path
                          - debug: Enable debug mode
                          - Various ASL parameters (bat, t1, t1b, etc.)
                          
        Returns:
            dict: Dictionary containing the output directory path under "oxford_asl_out" key.
        """
        logger.info("OxfordASL: Run oxford_asl...")
        base = self._base_args(data_descrip, params)
        s    = self._struct_args(data_descrip, params)
        i    = self._input_args(data_descrip, params)
        o, outdir = self._output_args(data_descrip, params)
        cmd  = [*base, *s, *i, *o]
        self._run_cli(cmd, env=params.get("env"))
        return {"oxford_asl_out": outdir}
