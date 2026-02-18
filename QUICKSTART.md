# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Install Dependencies**
   ```bash
   cd d:\Codup\NPS-IntelliPlan
   pip install -r requirements.txt
   ```

2. **Start the Server**
   ```bash
   python main.py
   ```

   The server will start at `http://localhost:8000`

3. **Open the Dashboard**
   - Open your browser and navigate to: `http://localhost:8000`
   - Or directly open `frontend/index.html` in your browser

## Usage

### Basic Forecast

1. Enter your personal details:
   - Current Age (e.g., 30)
   - Retirement Age (e.g., 60)
   - Monthly Contribution (minimum ₹500)
   - Risk Profile (Conservative/Moderate/Aggressive)

2. Click **"Calculate Forecast"**

3. View results:
   - Projected retirement corpus
   - Expected monthly pension
   - Probability of success
   - Detailed breakdown

### Scenario Comparison

1. Fill in the form with your details
2. Click **"Compare Scenarios"**
3. View side-by-side comparison of all three risk profiles

## API Endpoints

The backend provides REST API endpoints:

- `POST /api/forecast` - Calculate retirement projection
- `POST /api/optimize` - Find required contribution for target pension
- `POST /api/compare` - Compare risk scenarios
- `GET /api/assumptions` - View modeling assumptions
- `GET /health` - Health check

View full API documentation at: `http://localhost:8000/docs`

## Demo Instructions

### For Hackathon Judges

1. **Quick Demo Scenario:**
   - Age: 30, Retirement: 60
   - Monthly Contribution: ₹5,000
   - Risk: Moderate
   - Click "Calculate Forecast"

   **Expected Results:**
   - Corpus: ~₹52-55 lakh
   - Monthly Pension: ~₹17,000-19,000
   - Probability distribution chart shows range of outcomes

2. **Scenario Comparison:**
   - Use same inputs
   - Click "Compare Scenarios"
   - See how Conservative vs Aggressive strategies differ

## Troubleshooting

**Server won't start:**
- Ensure Python 3.8+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`

**API errors:**
- Check server is running at `http://localhost:8000`
- Visit `/docs` to test API directly

**Charts not showing:**
- Ensure internet connection (Chart.js loads from CDN)
- Check browser console for JavaScript errors

## Project Structure

```
NPS-IntelliPlan/
├── backend/
│   ├── engine/          # Financial modeling core
│   │   ├── nps_config.py
│   │   ├── corpus_calculator.py
│   │   ├── monte_carlo.py
│   │   └── optimizer.py
│   └── api/             # FastAPI server
│       ├── main.py
│       └── routes.py
├── frontend/
│   ├── index.html       # Main dashboard
│   └── assets/
│       ├── styles.css
│       └── app.js
├── requirements.txt
└── main.py             # Server entry point
```

## Technical Highlights

- **Monte Carlo Simulation:** 10,000 iterations for probability-based projections
- **NPS Compliance:** Aligned with PFRDA regulations (40% mandatory annuity)
- **Inflation Adjustment:** Real vs nominal value differentiation
- **Contribution Optimization:** Binary search algorithm with Monte Carlo validation
- **Risk Modeling:** Three profiles based on historical NPS fund performance
