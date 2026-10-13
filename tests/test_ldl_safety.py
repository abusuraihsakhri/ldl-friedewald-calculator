"""Regression tests for calculation safety, API behavior, and audit tampering."""
import math
import pytest
from agents.base import AuditTrail
from ldl_calc import calculate_friedewald, calculate_sampson, calculate_martin_hopkins


@pytest.mark.parametrize("tc,hdl,tg", [
    (math.nan, 40, 100), (200, math.inf, 100), (200, 40, -1),
    (100, 120, 100), ("nan", 40, 100)
])
def test_bad_panel_rejected(tc, hdl, tg):
    with pytest.raises(ValueError):
        calculate_friedewald(tc, hdl, tg)
    with pytest.raises(ValueError):
        calculate_sampson(tc, hdl, tg)


@pytest.mark.parametrize("tg", [400, 401, 800, 1000])
def test_friedewald_upper_limit(tg):
    result = calculate_friedewald(300, 50, tg)
    assert result["ldl"] is None and not result["valid"]


def test_martin_hopkins_withheld_without_180_cell_table():
    r = calculate_martin_hopkins(200, 50, 150)
    assert r["ldl"] is None and not r["valid"]


def test_sampson_upper_limit():
    assert calculate_sampson(250, 40, 799)["valid"]
    assert not calculate_sampson(250, 40, 800)["valid"]


def test_audit_detects_forged_signature_and_no_external_mutation():
    trail = AuditTrail(secret_key="unit-test")
    trail.log("unit", "test", "event", {"result": "PASS"})
    assert trail.verify_integrity()
    trail.get_trail()[0]["current_hash"] = "forged"
    assert trail.verify_integrity()  # accessor returns a defensive copy
    trail.logs[0]["payload_hash"] = "forged"
    assert not trail.verify_integrity()


def test_fastapi_ldl_endpoint_uses_same_calculation():
    from agents.api import api_ldl, LipidPanel
    r = api_ldl(LipidPanel(total_cholesterol=200, hdl=50, triglycerides=150,
                           method="sampson"))
    assert r["formula"] == "Sampson-NIH"
    assert r["ldl"] == 123.40


def test_csv_critical_flag_parser_rejects_ambiguous_values():
    from cli import parse_csv_bool, csv_safe
    assert parse_csv_bool("false") is False
    assert parse_csv_bool("TRUE") is True
    with pytest.raises(ValueError):
        parse_csv_bool("maybe")
    assert csv_safe("=1+1").startswith("'")
    assert csv_safe("normal") == "normal"
