"""
Unit tests for purlin_engine.py
Run with: pytest tests/test_purlin_engine.py -v
"""

import math
import pytest
from utils.purlin_engine import (
    PurlinInputs, ZSectionProps, DesignResult,
    compute_section, design_purlin
)


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def mid_bay_inputs():
    return PurlinInputs(
        span=35.5, bay_spacing=9.347, purlin_spacing=1.5,
        slope_x=10.0, slope_y=1.0, bay_type="Mid Bay",
        dead_load=15.0, live_load=75.0, collateral_load=75.0,
        wind_load=130.0, wind_pressure_coeff=1.4,
        fy=345.0, E=200000.0, num_sag_bars=4, lap_length=0.0,
    )

@pytest.fixture
def end_bay_inputs():
    return PurlinInputs(
        span=35.5, bay_spacing=9.347, purlin_spacing=1.5,
        slope_x=10.0, slope_y=1.0, bay_type="End Bay",
        dead_load=15.0, live_load=75.0, collateral_load=75.0,
        wind_load=130.0, wind_pressure_coeff=1.4,
        fy=345.0, E=200000.0, num_sag_bars=5, lap_length=650.0,
    )

@pytest.fixture
def mid_section():
    return ZSectionProps(t=2.0, d=246, b1=64, b2=66, L1=20, L2=20, D=250)

@pytest.fixture
def end_section():
    return ZSectionProps(t=2.5, d=245, b1=64, b2=66, L1=20, L2=20, D=250)


# ── Section property tests ────────────────────────────────────────

class TestSectionProperties:

    def test_centroid_y_in_range(self, mid_section):
        s = compute_section(mid_section)
        assert 0 < s.Y < mid_section.D, "Centroid Y must be within section depth"

    def test_Ixx_positive(self, mid_section):
        s = compute_section(mid_section)
        assert s.Ixx > 0

    def test_Iyy_positive(self, mid_section):
        s = compute_section(mid_section)
        assert s.Iyy > 0

    def test_section_moduli_consistent(self, mid_section):
        s = compute_section(mid_section)
        # Ixx = Z1xx_top × distance_top
        assert abs(s.Ixx - s.Z1xx_top * s.Y) < 1.0  # 1 mm⁴ tolerance

    def test_area_reasonable(self, mid_section):
        s = compute_section(mid_section)
        # area should be between 5 and 20 cm² for typical purlin
        assert 3 < s.area < 30

    def test_weight_per_m(self, mid_section):
        s = compute_section(mid_section)
        # density 7.85 g/cm³; for ~8 cm² area ≈ 6 kg/m
        assert 2 < s.weight_per_m < 30

    def test_thicker_section_higher_Ixx(self):
        s1 = compute_section(ZSectionProps(t=2.0, d=246, b1=64, b2=66, L1=20, L2=20, D=250))
        s2 = compute_section(ZSectionProps(t=2.5, d=245, b1=64, b2=66, L1=20, L2=20, D=250))
        assert s2.Ixx > s1.Ixx


# ── Load calculation tests ────────────────────────────────────────

class TestLoadCalculations:

    def test_slope_factor_kx(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        expected_kx = 10.0 / math.sqrt(10**2 + 1**2)
        assert abs(res.Kx - expected_kx) < 1e-6

    def test_combo1_positive(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.w_combo1 > 0, "Gravity load must be positive"

    def test_combo2_positive(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.w_combo2 > 0, "Wind uplift must be positive"

    def test_combo1_approx_value(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        # From Excel: 246.27 kg/m
        assert abs(res.w_combo1 - 246.27) < 1.0

    def test_end_bay_larger_moments(self, mid_bay_inputs, end_bay_inputs, mid_section, end_section):
        res_mid = design_purlin(mid_bay_inputs, mid_section)
        res_end = design_purlin(end_bay_inputs, end_section)
        assert res_end.M_supp_c1 > res_mid.M_supp_c1


# ── Depth check tests ─────────────────────────────────────────────

class TestDepthChecks:

    def test_depth_check_150t_pass(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        # D=250, t=2 → 150t=300: 250 < 300 → OK
        assert res.depth_check_150t.status == "OK"

    def test_depth_check_dmin_pass(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.depth_check_dmin.status == "OK"

    def test_thin_section_depth_check(self):
        inp = PurlinInputs(bay_type="Mid Bay")
        # Extremely thin section relative to depth should fail 150t check
        thin = ZSectionProps(t=1.0, d=196, b1=60, b2=62, L1=16, L2=16, D=200)
        res = design_purlin(inp, thin)
        # D=200, 150t=150: 200 > 150 → NOT OK
        assert res.depth_check_150t.status == "NOT OK"

    def test_flange_check_passes_for_adopted_section(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.flange_check.status == "OK"
        assert res.flange_effective

    def test_wide_flange_requires_reduced_width_design(self, mid_bay_inputs):
        wide = ZSectionProps(t=2.0, d=246, b1=100, b2=66, L1=20, L2=20, D=250)
        res = design_purlin(mid_bay_inputs, wide)
        assert res.flange_check.status == "NOT OK"
        assert not res.passed
        assert res.flange_check.label in res.fail_reasons


# ── Stress check tests ────────────────────────────────────────────

class TestStressChecks:

    def test_mid_bay_adopted_section_passes(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        # The Excel-validated Z-250×2.0 mid bay section should pass all stress checks
        for chk in res.stress_checks:
            assert chk.status == "OK", f"Stress check failed: {chk.label}"

    def test_fb_less_than_fy(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.Fb <= mid_bay_inputs.fy * 0.7, "Fb should not exceed ~0.6Fy"

    def test_fb_positive(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.Fb > 0


# ── Deflection tests ──────────────────────────────────────────────

class TestDeflection:

    def test_mid_bay_deflection_passes(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.defl_check_c1.status == "OK"
        assert res.defl_check_c2.status == "OK"

    def test_allowable_deflection_formula(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        expected = mid_bay_inputs.bay_spacing * 1000 / 150
        assert abs(res.delta_allow - expected) < 0.01

    def test_delta_positive(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.delta_c1 > 0
        assert res.delta_c2 > 0


# ── Overlap tests ─────────────────────────────────────────────────

class TestOverlap:

    def test_overlap_check_passes(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.lap_check.status == "OK"

    def test_custom_lap_respected(self, mid_bay_inputs, mid_section):
        inp = PurlinInputs(**{**mid_bay_inputs.__dict__, "lap_length": 1175.0})
        res = design_purlin(inp, mid_section)
        assert abs(res.lap_used * 1000 - 1175.0) < 1.0

    def test_m_capacity_positive(self, mid_bay_inputs, mid_section):
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.M_capacity > 0


# ── Overall design tests ──────────────────────────────────────────

class TestOverallDesign:

    def test_mid_bay_excel_section_passes(self, mid_bay_inputs, mid_section):
        """Z-250×2.0 for mid bay from Excel should pass all checks."""
        res = design_purlin(mid_bay_inputs, mid_section)
        assert res.passed, f"Failed checks: {res.fail_reasons}"

    def test_inadequate_section_fails(self, mid_bay_inputs):
        """Very thin shallow section should fail."""
        tiny = ZSectionProps(t=1.2, d=146, b1=50, b2=52, L1=14, L2=14, D=150)
        res = design_purlin(mid_bay_inputs, tiny)
        assert not res.passed, "Tiny section should fail design checks"

    def test_fail_reasons_populated_on_failure(self, mid_bay_inputs):
        tiny = ZSectionProps(t=1.2, d=146, b1=50, b2=52, L1=14, L2=14, D=150)
        res = design_purlin(mid_bay_inputs, tiny)
        assert len(res.fail_reasons) > 0
