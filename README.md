# SpendWise

Local desktop personal-expense tracker built with Python and CustomTkinter.

## Overview

SpendWise allows users to log income and expenses, organize them into categories, set monthly budgets with alerts, visualize spending trends, and use local machine learning for category suggestions and next-month spending forecasts.

## Project Structure

```text
SpendWise/
├── .github/workflows/ci.yml   # GitHub Actions CI pipeline
├── docs/                      # MkDocs documentation
├── scripts/
│   └── generate_data.py       # Synthetic data generator script
├── src/spendwise/
│   ├── main.py                # Application entry point
│   ├── models.py              # Domain dataclasses
│   ├── paths.py               # platformdirs path helpers
│   ├── ui/                    # CustomTkinter GUI views
│   ├── services/              # Business logic layer
│   ├── repositories/          # SQLite database access & schema
│   └── ml/                    # Predictor interfaces & models
├── tests/                     # Unit tests (services, repositories, ml)
├── .pre-commit-config.yaml
├── pyproject.toml
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Running the App

```bash
python -m spendwise.main
```

## Running Tests & Linter

```bash
ruff check .
ruff format --check .
pytest
```
