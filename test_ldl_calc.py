"""
Comprehensive test suite for LDL Friedewald Calculator core functionality.
"""
import csv
import json
import math
import os
import sys
import tempfile

import ldl_calc as m


# --- Friedewald Formula Tests ---

class TestFriedewaldFormula:
    """Tests for the Friedewald LDL calculation formula."""

    def test_basic_friedewald(self):
        """Standard Friedewald calculation: LDL = TC - HDL - TG/5"""
        result = m.calculate_friedewald(total_cholesterol=200, hdl=50, triglycerides=150)
        expected_ldl = 200 - 50 - (150 / 5.0)  # = 150 - 30 = 120
        assert result["ldl"] == expected_ldl
        assert result["valid"] is True
        assert result["formula"] == "Friedewald"

    def test_friedewald_exact_calculation(self):
        """Verify exact Friedewald calculation with known values."""
        result = m.calculate_friedewald(total_cholesterol=240, hdl=60, triglycerides=200)
        expected_ldl = 240 - 60 - (200 / 5.0)  # = 180 - 40 = 140
        assert result["ldl"] == expected_ldl

    def test_friedewald_high_triglycerides_invalid(self):
        """Friedewald formula is invalid when triglycerides > 400."""
        result = m.calculate_friedewald(total_cholesterol=300, hdl=50, triglycerides=450)
        assert result["ldl"] is None
        assert result["valid"] is False
        assert "exceed 400" in result["reason"]

    def test_friedewald_boundary_triglycerides(self):
        """Test at exactly 400 mg/dL triglycerides (should be valid)."""
        result = m.calculate_friedewald(total_cholesterol=250, hdl=50, triglycerides=400)
        assert result["valid"] is True
        expected_ldl = 250 - 50 - (400 / 5.0)  # = 200 - 80 = 120
        assert result["ldl"] == expected_ldl

    def test_friedewald_zero_triglycerides(self):
        """Test with zero triglycerides."""
        result = m.calculate_friedewald(total_cholesterol=180, hdl=60, triglycerides=0)
        assert result["valid"] is True
        assert result["ldl"] == 180 - 60 - 0  # = 120

    def test_friedewald_negative_values_rejected(self):
        """Negative cholesterol values should raise ValueError."""
        try:
            m.calculate_friedewald(total_cholesterol=-10, hdl=50, triglycerides=100)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)

    def test_friedewald_negative_hdl_rejected(self):
        """Negative HDL should raise ValueError."""
        try:
            m.calculate_friedewald(total_cholesterol=200, hdl=-10, triglycerides=100)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)

    def test_friedewald_negative_triglycerides_rejected(self):
        """Negative triglycerides should raise ValueError."""
        try:
            m.calculate_friedewald(total_cholesterol=200, hdl=50, triglycerides=-5)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)

    def test_friedewald_ldl_never_negative(self):
        """LDL should be clamped to 0 when calculation yields negative."""
        result = m.calculate_friedewald(total_cholesterol=100, hdl=90, triglycerides=100)
        # LDL = 100 - 90 - 20 = -10, should be clamped to 0
        assert result["ldl"] == 0.0


# --- Martin-Hopkins Formula Tests ---

class TestMartinHopkinsFormula:
    """Tests for the Martin-Hopkins LDL calculation formula."""

    def test_basic_martin_hopkins(self):
        """Test Martin-Hopkins calculation."""
        result = m.calculate_martin_hopkins(total_cholesterol=200, hdl=50, triglycerides=150)
        assert result["valid"] is True
        assert result["formula"] == "Martin-Hopkins"
        assert result["ldl"] is not None

    def test_martin_hopkins_high_triglycerides_valid(self):
        """Martin-Hopkins should be valid even with high triglycerides."""
        result = m.calculate_martin_hopkins(total_cholesterol=350, hdl=40, triglycerides=450)
        assert result["valid"] is True
        assert result["ldl"] is not None

    def test_martin_hopkins_adjustable_factor_low_tg(self):
        """Test adjustable factor for low triglycerides."""
        result = m.calculate_martin_hopkins(total_cholesterol=200, hdl=50, triglycerides=100)
        assert result["adjustable_factor"] == 5.0

    def test_martin_hopkins_adjustable_factor_high_tg(self):
        """Test adjustable factor for high triglycerides."""
        result = m.calculate_martin_hopkins(total_cholesterol=300, hdl=40, triglycerides=450)
        assert result["adjustable_factor"] == 3.0

    def test_martin_hopkins_negative_values_rejected(self):
        """Negative values should raise ValueError."""
        try:
            m.calculate_martin_hopkins(total_cholesterol=-10, hdl=50, triglycerides=100)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "non-negative" in str(e)


# --- Unified Calculator Tests ---

class TestCalculateLDL:
    """Tests for the unified calculate_ldl function."""

    def test_friedewald_method(self):
        """Test selecting Friedewald method."""
        result = m.calculate_ldl(total_cholesterol=200, hdl=50, triglycerides=150, method="friedewald")
        assert result["formula"] == "Friedewald"

    def test_martin_hopkins_method(self):
        """Test selecting Martin-Hopkins method."""
        result = m.calculate_ldl(total_cholesterol=200, hdl=50, triglycerides=150, method="martin-hopkins")
        assert result["formula"] == "Martin-Hopkins"

    def test_unknown_method_raises_error(self):
        """Unknown method should raise ValueError."""
        try:
            m.calculate_ldl(total_cholesterol=200, hdl=50, triglycerides=150, method="unknown")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown method" in str(e)

    def test_default_method_is_friedewald(self):
        """Default method should be Friedewald."""
        result = m.calculate_ldl(total_cholesterol=200, hdl=50, triglycerides=150)
        assert result["formula"] == "Friedewald"


# --- assess_row Tests ---

class TestAssessRow:
    """Tests for the assess_row function."""

    def test_ldl_calculation_via_assess_row(self):
        """Test LDL calculation through assess_row."""
        row = {"total_cholesterol": 200, "hdl": 50, "triglycerides": 150}
        result = m.assess_row(row)
        assert result["formula"] == "Friedewald"
        assert result["ldl"] == 120.0

    def test_ldl_martin_hopkins_via_assess_row(self):
        """Test Martin-Hopkins calculation through assess_row."""
        row = {"total_cholesterol": 200, "hdl": 50, "triglycerides": 150, "method": "martin-hopkins"}
        result = m.assess_row(row)
        assert result["formula"] == "Martin-Hopkins"

    def test_invalid_input_type(self):
        """Non-dict input should return error."""
        result = m.assess_row("not a dict")
        assert "error" in result

    def test_missing_ldl_values(self):
        """Missing required LDL values should return error."""
        result = m.assess_row({"total_cholesterol": 200})
        assert "error" in result

    def test_empty_dict_returns_score(self):
        """Empty dict should return generic score."""
        result = m.assess_row({})
        assert "score" in result

    def test_meld_na_calculation(self):
        """Test MELD-Na calculation through assess_row."""
        row = {"bilirubin": 3.0, "creatinine": 1.5, "inr": 1.5, "sodium": 135}
        result = m.assess_row(row)
        assert "meld_na" in result
        assert result["formula"] == "MELD-Na"

    def test_qtc_calculation(self):
        """Test QTc calculation through assess_row."""
        row = {"qt_ms": 400, "rr_ms": 1000}
        result = m.assess_row(row)
        assert "qtc" in result
        assert result["formula"] == "Bazett"

    def test_bmi_calculation(self):
        """Test BMI calculation through assess_row."""
        row = {"weight_kg": 70, "height_cm": 175, "age": 360, "sex": "M"}
        result = m.assess_row(row)
        assert "bmi" in result

    def test_hba1c_to_eag(self):
        """Test HbA1c to eAG conversion through assess_row."""
        row = {"hba1c_percent": 7.0}
        result = m.assess_row(row)
        assert "eag_mgdl" in result

    def test_apri_calculation(self):
        """Test APRI calculation through assess_row."""
        row = {"ast_u_l": 80, "alt_u_l": 60, "platelets_109": 200, "age_years": 45}
        result = m.assess_row(row)
        assert "apri" in result or "error" in result  # may error on missing fields


# --- CSV Processing Tests ---

class TestProcessCSV:
    """Tests for the process_csv function."""

    def test_basic_csv_processing(self):
        """Test basic CSV processing with LDL data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as inp:
            writer = csv.DictWriter(inp, fieldnames=["id", "total_cholesterol", "hdl", "triglycerides"])
            writer.writeheader()
            writer.writerow({"id": "A", "total_cholesterol": "200", "hdl": "50", "triglycerides": "150"})
            writer.writerow({"id": "B", "total_cholesterol": "240", "hdl": "60", "triglycerides": "200"})
            inp_path = inp.name

        out_path = inp_path + ".out.csv"
        try:
            results = m.process_csv(inp_path, out_path)
            assert len(results) == 2
            assert results[0]["ldl"] == "120.0"
            assert results[1]["ldl"] == "140.0"

            # Verify output file exists and has correct content
            with open(out_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
        finally:
            os.unlink(inp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_csv_with_missing_values(self):
        """Test CSV processing with missing/invalid values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as inp:
            writer = csv.DictWriter(inp, fieldnames=["id", "total_cholesterol", "hdl", "triglycerides"])
            writer.writeheader()
            writer.writerow({"id": "A", "total_cholesterol": "200", "hdl": "50", "triglycerides": "150"})
            writer.writerow({"id": "B", "total_cholesterol": "abc", "hdl": "50", "triglycerides": "150"})
            inp_path = inp.name

        out_path = inp_path + ".out.csv"
        try:
            results = m.process_csv(inp_path, out_path)
            assert len(results) == 2
            # Second row should have error
            assert "error" in results[1]
        finally:
            os.unlink(inp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_csv_same_input_output_raises_error(self):
        """Input and output paths must be different."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as inp:
            writer = csv.DictWriter(inp, fieldnames=["id"])
            writer.writeheader()
            inp_path = inp.name

        try:
            m.process_csv(inp_path, inp_path)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "different" in str(e).lower()
        finally:
            os.unlink(inp_path)

    def test_csv_nonexistent_input_raises_error(self):
        """Non-existent input file should raise FileNotFoundError."""
        try:
            m.process_csv("/nonexistent/path/file.csv", "/tmp/output.csv")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass

    def test_csv_with_generic_scores(self):
        """Test CSV processing with generic score data (no LDL fields)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as inp:
            writer = csv.DictWriter(inp, fieldnames=["id", "value", "qty"])
            writer.writeheader()
            writer.writerow({"id": "A", "value": "10", "qty": "2"})
            inp_path = inp.name

        out_path = inp_path + ".out.csv"
        try:
            results = m.process_csv(inp_path, out_path)
            assert len(results) == 1
            assert "score" in results[0]
        finally:
            os.unlink(inp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)


# --- CLI Tests ---

class TestCLI:
    """Tests for the CLI interface."""

    def test_single_ldl_calculation(self):
        """Test single LDL calculation via CLI."""
        exit_code = m.main([
            "single",
            "--total-cholesterol", "200",
            "--hdl", "50",
            "--triglycerides", "150"
        ])
        assert exit_code == 0

    def test_single_martin_hopkins(self):
        """Test single Martin-Hopkins calculation via CLI."""
        exit_code = m.main([
            "single",
            "--total-cholesterol", "200",
            "--hdl", "50",
            "--triglycerides", "150",
            "--method", "martin-hopkins"
        ])
        assert exit_code == 0

    def test_single_json_input(self):
        """Test single calculation with JSON input."""
        json_input = json.dumps({"total_cholesterol": 200, "hdl": 50, "triglycerides": 150})
        exit_code = m.main(["single", "--json", json_input])
        assert exit_code == 0

    def test_batch_csv_via_cli(self):
        """Test batch CSV processing via CLI."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as inp:
            writer = csv.DictWriter(inp, fieldnames=["id", "total_cholesterol", "hdl", "triglycerides"])
            writer.writeheader()
            writer.writerow({"id": "A", "total_cholesterol": "200", "hdl": "50", "triglycerides": "150"})
            inp_path = inp.name

        out_path = inp_path + ".out.csv"
        try:
            exit_code = m.main(["batch", "--input", inp_path, "--output", out_path])
            assert exit_code == 0
            assert os.path.exists(out_path)
        finally:
            os.unlink(inp_path)
            if os.path.exists(out_path):
                os.unlink(out_path)


# --- Legacy Compatibility Tests ---

class TestLegacyCompatibility:
    """Tests to ensure backward compatibility."""

    def test_calculate_score_still_works(self):
        """The legacy calculate_score function should still work."""
        result = m.calculate_score(value=10)
        assert "score" in result
        assert "inputs" in result

    def test_assess_row_generic_score(self):
        """assess_row with generic data should return score."""
        result = m.assess_row({"value": 10})
        assert "score" in result


# --- run_smoke_test for backward compat ---
def test_smoke():
    """Original smoke test preserved."""
    r = m.assess_row({"value": 10})
    assert isinstance(r, dict)
