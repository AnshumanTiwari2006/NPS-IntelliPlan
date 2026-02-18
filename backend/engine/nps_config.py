"""
NPS-specific Configuration Constants

Complete configuration aligned with National Pension System (NPS)
regulatory framework, market assumptions, and tax rules.
"""

# ── NPS Account Configuration ────────────────────────────────
NPS_MIN_CONTRIBUTION_MONTHLY = 500
NPS_MIN_CONTRIBUTION_ANNUAL = 6000
NPS_DEFAULT_RETIREMENT_AGE = 60
NPS_MIN_ENTRY_AGE = 18
NPS_MAX_ENTRY_AGE = 70

# ── Withdrawal & Annuity Rules (PFRDA) ───────────────────────
NPS_MANDATORY_ANNUITY_PERCENT = 40
NPS_MAX_LUMPSUM_WITHDRAWAL = 60

# ── Asset Allocation (Auto Choice / Active Choice) ───────────
ASSET_ALLOCATION = {
    "conservative": {"equity": 25, "corporate_bonds": 40, "govt_securities": 35},
    "moderate":     {"equity": 50, "corporate_bonds": 30, "govt_securities": 20},
    "aggressive":   {"equity": 75, "corporate_bonds": 15, "govt_securities": 10}
}

# ── Historical Return Assumptions (NPS 2009-2024) ────────────
EXPECTED_RETURNS = {
    "conservative": {"mean": 9.0,  "std_dev": 5.0},
    "moderate":     {"mean": 11.0, "std_dev": 8.0},
    "aggressive":   {"mean": 13.0, "std_dev": 12.0}
}

# ── Inflation ────────────────────────────────────────────────
DEFAULT_INFLATION_RATE = 6.0
INFLATION_STD_DEV = 1.5

# ── Annuity Rates (current market) ──────────────────────────
ANNUITY_RATE_SINGLE_LIFE = 6.5
ANNUITY_RATE_JOINT_LIFE = 6.0

ANNUITY_PROVIDERS = {
    "LIC":  {"single": 6.5, "joint": 6.0, "name": "LIC of India"},
    "SBI":  {"single": 6.3, "joint": 5.8, "name": "SBI Life"},
    "HDFC": {"single": 6.1, "joint": 5.6, "name": "HDFC Life"},
    "ICICI":{"single": 6.4, "joint": 5.9, "name": "ICICI Prudential"}
}

# ── Monte Carlo Parameters ───────────────────────────────────
DEFAULT_SIMULATION_ITERATIONS = 10000
RANDOM_SEED = 42

# ── Tax Benefit Rules (FY 2025-26) ──────────────────────────
TAX_SLABS_OLD_REGIME = [
    (250000,   0.00),
    (500000,   0.05),
    (1000000,  0.20),
    (float('inf'), 0.30)
]

TAX_SLABS_NEW_REGIME = [
    (300000,   0.00),
    (700000,   0.05),
    (1000000,  0.10),
    (1200000,  0.15),
    (1500000,  0.20),
    (float('inf'), 0.30)
]

NPS_80CCD1_LIMIT = 150000       # Sec 80CCD(1) — included in 80C limit
NPS_80CCD1B_ADDITIONAL = 50000  # Sec 80CCD(1B) — exclusive NPS deduction
NPS_80CCD2_EMPLOYER_LIMIT = 0.10  # 10% of basic salary
NPS_80C_LIMIT = 150000

# ── Lifecycle Auto-Rebalancing ───────────────────────────────
# Maximum equity allocation reduces by age
LIFECYCLE_EQUITY_CAP = {
    "aggressive": {
        "max_equity": 75,
        "glide_start_age": 35,
        "glide_end_age": 55,
        "floor_equity": 15
    },
    "moderate": {
        "max_equity": 50,
        "glide_start_age": 36,
        "glide_end_age": 55,
        "floor_equity": 10
    },
    "conservative": {
        "max_equity": 25,
        "glide_start_age": 36,
        "glide_end_age": 55,
        "floor_equity": 5
    }
}

# ── Partial Withdrawal Rules ────────────────────────────────
# NPS allows up to 25% withdrawal after 3 years for specific purposes
PARTIAL_WITHDRAWAL_MAX_PERCENT = 25
PARTIAL_WITHDRAWAL_MIN_YEARS = 3
PARTIAL_WITHDRAWAL_MAX_COUNT = 3
PARTIAL_WITHDRAWAL_PURPOSES = [
    "Children's Higher Education",
    "Children's Marriage",
    "Treatment of Critical Illness",
    "Purchase/Construction of House",
    "Skill Development/Re-skilling"
]
