# Transaction Risk Prioritization System

A rule-based transaction monitoring and risk prioritization platform built to identify potentially suspicious financial transactions, generate explainable risk alerts, and organize investigations into manageable cases.

## Overview

The Transaction Risk Prioritization System helps financial risk analysts identify and investigate potentially unusual transaction activity.

The system evaluates transactions using configurable risk rules, generates alerts with supporting evidence, assigns alerts to investigation cases, and provides a dashboard to monitor risk levels and analyst workloads.

This project uses synthetic financial data for development, testing, and evaluation. It does not process real customer or banking information.

## Key Features

- **Transaction Monitoring:** Analyze transaction activity using predefined risk rules.
- **Risk Detection:** Identify high-value transactions, velocity spikes, new-device activity, circular transfers, and dormant account reactivation.
- **Explainable Alerts:** Generate risk alerts with associated evidence and risk scores.
- **Case Management:** Group related alerts into investigation cases.
- **Analyst Assignment:** Assign investigation cases to analysts.
- **Investigation Workflow:** Start investigations, add comments, escalate cases, and record resolutions.
- **Dashboard:** View transaction statistics, alert distribution, case priorities, and analyst workloads.
- **Data Validation:** Validate identifiers, relationships, account balances, transfers, and account lifecycle events.
- **Detection Evaluation:** Compare detected transaction-rule pairs against labelled synthetic anomaly scenarios.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React.js, Vite, JavaScript |
| UI and Charts | CSS, Recharts, Lucide React |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Data Processing | Pandas, NumPy |
| Testing | Pytest, HTTPX |
| Version Control | Git, GitHub |

## System Architecture

```text
Synthetic Data Generation
          |
          v
Data Validation
          |
          v
PostgreSQL Database
          |
          v
Risk Detection Engine
          |
          v
Risk Alerts and Evidence
          |
          v
Investigation Case Management
          |
          v
FastAPI REST API
          |
          v
React Dashboard
```

## Risk Detection Rules

The system implements five primary risk detection rules:

1. **HIGH_VALUE:** Identifies unusually large transactions.
2. **VELOCITY_SPIKE:** Detects unusually frequent transaction activity.
3. **NEW_DEVICE:** Identifies transactions originating from newly observed devices.
4. **CIRCULAR_TRANSFER:** Detects linked transfers that form circular transaction patterns.
5. **DORMANT_REACTIVATION:** Identifies activity on previously inactive accounts.

Alerts are potential indicators of suspicious activity and should not be interpreted as proof of fraud.

## Dataset

The project includes a starter synthetic dataset in the `data/` directory.

Additional full-scale generated datasets are maintained locally and excluded from the Git repository to avoid unnecessary repository size.

The revised full-scale dataset (`data_full_v2`) used during evaluation contains:

| Dataset component | Records |
|---|---:|
| Customers | 5,000 |
| KYC Profiles | 5,000 |
| Accounts | 7,000 |
| Account Ownership Records | 7,000 |
| Merchants | 15 |
| Devices | 9,977 |
| Transactions | 100,216 |
| Transfers | 103 |
| Labelled Anomaly Scenarios | 16 |
| Risk Rules | 5 |
| Generated Alerts | 28 |

The dataset contains deliberately injected anomaly scenarios for evaluating detection performance.

## Detection Evaluation

The revised detection evaluation produced the following results:

| Metric | Result |
|---|---:|
| True Positives | 16 |
| False Positives | 12 |
| False Negatives | 0 |
| Precision | 57.14% |
| Recall | 100.00% |
| F1-Score | 72.73% |

### Interpretation

- The system detected all 16 labelled anomaly transaction-rule pairs.
- No labelled anomaly pair was missed.
- Some additional alerts did not match the deliberately injected ground-truth labels.
- These unmatched alerts are counted as false positives for this comparison, but they are not necessarily confirmed legitimate transactions.

The evaluation is based on a limited synthetic ground-truth dataset and should not be treated as a measure of real-world fraud detection performance.

Detailed evaluation outputs are available in the `evaluation/` directory.

## Project Structure

```text
risk-prioritization-system/
|
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- database.py
|   |   |-- main.py
|   |
|   |-- migrations/
|   |-- tests/
|   |-- requirements.txt
|
|-- data/
|
|-- evaluation/
|   |-- calculate_metrics.py
|   |-- evaluate_detection.py
|   |-- detection_results.csv
|   |-- metrics_summary.csv
|
|-- frontend/
|   |-- src/
|   |-- public/
|   |-- package.json
|
|-- generator/
|   |-- generate_customers.py
|   |-- generate_accounts.py
|   |-- generate_transactions.py
|   |-- generate_transfers.py
|   |-- inject_anomalies.py
|   |-- import_to_database.py
|
|-- validation/
|   |-- validate_ids.py
|   |-- validate_balances.py
|   |-- validate_relationships.py
|   |-- validate_transfers.py
|   |-- validate_lifecycle.py
|
|-- .env.example
|-- .gitignore
|-- alembic.ini
|-- README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- PostgreSQL
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/risk-prioritization-system.git
cd risk-prioritization-system
```

### 2. Set Up the Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables

Create a private `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Update the `.env` file with your local PostgreSQL credentials:

```env
APP_NAME=Transaction Risk Prioritization System
DB_USER=postgres
DB_PASSWORD=your_local_database_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=risk_analytics
```

Never commit your private `.env` file or database credentials.

### 4. Create the PostgreSQL Database

Create a PostgreSQL database named:

```sql
CREATE DATABASE risk_analytics;
```

Apply database migrations from the project root:

```powershell
alembic upgrade head
```

### 5. Start the Backend

From the project root:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend:

- API: http://127.0.0.1:8000
- Swagger documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### 6. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local Vite URL displayed in your terminal.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend welcome endpoint |
| GET | `/health` | Health check |
| GET | `/api/dashboard` | Dashboard statistics |
| GET | `/api/alerts` | List risk alerts |
| GET | `/api/cases` | List investigation cases |
| GET | `/api/cases/{case_id}` | Get case details |
| GET | `/api/analysts` | List analysts and workloads |
| POST | `/api/cases/{case_id}/start` | Start an investigation |
| POST | `/api/cases/{case_id}/comments` | Add an investigation comment |
| POST | `/api/cases/{case_id}/escalate` | Escalate a case |
| POST | `/api/cases/{case_id}/resolve` | Resolve a case |

Full API documentation is available through FastAPI Swagger UI at `/docs`.

## Testing

Run backend API tests from the project root:

```powershell
python -m pytest backend/tests -v
```

Build the frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## Limitations

- The project uses synthetic transaction data rather than real banking data.
- Detection rules are predefined and rule-based.
- Evaluation results depend on the available labelled anomaly scenarios.
- An alert indicates a potential risk and requires analyst investigation.
- The project is an academic and portfolio demonstration, not a production banking compliance platform.

## Future Improvements

- Add configurable risk thresholds.
- Improve new-device detection to reduce false positives.
- Introduce advanced anomaly detection and machine learning models.
- Add authentication and stronger role-based access controls.
- Improve investigation analytics and reporting.
- Add automated monitoring and alert notifications.

## Author

**Nikhitha Janapana**

GitHub: https://github.com/nikhitha178

Project: Transaction Risk Prioritization System
