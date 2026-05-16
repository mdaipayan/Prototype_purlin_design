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
    X: float = 0.0      # centroid from top (mm)
    Y: float = 0.0      # centroid from right (mm)
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
    All inputs and outputs in mm (Ixx in mm⁴, Z in mm³).
    Area returned in cm², weight in kg/m.
    """
    t  = sec.t
    d  = sec.d    # clear web depth
    b1 = sec.b1
    b2 = sec.b2
    L1 = sec.L1
    L2 = sec.L2
    D  = sec.D    # overall depth = d + 2t  (approximately)

    # Elements (centre-line model):
    # 1. Top flange: b1 × t, centroid y from top edge = t/2
    # 2. Web:        (D-2t) × t, centroid y = t + (D-2t)/2
    # 3. Bottom flange: b2 × t, centroid y = D - t/2
    # 4. Top lip:    L1 × t,  centroid x ≈ (b1 - t/2), y = t/2
    # 5. Bottom lip: L2 × t,  centroid x ≈ -(b2 - t/2), y = D - t/2

    h = D  # overall depth

    # Areas
    A_tf = b1 * t
    A_bf = b2 * t
    A_w  = (h - 2*t) * t
    A_L1 = L1 * t
    A_L2 = L2 * t
    A_total = A_tf + A_bf + A_w + A_L1 + A_L2

    # y-centroids from top
    y_tf = t / 2
    y_bf = h - t / 2
    y_w  = t + (h - 2*t) / 2
    y_L1 = t / 2
    y_L2 = h - t / 2

    # Centroid Y from top
    Ybar = (A_tf*y_tf + A_bf*y_bf + A_w*y_w + A_L1*y_L1 + A_L2*y_L2) / A_total

    # Ixx about neutral axis
    def rect_I(b, h_r): return b * h_r**3 / 12

    Ixx = (
        rect_I(b1, t)  + A_tf * (y_tf - Ybar)**2 +
        rect_I(t, h-2*t) + A_w  * (y_w  - Ybar)**2 +
        rect_I(b2, t)  + A_bf * (y_bf - Ybar)**2 +
        rect_I(t, L1)  + A_L1 * (y_L1 - Ybar)**2 +
        rect_I(t, L2)  + A_L2 * (y_L2 - Ybar)**2
    )

    # x-centroids (Z-section: top flange right, bottom flange left)
    x_tf = b1 / 2          # from web centre-line
    x_bf = -b2 / 2
    x_w  = 0.0
    x_L1 = b1 - t/2       # lip extends from end of top flange
    x_L2 = -(b2 - t/2)

    Xbar = (A_tf*x_tf + A_bf*x_bf + A_w*x_w + A_L1*x_L1 + A_L2*x_L2) / A_total

    Iyy = (
        rect_I(t, b1)  + A_tf * (x_tf - Xbar)**2 +
        rect_I(t, b2)  + A_bf * (x_bf - Xbar)**2 +
        rect_I(h-2*t, t) + A_w  * (x_w  - Xbar)**2 +
        rect_I(t, L1)  + A_L1 * (x_L1 - Xbar)**2 +
        rect_I(t, L2)  + A_L2 * (x_L2 - Xbar)**2
    )

    Z1xx_top = Ixx / Ybar
    Z1xx_bot = Ixx / (h - Ybar)

    # Zyy: distance to right-most fibre = b1 - Xbar
    right_fibre = b1 - Xbar
    left_fibre  = b2 + Xbar   # distance to left-most fibre (bottom flange side)
    Zyy_right = Iyy / right_fibre if right_fibre > 0 else 0
    Zyy_left  = Iyy / left_fibre  if left_fibre  > 0 else 0

    area_cm2     = A_total / 100        # mm² → cm²
    weight_kg_m  = area_cm2 * 7.85 / 10  # kg/m

    sec.X           = Xbar
    sec.Y           = Ybar
    sec.Ixx         = Ixx
    sec.Iyy         = Iyy
    sec.Z1xx_top    = Z1xx_top
    sec.Z1xx_bot    = Z1xx_bot
    sec.Zyy_right   = Zyy_right
    sec.Zyy_left    = Zyy_left
    sec.area        = area_cm2
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
    # Approximate actual stress in compression element
    Zxx_top_cm3 = r.section.Z1xx_top / 1000   # mm³ → cm³
    if Zxx_top_cm3 > 0:
        f_actual_kgcm2 = (r.M_supp_gvn * 100) / Zxx_top_cm3  # kg/cm²
    else:
        f_actual_kgcm2 = 0

    f_actual_kgcm2 = max(f_actual_kgcm2, 1)
    r.b1_t_actual = b1 / t
    r.b1_t_limit  = 1435 / math.sqrt(f_actual_kgcm2)
    r.flange_effective = r.b1_t_actual <= r.b1_t_limit

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
