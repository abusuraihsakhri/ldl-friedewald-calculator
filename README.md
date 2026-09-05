# LDL Friedewald & Martin-Hopkins Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Language:** Python 3.10+  
> **Dependencies:** Stdlib only (core calculator)

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)

</div>

---

## 📖 What It Does

A clinical calculator for LDL cholesterol using two validated formulas:

- **Friedewald Formula:** LDL = Total Cholesterol - HDL - (Triglycerides / 5)
- **Martin-Hopkins Formula:** LDL = Total Cholesterol - HDL - (Triglycerides / adjustable_factor)

The Friedewald formula is valid only when triglycerides ≤ 400 mg/dL. The Martin-Hopkins formula uses an adjustable factor for more accurate results at higher triglyceride levels.

Also supports additional clinical calculations: MELD-Na, QTc (Bazett), BMI z-score, HbA1c conversion, and APRI/FIB-4.

---

## ⚙️ Key Features

### Core LDL Calculations
- **`calculate_friedewald(tc, hdl, tg)`** — Friedewald formula with triglyceride validity check
- **`calculate_martin_hopkins(tc, hdl, tg)`** — Martin-Hopkins with adjustable factor
- **`calculate_ldl(tc, hdl, tg, method)`** — Unified interface for both methods

### Additional Clinical Calculations
- **`calculate_meld_na()`** — MELD-Na score for liver disease severity
- **`calculate_qtc()`** — QTc interval (Bazett's formula)
- **`calculate_bmi_z()`** — BMI with z-score approximation
- **`convert_hba1c()`** — HbA1c ↔ estimated average glucose
- **`calculate_apri_fib4()`** — APRI and FIB-4 liver fibrosis scores

### Batch Processing
- **`process_csv(input, output)`** — Process CSV files with lab data
- **`assess_row(row)`** — Auto-detect calculation type from input fields

---

## 📐 Mathematical Formulations

### Friedewald Formula
```
LDL = Total Cholesterol - HDL - (Triglycerides / 5)
```
Valid for triglycerides ≤ 400 mg/dL. All values in mg/dL.

### Martin-Hopkins Formula
```
LDL = Total Cholesterol - HDL - (Triglycerides / adjustable_factor)
```
Uses adjustable factor based on triglyceride level:
- TG < 150: factor = 5.0
- TG < 200: factor = 4.5
- TG < 300: factor = 4.0
- TG < 400: factor = 3.5
- TG ≥ 400: factor = 3.0

---

## 💻 Usage

### Single Calculation
```bash
# Friedewald (default)
python ldl_calc.py single --total-cholesterol 200 --hdl 50 --triglycerides 150

# Martin-Hopkins
python ldl_calc.py single --total-cholesterol 200 --hdl 50 --triglycerides 150 --method martin-hopkins

# JSON input
python ldl_calc.py single --json '{"total_cholesterol": 200, "hdl": 50, "triglycerides": 150}'
```

### Batch CSV Processing
```bash
python ldl_calc.py batch --input lab_results.csv --output results.csv
```

### CSV Input Format
| Field | Description | Unit |
|:------|:------------|:-----|
| total_cholesterol | Total cholesterol | mg/dL |
| hdl | HDL cholesterol | mg/dL |
| triglycerides | Triglycerides | mg/dL |

---

## 🧪 Testing

Run the full test suite:
```bash
pytest -v
```

Run only core calculator tests:
```bash
pytest test_ldl_calc.py -v
```

---

## 🐳 Docker Deployment

```bash
docker build -t ldl-friedewald-calculator .
docker run -p 8000:8000 ldl-friedewald-calculator
```

Or with docker-compose:
```bash
docker-compose up
```

---

## 🛡️ Security

- Input validation on all numeric parameters
- Path traversal protection for file operations
- File path validation prevents null byte injection
- CSV processing validates file existence and prevents self-overwrite

---

## 📁 Project Structure

```
ldl-friedewald-calculator/
├── ldl_calc.py           # Core calculator module
├── cli.py                # CLI interface (enterprise features)
├── enrichment.py         # Enrichment feature suite
├── simulator.py          # High-throughput simulation
├── test_ldl_calc.py      # Core calculator tests
├── tests/                # Additional test suites
│   ├── test_enrichment.py
│   └── test_ldl_friedewald_calculator.py
├── agents/               # Enterprise agent framework
│   ├── base.py           # Security, PHI guard, audit trail
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized calculation workers
│   └── api.py            # FastAPI REST endpoints
├── web/index.html        # Web operations console
├── Dockerfile
├── docker-compose.yml
├── sample.csv            # Example input data
└── benchmark_dataset.json
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
