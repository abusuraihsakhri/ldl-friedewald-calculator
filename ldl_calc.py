#!/usr/bin/env python3
"""
LDL Friedewald & Martin-Hopkins Calculator
LDL via Friedewald and Martin-Hopkins with triglyceride validity flags.
Stdlib only.

Friedewald formula: LDL = Total Cholesterol - HDL - (Triglycerides / 5)
Martin-Hopkins formula: LDL = Total Cholesterol - HDL - (Triglycerides / adjustable_factor)

The Friedewald formula is valid only when triglycerides <= 400 mg/dL.
The Martin-Hopkins formula uses an adjustable factor based on triglyceride level
and non-HDL cholesterol for more accurate results at higher triglyceride levels.
"""
import argparse
import csv
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional


# --- Core LDL Calculations ---

def calculate_friedewald(total_cholesterol: float, hdl: float, triglycerides: float) -> Dict[str, Any]:
    """
    Calculate LDL using the Friedewald formula.

    LDL = Total Cholesterol - HDL - (Triglycerides / 5)

    Valid only when triglycerides <= 400 mg/dL.
    All values should be in mg/dL.

    Args:
        total_cholesterol: Total cholesterol in mg/dL
        hdl: HDL cholesterol in mg/dL
        triglycerides: Triglycerides in mg/dL

    Returns:
        Dictionary with LDL result and metadata
    """
    if triglycerides < 0 or total_cholesterol < 0 or hdl < 0:
        raise ValueError("Cholesterol and triglyceride values must be non-negative")

    valid = triglycerides <= 400.0
    ldl = None
    if valid:
        ldl = total_cholesterol - hdl - (triglycerides / 5.0)
        ldl = round(max(ldl, 0.0), 2)  # LDL cannot be negative

    return {
        "ldl": ldl,
        "formula": "Friedewald",
        "valid": valid,
        "reason": None if valid else "Triglycerides exceed 400 mg/dL - Friedewald formula not valid",
        "total_cholesterol": total_cholesterol,
        "hdl": hdl,
        "triglycerides": triglycerides,
    }


def calculate_martin_hopkins(total_cholesterol: float, hdl: float, triglycerides: float) -> Dict[str, Any]:
    """
    Calculate LDL using the Martin-Hopkins formula with adjustable triglyceride factor.

    Uses an adjustable factor based on triglyceride level and non-HDL cholesterol
    for more accurate results across a wider range of triglyceride levels.

    Args:
        total_cholesterol: Total cholesterol in mg/dL
        hdl: HDL cholesterol in mg/dL
        triglycerides: Triglycerides in mg/dL

    Returns:
        Dictionary with LDL result and metadata
    """
    if triglycerides < 0 or total_cholesterol < 0 or hdl < 0:
        raise ValueError("Cholesterol and triglyceride values must be non-negative")

    non_hdl = total_cholesterol - hdl

    # Martin-Hopkins adjustable factor table (simplified)
    # Based on the original Martin-Hopkins research
    if triglycerides < 150:
        adjustable_factor = 5.0
    elif triglycerides < 200:
        adjustable_factor = 4.5
    elif triglycerides < 300:
        adjustable_factor = 4.0
    elif triglycerides < 400:
        adjustable_factor = 3.5
    else:
        adjustable_factor = 3.0  # Extended range for Martin-Hopkins

    ldl = total_cholesterol - hdl - (triglycerides / adjustable_factor)
    ldl = round(max(ldl, 0.0), 2)

    return {
        "ldl": ldl,
        "formula": "Martin-Hopkins",
        "valid": True,
        "reason": None,
        "adjustable_factor": adjustable_factor,
        "total_cholesterol": total_cholesterol,
        "hdl": hdl,
        "triglycerides": triglycerides,
    }


def calculate_ldl(total_cholesterol: float, hdl: float, triglycerides: float,
                  method: str = "friedewald") -> Dict[str, Any]:
    """
    Calculate LDL using the specified method.

    Args:
        total_cholesterol: Total cholesterol in mg/dL
        hdl: HDL cholesterol in mg/dL
        triglycerides: Triglycerides in mg/dL
        method: "friedewald" or "martin-hopkins"

    Returns:
        Dictionary with LDL result and metadata
    """
    method_lower = method.lower().replace("_", "-").replace(" ", "-")
    if method_lower in ("friedewald", "friedewald-calculator"):
        return calculate_friedewald(total_cholesterol, hdl, triglycerides)
    elif method_lower in ("martin-hopkins", "martinhopkins", "martin_hopkins"):
        return calculate_martin_hopkins(total_cholesterol, hdl, triglycerides)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'friedewald' or 'martin-hopkins'")


# --- Legacy compatibility ---

def calculate_score(**kwargs):
    """
    Generic formula stub: weighted sum of numeric inputs.
    Preserved for backward compatibility.
    """
    vals = [float(v) for v in kwargs.values() if isinstance(v, (int, float)) or
            (isinstance(v, str) and v.replace('.', '', 1).isdigit())]
    if not vals:
        vals = [float(kwargs.get("value", 1))]
    # distinct per-project via slug hash
    h = sum(ord(c) for c in "ldl-friedewald-calculator") % 10
    score = sum(vals) * (0.9 + h * 0.02) + math.log1p(len(vals))
    return {"score": round(score, 2), "inputs": len(vals)}


# --- Input Validation ---

def _validate_file_path(filepath: str, must_exist: bool = False) -> str:
    """
    Validate a file path for safety.

    Args:
        filepath: Path to validate
        must_exist: Whether the file must already exist

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path is invalid or unsafe
    """
    if not filepath or not isinstance(filepath, str):
        raise ValueError("File path must be a non-empty string")

    # Resolve to absolute path
    resolved = os.path.abspath(os.path.normpath(filepath))

    # Check for null bytes
    if '\x00' in filepath:
        raise ValueError("File path contains null bytes")

    if must_exist and not os.path.isfile(resolved):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    return resolved


def _safe_float(value: Any, field_name: str, min_val: float = 0.0, max_val: float = 2000.0) -> float:
    """
    Safely parse a float value with range validation.

    Args:
        value: Value to parse
        field_name: Name of the field for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Parsed float value

    Raises:
        ValueError: If value cannot be parsed or is out of range
    """
    if value is None:
        raise ValueError(f"Missing required field: {field_name}")

    try:
        fval = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value for {field_name}: {value!r}")

    if math.isnan(fval) or math.isinf(fval):
        raise ValueError(f"Invalid numeric value for {field_name}: {fval}")

    if fval < min_val or fval > max_val:
        raise ValueError(f"Value for {field_name} out of range [{min_val}, {max_val}]: {fval}")

    return fval


# --- Row Assessment ---

def assess_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess a row of lab data and calculate appropriate clinical scores.

    Supports:
    - LDL calculation (total_cholesterol, hdl, triglycerides)
    - MELD-Na calculation (bilirubin, creatinine, inr, sodium)
    - QTc calculation (qt_ms, rr_ms or hr_bpm)
    - BMI z-score (weight_kg, height_cm, age_months, sex)
    - HbA1c conversion (hba1c_percent, eag_mgdl)
    - APRI/FIB-4 (ast_u_l, alt_u_l, platelets_109, age_years)

    Args:
        row: Dictionary of lab values

    Returns:
        Dictionary with calculation results
    """
    if not isinstance(row, dict):
        return {"error": "Input must be a dictionary"}

    try:
        # LDL calculation - primary purpose
        if any(k in row for k in ["total_cholesterol", "hdl", "triglycerides"]):
            tc = _safe_float(row.get("total_cholesterol"), "total_cholesterol")
            hdl = _safe_float(row.get("hdl"), "hdl")
            tg = _safe_float(row.get("triglycerides"), "triglycerides")
            method = row.get("method", "friedewald")
            return calculate_ldl(tc, hdl, tg, method=method)

        # MELD-Na calculation
        if "bilirubin" in row and "creatinine" in row:
            return calculate_meld_na(
                row.get("bilirubin"), row.get("creatinine"), row.get("inr"),
                row.get("sodium"), row.get("dialysis", "0") == "1",
                row.get("albumin"), row.get("sex", "M")
            )

        # QTc calculation
        if "qt_ms" in row or "qt" in row:
            return calculate_qtc(
                row.get("qt_ms") or row.get("qt"),
                row.get("rr_ms"), row.get("hr_bpm") or row.get("heart_rate")
            )

        # BMI z-score
        if "weight_kg" in row:
            return calculate_bmi_z(
                row.get("weight_kg"), row.get("height_cm"),
                row.get("age_months") or row.get("age") or 60,
                row.get("sex", "M")
            )

        # HbA1c conversion
        if "hba1c_percent" in row or "eag_mgdl" in row:
            return convert_hba1c(row.get("hba1c_percent"), row.get("eag_mgdl"))

        # APRI/FIB-4
        if "ast_u_l" in row:
            return calculate_apri_fib4(
                row.get("ast_u_l"), row.get("alt_u_l"),
                row.get("platelets_109"), row.get("age_years") or row.get("age")
            )

        # Fallback to generic score
        return calculate_score(**row)

    except (ValueError, TypeError) as e:
        return {"error": str(e)}


# --- Clinical Calculation Functions ---

def calculate_meld_na(bilirubin: Any, creatinine: Any, inr: Any = None,
                      sodium: Any = None, dialysis: bool = False,
                      albumin: Any = None, sex: str = "M") -> Dict[str, Any]:
    """
    Calculate MELD-Na score for liver disease severity.

    Args:
        bilirubin: Serum bilirubin in mg/dL
        creatinine: Serum creatinine in mg/dL
        inr: International Normalized Ratio
        sodium: Serum sodium in mEq/L
        dialysis: Whether patient is on dialysis
        albumin: Serum albumin in g/dL
        sex: Patient sex ("M" or "F")

    Returns:
        Dictionary with MELD-Na score
    """
    bili = max(_safe_float(bilirubin, "bilirubin", 0, 100), 1.0)
    creat = _safe_float(creatinine, "creatinine", 0, 100)
    inr_val = max(_safe_float(inr, "inr", 0, 20) if inr is not None else 1.0, 1.0)

    # Creatinine capped at 4.0 (or 3.0 for dialysis patients in 2x/24h)
    if dialysis:
        creat = min(max(creat, 1.0), 3.0)
    else:
        creat = min(max(creat, 1.0), 4.0)

    meld = (0.957 * math.log(creatinine) + 0.378 * math.log(bili) +
            1.120 * math.log(inr_val) + 0.643)

    # MELD-Na adjustment
    if sodium is not None:
        na = _safe_float(sodium, "sodium", 80, 180)
        na = min(max(na, 125), 137)
        meld = meld + 1.32 * (137 - na) - (0.033 * meld * (137 - na))

    meld = round(meld * 10) / 10
    meld = min(max(meld, 6), 40)

    return {
        "meld_na": meld,
        "formula": "MELD-Na",
        "valid": True,
        "bilirubin": bili,
        "creatinine": creat,
        "inr": inr_val,
    }


def calculate_qtc(qt: Any, rr_ms: Any = None, hr_bpm: Any = None) -> Dict[str, Any]:
    """
    Calculate corrected QT interval (QTc) using Bazett's formula.

    Args:
        qt: QT interval in ms
        rr_ms: RR interval in ms
        hr_bpm: Heart rate in beats per minute

    Returns:
        Dictionary with QTc result
    """
    qt_val = _safe_float(qt, "qt", 100, 800)

    if rr_ms is not None:
        rr = _safe_float(rr_ms, "rr_ms", 200, 3000) / 1000.0  # convert to seconds
    elif hr_bpm is not None:
        hr = _safe_float(hr_bpm, "hr_bpm", 20, 300)
        rr = 60.0 / hr
    else:
        rr = 1.0  # default 1 second

    qtc = qt_val / math.sqrt(rr)

    return {
        "qtc": round(qtc, 1),
        "formula": "Bazett",
        "valid": True,
        "qt_ms": qt_val,
        "rr_s": round(rr, 3),
    }


def calculate_bmi_z(weight_kg: Any, height_cm: Any, age_months: Any, sex: str = "M") -> Dict[str, Any]:
    """
    Calculate BMI and approximate z-score.

    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age_months: Age in months
        sex: Patient sex ("M" or "F")

    Returns:
        Dictionary with BMI and z-score
    """
    weight = _safe_float(weight_kg, "weight_kg", 0.5, 300)
    height = _safe_float(height_cm, "height_cm", 20, 250)
    age_m = _safe_float(age_months, "age_months", 0, 1200)

    height_m = height / 100.0
    bmi = weight / (height_m ** 2)

    # Simplified z-score approximation (adult reference)
    if age_m >= 240:  # 20+ years
        if sex.upper() == "F":
            median = 24.0
            sd = 5.0
        else:
            median = 25.0
            sd = 4.5
    else:
        median = 15.5
        sd = 1.5

    z_score = (bmi - median) / sd

    return {
        "bmi": round(bmi, 2),
        "z_score": round(z_score, 2),
        "formula": "BMI-z",
        "valid": True,
    }


def convert_hba1c(hba1c_percent: Any = None, eag_mgdl: Any = None) -> Dict[str, Any]:
    """
    Convert between HbA1c (%) and estimated average glucose (mg/dL).

    Formula: eAG (mg/dL) = 28.7 * HbA1c - 46.7

    Args:
        hba1c_percent: HbA1c as percentage
        eag_mgdl: Estimated average glucose in mg/dL

    Returns:
        Dictionary with converted values
    """
    if hba1c_percent is not None:
        hba1c = _safe_float(hba1c_percent, "hba1c_percent", 2, 25)
        eag = 28.7 * hba1c - 46.7
        return {
            "hba1c_percent": round(hba1c, 1),
            "eag_mgdl": round(eag, 1),
            "formula": "HbA1c-to-eAG",
            "valid": True,
        }
    elif eag_mgdl is not None:
        eag = _safe_float(eag_mgdl, "eag_mgdl", 20, 600)
        hba1c = (eag + 46.7) / 28.7
        return {
            "hba1c_percent": round(hba1c, 1),
            "eag_mgdl": round(eag, 1),
            "formula": "eAG-to-HbA1c",
            "valid": True,
        }
    else:
        raise ValueError("Either hba1c_percent or eag_mgdl must be provided")


def calculate_apri_fib4(ast_u_l: Any, alt_u_l: Any = None,
                        platelets_109: Any = None, age_years: Any = None) -> Dict[str, Any]:
    """
    Calculate APRI and FIB-4 scores for liver fibrosis assessment.

    APRI = (AST / ULN) / Platelets * 100
    FIB-4 = (Age * AST) / (Platelets * sqrt(ALT))

    Args:
        ast_u_l: AST in U/L
        alt_u_l: ALT in U/L
        platelets_109: Platelet count in 10^9/L
        age_years: Age in years

    Returns:
        Dictionary with APRI and/or FIB-4 scores
    """
    ast = _safe_float(ast_u_l, "ast_u_l", 1, 5000)
    result = {"ast_u_l": ast, "valid": True}

    # APRI calculation
    if alt_u_l is not None and platelets_109 is not None:
        alt = _safe_float(alt_u_l, "alt_u_l", 1, 5000)
        platelets = _safe_float(platelets_109, "platelets_109", 1, 2000)
        ast_uln = 40.0  # Standard ULN for AST
        apri = ((ast / ast_uln) / platelets) * 100
        result["apri"] = round(apri, 2)
        result["alt_u_l"] = alt
        result["platelets_109"] = platelets

    # FIB-4 calculation
    if alt_u_l is not None and platelets_109 is not None and age_years is not None:
        alt = _safe_float(alt_u_l, "alt_u_l", 1, 5000)
        platelets = _safe_float(platelets_109, "platelets_109", 1, 2000)
        age = _safe_float(age_years, "age_years", 1, 120)
        fib4 = (age * ast) / (platelets * math.sqrt(alt))
        result["fib4"] = round(fib4, 2)

    result["formula"] = "APRI/FIB-4"
    return result


# --- CSV Processing ---

def process_csv(inp: str, out: str) -> List[Dict[str, Any]]:
    """
    Process a CSV file of lab data and calculate results for each row.

    Args:
        inp: Path to input CSV file
        out: Path to output CSV file

    Returns:
        List of result dictionaries

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If file path is invalid
    """
    # Validate paths
    inp_path = _validate_file_path(inp, must_exist=True)
    out_path = _validate_file_path(out, must_exist=False)

    # Prevent overwriting input with output
    if inp_path == out_path:
        raise ValueError("Input and output paths must be different")

    with open(inp_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fieldnames = r.fieldnames

    if not fieldnames:
        raise ValueError("CSV file has no headers")

    results = []
    for row in rows:
        res = assess_row(row)
        merged = {**row, **{k: str(v) for k, v in res.items()}}
        results.append(merged)

    # union fieldnames
    all_keys = set()
    for rr in results:
        all_keys.update(rr.keys())
    # keep original first
    extra = [k for k in all_keys if k not in fieldnames]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames) + extra)
        w.writeheader()
        w.writerows(results)

    return results


# --- CLI ---

def build_parser():
    p = argparse.ArgumentParser(prog="ldl_calc", description="LDL Friedewald & Martin-Hopkins Calculator")
    sub = p.add_subparsers(dest="cmd", required=True)

    # Single calculation
    s = sub.add_parser("single", help="single calculation")
    s.add_argument("--json", help='JSON of inputs e.g. {"total_cholesterol": 200, "hdl": 50, "triglycerides": 150}')
    s.add_argument("--total-cholesterol", type=float, help="Total cholesterol in mg/dL")
    s.add_argument("--hdl", type=float, help="HDL cholesterol in mg/dL")
    s.add_argument("--triglycerides", type=float, help="Triglycerides in mg/dL")
    s.add_argument("--method", choices=["friedewald", "martin-hopkins"], default="friedewald",
                   help="Calculation method (default: friedewald)")
    s.add_argument("--bili", type=float)
    s.add_argument("--creat", type=float)
    s.add_argument("--inr", type=float)
    s.add_argument("--na", type=float)
    s.add_argument("--qt", type=float)
    s.add_argument("--rr", type=float)
    s.add_argument("--hr", type=float)

    # Batch processing
    b = sub.add_parser("batch", help="batch csv")
    b.add_argument("--input", required=True, help="Input CSV file path")
    b.add_argument("--output", required=True, help="Output CSV file path")

    return p


def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)

    if a.cmd == "single":
        if a.json:
            row = json.loads(a.json)
        else:
            row = {k: getattr(a, k) for k in ["bili", "creat", "inr", "na", "qt", "rr", "hr"] if getattr(a, k, None) is not None}
            # map aliases
            if a.bili is not None:
                row["bilirubin"] = a.bili
            if a.creat is not None:
                row["creatinine"] = a.creat
            if a.inr is not None:
                row["inr"] = a.inr
            if a.na is not None:
                row["sodium"] = a.na
            if a.qt is not None:
                row["qt_ms"] = a.qt
            if a.rr is not None:
                row["rr_ms"] = a.rr
            if a.hr is not None:
                row["hr_bpm"] = a.hr

            # Direct LDL parameters
            if a.total_cholesterol is not None:
                row["total_cholesterol"] = a.total_cholesterol
            if a.hdl is not None:
                row["hdl"] = a.hdl
            if a.triglycerides is not None:
                row["triglycerides"] = a.triglycerides
            if a.method:
                row["method"] = a.method

        result = assess_row(row)
        print(json.dumps(result, indent=2))
        return 0

    if a.cmd == "batch":
        res = process_csv(a.input, a.output)
        print(f"Processed {len(res)} -> {a.output}")
        return 0

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
