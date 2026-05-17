"""
Purlin Design Engine — IS 801-1975 / IS 875-1987
Implements all 13 steps of the design algorithm.
"""

import math
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class PurlinInputs:
    # Geometry
    span: float = 35.5          # m
    bay_spacing: float = 9.347  # m (= Le)
    purlin_spacing: float = 1.5 # m
    slope_x: float = 10.0       # horizontal component
    slope_y: float = 1.0        # vertical component
    bay_type: str = "Mid Bay"   # "End Bay" or "Mid Bay"

    # Loads (kg/m²)
    dead_load: float = 15.0
    live_load: float = 75.0
    collateral_load: float = 75.0
    wind_load: float = 130.0
    wind_pressure_coeff: float = 1.4  # Cp1

    # Material
    fy: float = 345.0   # MPa (N/mm²)
    E: float = 200000.0 # MPa (steel)

    # Sag bars
    num_sag_bars: int = 4

    # Lap length (mm) — 0 = auto-compute
    lap_length: float = 0.0


@dataclass
class ZSectionProps:
    t: float   # thickness mm
    d: float   # web depth mm (clear)
    b1: float  # top flange mm
    b2: float  # bottom flange mm
    L1: float  # top lip mm
    L2: float  # bottom lip mm
    D: float   # overall depth mm

    # Computed — filled by compute_section()
    X: float = 0.0      # horizontal centroid from web centre-line (mm)
    Y: float = 0.0      # vertical centroid from top edge (mm)
    Ixx: float = 0.0    # mm⁴
    Iyy: float = 0.0    # mm⁴
    Z1xx_top: float = 0.0   # mm³
    Z1xx_bot: float = 0.0   # mm³
    Zyy_right: float = 0.0  # mm³
    Zyy_left: float = 0.0   # mm³
    area: float = 0.0        # cm²
    weight_per_m: float = 0.0  # kg/m


@dataclass
class CheckResult:
    label: str
    value: float
    limit: float
    unit: str
    status: str          # "OK" | "NOT OK"
    formula: str = ""


@dataclass
class DesignResult:
    # Step outputs
    Kx: float = 0.0
    Ky: float = 0.0
    w_combo1: float = 0.0   # kg/m (downward)
    w_combo2: float = 0.0   # kg/m (upward)

    M_span_c1: float = 0.0   # kg·m
    M_supp_c1: float = 0.0
    M_span_c2: float = 0.0
    M_supp_c2: float = 0.0
    M_span_gvn: float = 0.0  # governing
    M_supp_gvn: float = 0.0
    w_governing: float = 0.0

    section: Optional[ZSectionProps] = None

    # Depth checks
    depth_check_150t: Optional[CheckResult] = None
    depth_check_dmin: Optional[CheckResult] = None

    # Flange effective width
    b1_t_actual: float = 0.0
    b1_t_limit: float = 0.0
    flange_effective: bool = True
    flange_check: Optional[CheckResult] = None

    # Lateral buckling
    L_unbraced: float = 0.0  # m
    Iyc: float = 0.0          # cm⁴
    Sxc: float = 0.0          # cm³
    lambda_val: float = 0.0
    Fb: float = 0.0           # N/mm²
    F_basic: float = 0.0      # N/mm²

    # Stress checks
    stress_checks: list = field(default_factory=list)

    # Deflection
    delta_allow: float = 0.0  # mm
    delta_c1: float = 0.0     # mm
    delta_c2: float = 0.0     # mm
    defl_check_c1: Optional[CheckResult] = None
    defl_check_c2: Optional[CheckResult] = None

    # Overlap
    M_capacity: float = 0.0   # kg·m
    lap_used: float = 0.0     # m
    M_at_lap: float = 0.0     # kg·m
    lap_check: Optional[CheckResult] = None

    # Overall pass/fail
    passed: bool = False
    fail_reasons: list = field(default_factory=list)


# ─────────────────────────────────────────────
# SECTION PROPERTY CALCULATOR
# ─────────────────────────────────────────────

def compute_section(sec: ZSectionProps) -> ZSectionProps:
    """
    Compute centroid, Ixx, Iyy, section moduli for a Z-section.

    The section-property model intentionally follows the legacy Excel
    calculation used for this design workbook.  In that sheet, the web is
    taken as the clear web depth ``d`` and the return lips are reduced by one
    plate thickness at the bends (``L1 - t`` and ``L2 - t``).  This avoids
    double-counting the corner material and reproduces the workbook Ixx value
    of 7,416,273.44 mm⁴ for the default 250×2 Z-purlin.

    All inputs and outputs are in mm (Ixx/Iyy in mm⁴, Z in mm³). Area is
    returned in cm² and weight in kg/m.
    """
    t = sec.t
    d = sec.d      # clear web depth between flange bend lines
    b1 = sec.b1
    b2 = sec.b2
    L1 = sec.L1
    L2 = sec.L2
    D = sec.D      # overall depth used for extreme-fibre distances

    # Excel/legacy plate-line model areas.  Lips are reduced by one thickness
    # because the bend/corner material is already represented by the flanges.
    lip1_depth = max(L1 - t, 0.0)
    lip2_depth = max(L2 - t, 0.0)

    A_w = t * d
    A_tf = b1 * t
    A_bf = b2 * t
    A_L1 = lip1_depth * t
    A_L2 = lip2_depth * t
    A_total = A_w + A_tf + A_bf + A_L1 + A_L2

    if A_total <= 0:
        sec.X = sec.Y = sec.Ixx = sec.Iyy = 0.0
        sec.Z1xx_top = sec.Z1xx_bot = sec.Zyy_right = sec.Zyy_left = 0.0
        sec.area = sec.weight_per_m = 0.0
        return sec

    # y-centroids from the top outer face, matching the Excel substitutions:
    # web: 0.5d + t; top flange: 0.5t; top lip: t + 0.5(L1 - t);
    # bottom flange: d + 1.5t; bottom lip: d + t - 0.5(L2 - t).
    y_w = t + d / 2
    y_tf = t / 2
    y_L1 = t + lip1_depth / 2
    y_bf = d + 1.5 * t
    y_L2 = d + t - lip2_depth / 2

    Ybar = (
        A_w * y_w + A_tf * y_tf + A_L1 * y_L1 +
        A_bf * y_bf + A_L2 * y_L2
    ) / A_total

    # Ixx about the horizontal neutral axis.  This is written in the same five
    # component order as the Excel sheet: web, top flange, top lip, bottom
    # flange, bottom lip.  Flange local Ixx is omitted because it is negligible
    # in the source workbook; web/lip local Ixx is included.
    I_web = t * d**3 / 12 + A_w * (y_w - Ybar) ** 2
    I_top_flange = A_tf * (Ybar - y_tf) ** 2
    I_top_lip = t * lip1_depth**3 / 12 + A_L1 * (Ybar - y_L1) ** 2
    I_bottom_flange = A_bf * (y_bf - Ybar) ** 2
    I_bottom_lip = t * lip2_depth**3 / 12 + A_L2 * (y_L2 - Ybar) ** 2
    Ixx = I_web + I_top_flange + I_top_lip + I_bottom_flange + I_bottom_lip

    # x-centroids from web centre-line.  The same reduced lip areas are used so
    # Xbar, Iyy, and weight remain consistent with the corrected Ixx model.
    x_w = 0.0
    x_tf = b1 / 2
    x_bf = -b2 / 2
    x_L1 = b1 - t / 2
    x_L2 = -(b2 - t / 2)

    Xbar = (
        A_w * x_w + A_tf * x_tf + A_bf * x_bf +
        A_L1 * x_L1 + A_L2 * x_L2
    ) / A_total

    Iyy = (
        d * t**3 / 12 + A_w * (x_w - Xbar) ** 2 +
        t * b1**3 / 12 + A_tf * (x_tf - Xbar) ** 2 +
        t * b2**3 / 12 + A_bf * (x_bf - Xbar) ** 2 +
        lip1_depth * t**3 / 12 + A_L1 * (x_L1 - Xbar) ** 2 +
        lip2_depth * t**3 / 12 + A_L2 * (x_L2 - Xbar) ** 2
    )

    top_fibre = Ybar
    bottom_fibre = max(D - Ybar, 0.0)
    Z1xx_top = Ixx / top_fibre if top_fibre > 0 else 0.0
    Z1xx_bot = Ixx / bottom_fibre if bottom_fibre > 0 else 0.0

    # Zyy extreme-fibre distances from Xbar.
    right_fibre = b1 - Xbar
    left_fibre = b2 + Xbar
    Zyy_right = Iyy / right_fibre if right_fibre > 0 else 0.0
    Zyy_left = Iyy / left_fibre if left_fibre > 0 else 0.0

    area_cm2 = A_total / 100        # mm² → cm²
    weight_kg_m = area_cm2 * 7.85 / 10  # kg/m

    sec.X = Xbar
    sec.Y = Ybar
    sec.Ixx = Ixx
    sec.Iyy = Iyy
    sec.Z1xx_top = Z1xx_top
    sec.Z1xx_bot = Z1xx_bot
    sec.Zyy_right = Zyy_right
    sec.Zyy_left = Zyy_left
    sec.area = area_cm2
    sec.weight_per_m = weight_kg_m
    return sec

# ─────────────────────────────────────────────
# MAIN DESIGN FUNCTION
# ─────────────────────────────────────────────

def design_purlin(inp: PurlinInputs, sec: ZSectionProps) -> DesignResult:
    r = DesignResult()
    r.section = compute_section(sec)
    r.fail_reasons = []

    L   = inp.bay_spacing          # m
    Le  = inp.bay_spacing          # m (effective = bay spacing for simply supported)
    Ps  = inp.purlin_spacing       # m
    Fy  = inp.fy                   # N/mm²
    E   = inp.E                    # N/mm²
    end_bay = (inp.bay_type == "End Bay")

    # ── STEP 2: Slope factors ──────────────────
    mag = math.sqrt(inp.slope_x**2 + inp.slope_y**2)
    r.Kx = inp.slope_x / mag
    r.Ky = inp.slope_y / mag

    # ── STEP 3: Design loads (kg/m) ───────────
    r.w_combo1 = (inp.dead_load + inp.live_load + inp.collateral_load) * r.Kx * Ps
    r.w_combo2 = (inp.wind_load * inp.wind_pressure_coeff - inp.dead_load * r.Kx) * Ps

    # ── STEP 4: Bending moments ───────────────
    if end_bay:
        coeff_span = 0.0772
        coeff_supp = 0.1071
    else:
        coeff_span = 0.0364
        coeff_supp = 0.0714

    r.M_span_c1 = coeff_span * r.w_combo1 * L**2  # kg·m
    r.M_supp_c1 = coeff_supp * r.w_combo1 * L**2
    r.M_span_c2 = coeff_span * r.w_combo2 * L**2
    r.M_supp_c2 = coeff_supp * r.w_combo2 * L**2

    r.M_span_gvn = max(r.M_span_c1, r.M_span_c2)
    r.M_supp_gvn = max(r.M_supp_c1, r.M_supp_c2)
    r.w_governing = max(r.w_combo1, r.w_combo2)

    # ── STEP 6: Depth checks ──────────────────
    D   = sec.D
    t   = sec.t
    b1  = sec.b1

    # Check A: D < 150t
    r.depth_check_150t = CheckResult(
        label="Overall depth D < 150t",
        value=D, limit=150*t, unit="mm",
        status="OK" if D < 150*t else "NOT OK",
        formula="D < 150·t"
    )

    # Check B: d_min.  The bracketed expression is under a square root;
    # omitting the root overstates the required web depth by an order of
    # magnitude and incorrectly rejects typical validated sections.
    b1_over_t = b1 / t
    term = (b1_over_t)**2 - 281200 / Fy
    dmin_calc = 2.8 * t * math.sqrt(term) if term > 0 else 0
    dmin = max(dmin_calc, 4.8 * t)
    r.depth_check_dmin = CheckResult(
        label="Web depth d ≥ d_min",
        value=round(sec.d, 2), limit=round(dmin, 2), unit="mm",
        status="OK" if sec.d >= dmin else "NOT OK",
        formula="d_min = max(2.8t√[(b1/t)² - 281200/Fy], 4.8t)"
    )

    for chk in [r.depth_check_150t, r.depth_check_dmin]:
        if chk.status == "NOT OK":
            r.fail_reasons.append(chk.label)

    # ── STEP 7: Effective flange width ────────
    # IS 801 cl. 5.2.1.1 uses the actual compression stress in kgf/cm².
    # Near-support lapped purlins are checked with two nested sections, so the
    # support stress must use 2·Zxx just like the bending-stress checks below.
    Zxx_top_cm3 = r.section.Z1xx_top / 1000   # mm³ → cm³
    if Zxx_top_cm3 > 0:
        flange_stresses = [
            (r.M_supp_c1 * 100) / (2 * Zxx_top_cm3),
            (r.M_span_c1 * 100) / Zxx_top_cm3,
            (r.M_supp_c2 * 100) / (2 * Zxx_top_cm3),
            (r.M_span_c2 * 100) / Zxx_top_cm3,
        ]
        f_actual_kgcm2 = max(flange_stresses)
    else:
        f_actual_kgcm2 = 0

    f_actual_kgcm2 = max(f_actual_kgcm2, 1)
    r.b1_t_actual = b1 / t
    r.b1_t_limit  = 1435 / math.sqrt(f_actual_kgcm2)
    r.flange_effective = r.b1_t_actual <= r.b1_t_limit
    r.flange_check = CheckResult(
        label="Compression flange b1/t ≤ 1435/√f",
        value=round(r.b1_t_actual, 2), limit=round(r.b1_t_limit, 2), unit="—",
        status="OK" if r.flange_effective else "NOT OK",
        formula="b1/t ≤ 1435/√f, f = max actual compression stress (kgf/cm²)"
    )
    if r.flange_check.status == "NOT OK":
        r.fail_reasons.append(r.flange_check.label)

    # ── STEP 8: Unbraced length & Iyc ─────────
    r.L_unbraced = L / (inp.num_sag_bars + 1)   # m
    r.Iyc = r.section.Iyy / (2 * 1e4)            # mm⁴ → cm⁴  (compression half)
    r.Sxc = r.section.Z1xx_top / 1000            # mm³ → cm³

    # ── STEP 9: Permissible bending stress ────
    Cb = 1.0  # uniform moment (conservative)
    L_cm = r.L_unbraced * 100  # m → cm
    d_cm = D / 10              # mm → cm
    E_kgcm2 = E / 0.0981       # N/mm² → kgf/cm²  (1 kgf/cm² = 0.0981 N/mm²)
    Fy_kgcm2 = Fy / 0.0981

    r.lambda_val = (L_cm**2 * r.Sxc) / (d_cm * r.Iyc)

    lim1 = 0.18 * math.pi**2 * E_kgcm2 * Cb / Fy_kgcm2
    lim2 = 0.90 * math.pi**2 * E_kgcm2 * Cb / Fy_kgcm2

    if r.lambda_val <= lim1:
        Fb_kgcm2 = (2.0/3.0) * Fy_kgcm2
    elif r.lambda_val <= lim2:
        Fb_kgcm2 = (2.0/3.0)*Fy_kgcm2 - (Fy_kgcm2**2 / (2.7*math.pi**2*E_kgcm2*Cb)) * r.lambda_val
    else:
        Fb_kgcm2 = (0.9 * math.pi**2 * E_kgcm2 * Cb) / r.lambda_val

    F_basic_kgcm2 = 0.6 * Fy_kgcm2
    Fb_kgcm2 = min(Fb_kgcm2, F_basic_kgcm2)

    r.Fb     = Fb_kgcm2 * 0.0981   # → N/mm²
    r.F_basic = F_basic_kgcm2 * 0.0981

    # ── STEP 10: Stress checks ────────────────
    r.stress_checks = []
    Zxx_top_mm3 = r.section.Z1xx_top
    Fb_wind = r.Fb * 1.33   # 33% increase for wind (IS 801 cl. 6.1.2)

    # Convert moments to N·mm: M(kg·m) × 9.81 × 1000 → N·mm
    def kgm_to_Nmm(m): return m * 9.81 * 1000

    # DL+LL+COL — near support
    fb_supp_c1 = kgm_to_Nmm(r.M_supp_c1) / (2 * Zxx_top_mm3)
    r.stress_checks.append(CheckResult(
        label="DL+LL+CL — near support",
        value=round(fb_supp_c1, 2), limit=round(r.Fb, 2), unit="N/mm²",
        status="OK" if fb_supp_c1 <= r.Fb else "NOT OK",
        formula="M_supp / (2·Zxx) ≤ Fb"
    ))

    # DL+LL+COL — near midspan
    fb_span_c1 = kgm_to_Nmm(r.M_span_c1) / Zxx_top_mm3
    r.stress_checks.append(CheckResult(
        label="DL+LL+CL — near midspan",
        value=round(fb_span_c1, 2), limit=round(r.Fb, 2), unit="N/mm²",
        status="OK" if fb_span_c1 <= r.Fb else "NOT OK",
        formula="M_span / Zxx ≤ Fb"
    ))

    # DL+WL — near support (Fb × 1.33)
    fb_supp_c2 = kgm_to_Nmm(r.M_supp_c2) / (2 * Zxx_top_mm3)
    r.stress_checks.append(CheckResult(
        label="DL+WL — near support (Fb × 1.33)",
        value=round(fb_supp_c2, 2), limit=round(Fb_wind, 2), unit="N/mm²",
        status="OK" if fb_supp_c2 <= Fb_wind else "NOT OK",
        formula="M_supp / (2·Zxx) ≤ 1.33·Fb"
    ))

    # DL+WL — near midspan (Fb × 1.33)
    fb_span_c2 = kgm_to_Nmm(r.M_span_c2) / Zxx_top_mm3
    r.stress_checks.append(CheckResult(
        label="DL+WL — near midspan (Fb × 1.33)",
        value=round(fb_span_c2, 2), limit=round(Fb_wind, 2), unit="N/mm²",
        status="OK" if fb_span_c2 <= Fb_wind else "NOT OK",
        formula="M_span / Zxx ≤ 1.33·Fb"
    ))

    for chk in r.stress_checks:
        if chk.status == "NOT OK":
            r.fail_reasons.append(chk.label)

    # ── STEP 11: Deflection check ─────────────
    E_Nmm2 = E       # N/mm²
    Ixx_mm4 = r.section.Ixx  # mm⁴
    Le_mm   = Le * 1000       # m → mm

    coeff_defl = 0.0065 if end_bay else 0.00285

    # w in N/mm
    w_c1_Nmm = (r.w_combo1 * 9.81) / 1000   # kg/m → N/mm
    w_c2_Nmm = (r.w_combo2 * 9.81) / 1000

    r.delta_allow = Le_mm / 150
    r.delta_c1 = coeff_defl * w_c1_Nmm * Le_mm**4 / (E_Nmm2 * Ixx_mm4)
    r.delta_c2 = coeff_defl * w_c2_Nmm * Le_mm**4 / (E_Nmm2 * Ixx_mm4)

    r.defl_check_c1 = CheckResult(
        label="Deflection DL+LL+CL",
        value=round(r.delta_c1, 2), limit=round(r.delta_allow, 2), unit="mm",
        status="OK" if r.delta_c1 <= r.delta_allow else "NOT OK",
        formula="0.00285·w·Le⁴/(EI) ≤ Le/150" if not end_bay else "0.0065·w·Le⁴/(EI) ≤ Le/150"
    )
    r.defl_check_c2 = CheckResult(
        label="Deflection DL+WL",
        value=round(r.delta_c2, 2), limit=round(r.delta_allow, 2), unit="mm",
        status="OK" if r.delta_c2 <= r.delta_allow else "NOT OK",
        formula=r.defl_check_c1.formula
    )

    for chk in [r.defl_check_c1, r.defl_check_c2]:
        if chk.status == "NOT OK":
            r.fail_reasons.append(chk.label)

    # ── STEP 12: Overlap check ────────────────
    Fb_kgcm2_use = r.Fb / 0.0981
    Zxx_top_cm3  = r.section.Z1xx_top / 1000
    r.M_capacity = Zxx_top_cm3 * Fb_kgcm2_use / 100   # kg·m

    # Determine lap
    if inp.lap_length > 0:
        X_m = inp.lap_length / 1000   # mm → m
    else:
        # Auto: try 0.35·L → 1.5·L in steps
        X_m = 0.35 * L
        for trial in [x * L / 10 for x in range(3, 16)]:
            M_trial = (r.w_governing * trial**2 / 2 +
                       r.w_governing * L**2 / 12 -
                       r.w_governing * L * trial / 2)
            if M_trial <= r.M_capacity:
                X_m = trial
                break

    r.lap_used = X_m
    r.M_at_lap = (r.w_governing * X_m**2 / 2 +
                  r.w_governing * L**2 / 12 -
                  r.w_governing * L * X_m / 2)

    r.lap_check = CheckResult(
        label="Overlap moment capacity",
        value=round(r.M_at_lap, 2), limit=round(r.M_capacity, 2), unit="kg·m",
        status="OK" if r.M_at_lap <= r.M_capacity else "NOT OK",
        formula="M_at_X = wX²/2 + wL²/12 − wLX/2 ≤ M_capacity"
    )
    if r.lap_check.status == "NOT OK":
        r.fail_reasons.append("Overlap check")

    # ── Overall ───────────────────────────────
    r.passed = len(r.fail_reasons) == 0
    return r
