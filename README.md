# 🏗️ Purlin Design App — IS 801-1975

[![CI](https://github.com/YOUR_USERNAME/purlin-design-app/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/purlin-design-app/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)](https://streamlit.io)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-black)](https://flake8.pycqa.org)

A production-grade Streamlit application for the design of cold-formed **Z-section purlins** per Indian Standard codes, with automatic PDF report generation.

---

## Features

| Feature | Details |
|---------|---------|
| **Full IS 801-1975 design algorithm** | All 13 steps — loads → section classification → stress → deflection → overlap |
| **Two bay types** | End bay (coefficients 0.0772 / 0.1071) and mid bay (0.0364 / 0.0714) |
| **Two load combinations** | Combo I: DL+LL+CL (gravity) · Combo II: WL−DL (uplift) |
| **Lateral buckling** | Fb per IS 801 cl. 6.3(b) with 33% wind increase (cl. 6.1.2) |
| **Deflection check** | Span/150 limit; separate coefficients for end/mid bay |
| **Overlap check** | Moment at lap vs section capacity |
| **PDF report** | Professional ReportLab report with all check tables |
| **Section database** | Standard Z-sections with computed properties |
| **CI / GitHub Actions** | Matrix tests (Python 3.10–3.12), coverage, linting |

---

## Design Algorithm (13 Steps)

```
Step 1  ── Collect input data (geometry, loads, material)
Step 2  ── Compute slope reduction factors Kx, Ky
Step 3  ── Design load per metre — 2 combinations
Step 4  ── Design bending moments (end bay / mid bay coefficients)
Step 5  ── Z-section property computation (centroid, Ixx, Iyy, Zxx, Zyy)
Step 6  ── Depth checks: D < 150t  &  d ≥ d_min  (IS 801 cl. 5.2.4 & 5.2.1.2)
Step 7  ── Effective flange width: (b1/t) ≤ 1435/√f  (IS 801 cl. 5.2.1.1)
Step 8  ── Unbraced length, Iyc, Sxc (sag bar layout)
Step 9  ── Permissible bending stress Fb  (IS 801 cl. 6.3b)
Step 10 ── Actual vs permissible stress — 4 check cases
Step 11 ── Deflection: δ ≤ Le/150
Step 12 ── Overlap / lap length check
Step 13 ── Adopt final section
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/purlin-design-app.git
cd purlin-design-app

# Install
pip install -r requirements.txt

# Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Set:
   - **Repository**: `YOUR_USERNAME/purlin-design-app`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Click **Deploy**.

No secrets or environment variables required.

---

## Project Structure

```
purlin-design-app/
├── app.py                        # Main Streamlit app (Design page)
├── pages/
│   └── 1_Section_Database.py     # Z-section browser
├── utils/
│   ├── purlin_engine.py          # Core design engine (Steps 1–13)
│   └── pdf_report.py             # ReportLab PDF report generator
├── tests/
│   └── test_purlin_engine.py     # 20+ pytest unit/integration tests
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI (3 Python versions)
├── .streamlit/
│   └── config.toml               # Theme & server config
└── requirements.txt
```

---

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=utils --cov-report=term-missing
```

Expected output: **20+ tests passing** across section properties, loads, depth checks, stress checks, deflection, and overlap.

---

## Code References

| Check | IS Code Reference |
|-------|------------------|
| Overall depth | IS 801-1975, cl. 5.2.4 |
| Minimum depth | IS 801-1975, cl. 5.2.1.2 |
| Effective flange width | IS 801-1975, cl. 5.2.1.1 |
| Permissible bending stress | IS 801-1975, cl. 6.3(b) |
| Basic design stress | IS 801-1975, cl. 6.1 |
| Wind stress increase | IS 801-1975, cl. 6.1.2 |
| Wind pressure coefficients | IS 875 (Part 3)-1987, Table 5 |
| Material grade | IS 2062 |

---

## Contributing

Pull requests are welcome. For major changes please open an issue first.

---

## License

MIT — free for academic and commercial use.

---

*Developed as part of structural engineering software tools — Department of Civil Engineering,  
Kavikulguru Institute of Technology and Science (KITS), Ramtek, Nagpur — RTMNU.*
