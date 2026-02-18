# NPS IntelliPlan

AI-Driven Probabilistic Retirement Corpus & Pension Forecasting Engine

**PFRDA Hackathon 2026 - Problem Statement 3**

## Overview

NPS IntelliPlan is a production-ready retirement forecasting platform that uses Monte Carlo simulation and predictive analytics to help National Pension System (NPS) subscribers make informed retirement planning decisions.

## Features

- **Probabilistic Forecasting**: Monte Carlo simulation with 10,000+ market scenarios
- **Contribution Optimization**: Calculate required contributions for target pension goals
- **Inflation Adjustment**: Real purchasing power projections
- **Scenario Comparison**: Compare conservative, moderate, and aggressive strategies
- **Interactive Dashboard**: User-friendly web interface with real-time calculations

## Technology Stack

- **Backend**: FastAPI (Python 3.8+)
- **Frontend**: HTML5, CSS3, JavaScript (Chart.js for visualization)
- **Computation**: NumPy, SciPy for financial modeling
- **Architecture**: RESTful API with modular design

## Quick Start

bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py


Visit `http://localhost:8000` in your browser.

## Project Structure


NPS-IntelliPlan/
├── backend/
│   ├── engine/          # Financial modeling core
│   ├── api/             # FastAPI endpoints
│   └── utils/           # Helper functions
├── frontend/
│   ├── index.html       # Main dashboard
│   └── assets/          # CSS, JS, images
├── docs/                # Technical documentation
└── tests/               # Unit and integration tests


## Team

- **Anshuman Tiwari** - Team Lead & Backend Architect
- **Amritansh Tiwari** - Frontend Developer
- **Satakshi Srivastava** - UI/UX Designer

## License

Developed for PFRDA Hackathon 2026
