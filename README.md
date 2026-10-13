# LDL-C Calculator — Friedewald & Sampson-NIH

A lipid calculation tool for single panels and batch CSV files. Includes a **fully offline browser application**, a standard-library Python CLI, and an optional FastAPI service.

The repository also retains legacy non-LDL utilities and audit simulation commands for compatibility. Their outputs are not substitutes for separately validated clinical tools.

## Browser application

Open `web/index.html` in a modern browser. No installation, login, backend, telemetry, or network connection is required for calculations. The page supports:

- Friedewald and Sampson-NIH LDL-C estimates, with validity warnings
- Total, HDL, and triglyceride inputs in mg/dL or mmol/L
- Non-HDL cholesterol and copyable summaries
- Local CSV processing, preview, and downloadable results (CSV inputs in **mg/dL**)

**Privacy:** Lipid values and uploaded CSV files are processed within the browser. Files are not uploaded or persisted by the application. Do not enter patient identifiers. The standalone FastAPI service is separate and has its own network exposure.

For local HTTP serving:

```bash
python -m http.server 8000 --directory web
# Open http://localhost:8000/
```

GitHub Pages publishing is configured through `.github/workflows/pages.yml`. A live URL should be used only after deployment is enabled and verified.

## Calculation methods and limits

All Python function inputs and results are in **mg/dL**, unless otherwise specified.

| Method | Calculation | Reporting limit |
| --- | --- | --- |
| Friedewald | LDL-C = TC − HDL-C − TG/5 | TG **below** 400 mg/dL |
| Sampson-NIH (2020) | TC/0.948 − HDL/0.971 − (TG/8.56 + TG×non-HDL/2140 − TG²/16100) − 9.44 | TG **below** 800 mg/dL |

Non-HDL-C = TC − HDL-C. Non-finite, negative, and inconsistent cholesterol measurements are rejected. Negative LDL-C predictions are withheld rather than set to zero.

The original **Martin/Hopkins** method requires a validated **180-cell lookup table** indexed by triglycerides and non-HDL-C. The former implementation used five TG-only factors; this is *not* Martin/Hopkins. To prevent misreporting, the legacy `calculate_martin_hopkins()` and `method="martin-hopkins"` pathways now return `valid: false`, `ldl: null` and a reason. Use Sampson-NIH for a supported alternative.

Calculated LDL-C is an **estimate**, not a direct measurement. The accuracy depends on the population and lipid profile, particularly at low LDL-C and high triglycerides. This is an educational/research reference, not a validated diagnostic device.

**References:** [Sampson et al., JAMA Cardiology (2020)](https://doi.org/10.1001/jamacardio.2020.0013) · [2026 ACC/AHA Multisociety Dyslipidemia Guideline](https://doi.org/10.1161/CIR.0000000000001423).

## Python CLI

Python 3.10+; no dependencies for `ldl_calc.py` itself.

```bash
python ldl_calc.py single --total-cholesterol 200 --hdl 50 --triglycerides 150
python ldl_calc.py single --total-cholesterol 200 --hdl 50 --triglycerides 150 --method sampson
python ldl_calc.py batch --input sample.csv --output results.csv
```

Batch CSV headers: `total_cholesterol,hdl,triglycerides`, optionally `method` and other columns. Legacy calculations for MELD-Na, QTc, BMI, HbA1c, and APRI/FIB-4 remain in this file but require independent clinical validation before use in patient care.

## API and Docker

```bash
python -m pip install "fastapi>=0.115,<1" "uvicorn>=0.30,<1" "pydantic>=2,<3"
python cli.py serve --host 127.0.0.1 --port 8000
# UI: http://127.0.0.1:8000/
# Interactive API documentation: http://127.0.0.1:8000/docs
```

`POST /api/ldl` accepts:

```json
{"total_cholesterol":200,"hdl":50,"triglycerides":150,"method":"sampson"}
```

It returns estimated LDL-C, formula, validity flag, and reason when invalid. Existing legacy audit endpoints remain available; they demonstrate a mock supervisor rather than clinical decision support. The PHI regex guard is not a comprehensive de-identification solution; do not transmit patient data to those endpoints.

Docker can also run the API and browser UI:

```bash
docker build -t ldl-calculator .
docker run --rm -p 8000:8000 ldl-calculator
```

## Testing

```bash
python -m pip install pytest fastapi uvicorn pydantic
python -m pytest -q
node --test web/calculator.test.cjs  # Node.js 22+
node --check web/calculator.js
```

GitHub Actions runs Python tests across Python 3.10–3.12 and browser-engine tests with Node.js 22.

## Technology and license

Python 3.10+, FastAPI/Pydantic for the optional server, and dependency-free HTML/CSS/JavaScript for the static app. The browser app targets current Chromium, Firefox, and Safari versions. License: [MIT](LICENSE).
