"""
Enhanced Corpus Calculator

Full-featured retirement projection engine with salary step-up,
employer contributions, tax benefits, lifecycle rebalancing,
year-by-year breakdown, and inflation-adjusted values.
"""

import math
from typing import Dict, List, Optional, Tuple
from backend.engine.nps_config import (
    NPS_MANDATORY_ANNUITY_PERCENT,
    NPS_MAX_LUMPSUM_WITHDRAWAL,
    EXPECTED_RETURNS,
    ANNUITY_RATE_SINGLE_LIFE,
    ANNUITY_RATE_JOINT_LIFE,
    ANNUITY_PROVIDERS,
    DEFAULT_INFLATION_RATE,
    TAX_SLABS_OLD_REGIME,
    TAX_SLABS_NEW_REGIME,
    NPS_80CCD1_LIMIT,
    NPS_80CCD1B_ADDITIONAL,
    NPS_80CCD2_EMPLOYER_LIMIT,
    ASSET_ALLOCATION,
    LIFECYCLE_EQUITY_CAP
)


def calculate_retirement_projection(
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    risk_profile: str = "moderate",
    inflation_rate: float = DEFAULT_INFLATION_RATE,
    initial_balance: float = 0.0,
    annual_step_up: float = 0.0,
    employer_contribution: float = 0.0,
    annuity_provider: str = "LIC"
) -> Dict:
    """
    Calculate deterministic retirement projection.

    Args:
        current_age: Current age
        retirement_age: Target retirement age
        monthly_contribution: Monthly employee contribution (₹)
        risk_profile: conservative / moderate / aggressive
        inflation_rate: Expected annual inflation (%)
        initial_balance: Current NPS Tier-I balance (₹)
        annual_step_up: Annual increase in contribution (%)
        employer_contribution: Monthly employer contribution (₹)
        annuity_provider: LIC / SBI / HDFC / ICICI

    Returns:
        Comprehensive projection dictionary
    """
    years = retirement_age - current_age
    if years <= 0:
        raise ValueError("Retirement age must be greater than current age")

    expected_return_rate = EXPECTED_RETURNS[risk_profile]["mean"]
    monthly_rate = (expected_return_rate / 100) / 12

    # Year-by-year projection
    corpus = initial_balance
    current_contrib = monthly_contribution
    current_employer = employer_contribution
    total_employee_contributions = 0.0
    total_employer_contributions = 0.0
    yearly_breakdown = []

    for year in range(years):
        year_start_corpus = corpus
        year_contributions = 0.0
        year_employer = 0.0

        for month in range(12):
            corpus = corpus * (1 + monthly_rate) + current_contrib + current_employer
            year_contributions += current_contrib
            year_employer += current_employer

        total_employee_contributions += year_contributions
        total_employer_contributions += year_employer

        yearly_breakdown.append({
            "year": year + 1,
            "age": current_age + year + 1,
            "start_corpus": round(year_start_corpus, 2),
            "end_corpus": round(corpus, 2),
            "employee_contribution": round(year_contributions, 2),
            "employer_contribution": round(year_employer, 2),
            "growth": round(corpus - year_start_corpus - year_contributions - year_employer, 2),
            "monthly_contribution": round(current_contrib, 2)
        })

        # Apply annual step-up
        if annual_step_up > 0:
            current_contrib *= (1 + annual_step_up / 100)
            current_employer *= (1 + annual_step_up / 100)

    nominal_corpus = corpus
    total_contributions = total_employee_contributions + total_employer_contributions

    # Inflation-adjusted values
    real_corpus = calculate_inflation_adjusted_value(
        nominal_corpus, inflation_rate, years
    )

    # NPS Withdrawal split
    lumpsum_withdrawal = nominal_corpus * (NPS_MAX_LUMPSUM_WITHDRAWAL / 100)
    annuity_purchase_amount = nominal_corpus * (NPS_MANDATORY_ANNUITY_PERCENT / 100)

    # Pension calculation
    monthly_pension, annuity_rate = estimate_monthly_pension(
        nominal_corpus, annuity_provider=annuity_provider
    )

    # Growth multiplier
    growth_multiplier = nominal_corpus / total_contributions if total_contributions > 0 else 0

    return {
        "nominal_corpus": round(nominal_corpus, 2),
        "real_corpus": round(real_corpus, 2),
        "monthly_pension_nominal": round(monthly_pension, 2),
        "total_contributions": round(total_contributions, 2),
        "total_employee_contributions": round(total_employee_contributions, 2),
        "total_employer_contributions": round(total_employer_contributions, 2),
        "growth_amount": round(nominal_corpus - total_contributions - initial_balance, 2),
        "growth_multiplier": round(growth_multiplier, 2),
        "expected_return_rate": expected_return_rate,
        "years_invested": years,
        "lumpsum_withdrawal": round(lumpsum_withdrawal, 2),
        "annuity_purchase_amount": round(annuity_purchase_amount, 2),
        "annuity_rate_used": annuity_rate,
        "annuity_provider": annuity_provider,
        "yearly_breakdown": yearly_breakdown
    }


def calculate_tax_benefits(
    annual_contribution: float,
    annual_employer_contribution: float = 0.0,
    annual_salary: float = 0.0,
    tax_regime: str = "old"
) -> Dict:
    """
    Calculate NPS tax benefits under Section 80CCD.

    Args:
        annual_contribution: Employee annual NPS contribution
        annual_employer_contribution: Employer annual contribution
        annual_salary: Annual basic salary (for employer limit calculation)
        tax_regime: 'old' or 'new'

    Returns:
        Breakdown of tax deductions and savings
    """
    slabs = TAX_SLABS_OLD_REGIME if tax_regime == "old" else TAX_SLABS_NEW_REGIME

    # Section 80CCD(1): Employee contribution — up to 10% of salary, within 80C limit
    sec_80ccd1 = min(annual_contribution, NPS_80CCD1_LIMIT)

    # Section 80CCD(1B): Additional exclusive NPS deduction
    remaining = max(0, annual_contribution - sec_80ccd1)
    sec_80ccd1b = min(remaining + min(annual_contribution, NPS_80CCD1B_ADDITIONAL), NPS_80CCD1B_ADDITIONAL)

    # Section 80CCD(2): Employer contribution — up to 10% of basic
    employer_limit = annual_salary * NPS_80CCD2_EMPLOYER_LIMIT if annual_salary > 0 else float('inf')
    sec_80ccd2 = min(annual_employer_contribution, employer_limit)

    total_deduction = sec_80ccd1 + sec_80ccd1b + sec_80ccd2

    # Estimate tax saved
    tax_saved = estimate_tax_saved(total_deduction, slabs)

    return {
        "sec_80ccd1": round(sec_80ccd1, 2),
        "sec_80ccd1b": round(sec_80ccd1b, 2),
        "sec_80ccd2": round(sec_80ccd2, 2),
        "total_deduction": round(total_deduction, 2),
        "estimated_tax_saved": round(tax_saved, 2),
        "tax_regime": tax_regime,
        "effective_cost_reduction": round(
            (tax_saved / (annual_contribution + annual_employer_contribution)) * 100, 1
        ) if (annual_contribution + annual_employer_contribution) > 0 else 0
    }


def estimate_tax_saved(deduction: float, slabs: list) -> float:
    """Estimate marginal tax saved from deduction."""
    # Find the marginal rate
    marginal_rate = 0
    for limit, rate in slabs:
        marginal_rate = rate
        if deduction <= limit:
            break
    # Simplified: assume deduction applies at marginal rate + 4% cess
    return deduction * marginal_rate * 1.04


def estimate_monthly_pension(
    total_corpus: float,
    annuity_provider: str = "LIC"
) -> Tuple[float, float]:
    """
    Estimate monthly pension from NPS corpus.

    Uses provider-specific annuity rates.
    """
    annuity_amount = total_corpus * (NPS_MANDATORY_ANNUITY_PERCENT / 100)

    provider = ANNUITY_PROVIDERS.get(annuity_provider, ANNUITY_PROVIDERS["LIC"])
    annuity_rate = provider["single"]

    annual_pension = annuity_amount * (annuity_rate / 100)
    monthly_pension = annual_pension / 12

    return monthly_pension, annuity_rate


def calculate_inflation_adjusted_value(
    future_value: float,
    inflation_rate: float,
    years: int
) -> float:
    """Convert future value to present-day purchasing power."""
    if inflation_rate <= 0 or years <= 0:
        return future_value
    return future_value / ((1 + inflation_rate / 100) ** years)


def calculate_inflation_erosion(
    amount: float = 100000,
    inflation_rate: float = DEFAULT_INFLATION_RATE,
    years: int = 30
) -> List[Dict]:
    """Show how inflation erodes purchasing power over time."""
    timeline = []
    for y in range(0, years + 1, max(1, years // 10)):
        real_value = amount / ((1 + inflation_rate / 100) ** y)
        timeline.append({
            "year": y,
            "nominal": amount,
            "real_value": round(real_value, 2),
            "purchasing_power_pct": round((real_value / amount) * 100, 1)
        })
    return timeline


def compare_scenarios(
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    inflation_rate: float = DEFAULT_INFLATION_RATE,
    initial_balance: float = 0.0,
    annual_step_up: float = 0.0,
    employer_contribution: float = 0.0
) -> Dict:
    """Compare all risk profiles side by side."""
    comparison = {}
    for profile in ["conservative", "moderate", "aggressive"]:
        comparison[profile] = calculate_retirement_projection(
            current_age=current_age,
            retirement_age=retirement_age,
            monthly_contribution=monthly_contribution,
            risk_profile=profile,
            inflation_rate=inflation_rate,
            initial_balance=initial_balance,
            annual_step_up=annual_step_up,
            employer_contribution=employer_contribution
        )
    return comparison


def calculate_sensitivity(
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    risk_profile: str = "moderate",
    inflation_rate: float = DEFAULT_INFLATION_RATE,
    initial_balance: float = 0.0
) -> Dict:
    """
    Sensitivity analysis: how much does each variable affect the outcome?
    Returns impact of ±10% change in each variable.
    """
    base = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution,
        risk_profile, inflation_rate, initial_balance
    )
    base_corpus = base["nominal_corpus"]

    sensitivities = []
    
    # Test contribution sensitivity
    high = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution * 1.1,
        risk_profile, inflation_rate, initial_balance
    )["nominal_corpus"]
    low = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution * 0.9,
        risk_profile, inflation_rate, initial_balance
    )["nominal_corpus"]
    sensitivities.append({
        "variable": "Monthly Contribution",
        "low_value": round(low, 2),
        "base_value": round(base_corpus, 2),
        "high_value": round(high, 2),
        "impact_pct": round(((high - low) / base_corpus) * 100, 1)
    })

    # Test retirement age sensitivity
    if retirement_age + 2 <= 75:
        high = calculate_retirement_projection(
            current_age, retirement_age + 2, monthly_contribution,
            risk_profile, inflation_rate, initial_balance
        )["nominal_corpus"]
    else:
        high = base_corpus
    low = calculate_retirement_projection(
        current_age, max(current_age + 1, retirement_age - 2), monthly_contribution,
        risk_profile, inflation_rate, initial_balance
    )["nominal_corpus"]
    sensitivities.append({
        "variable": "Retirement Age (±2 yrs)",
        "low_value": round(low, 2),
        "base_value": round(base_corpus, 2),
        "high_value": round(high, 2),
        "impact_pct": round(((high - low) / base_corpus) * 100, 1)
    })

    # Test inflation sensitivity
    high_inf = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution,
        risk_profile, inflation_rate * 1.2, initial_balance
    )["real_corpus"]
    low_inf = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution,
        risk_profile, inflation_rate * 0.8, initial_balance
    )["real_corpus"]
    base_real = base["real_corpus"]
    sensitivities.append({
        "variable": "Inflation Rate (±20%)",
        "low_value": round(high_inf, 2),  # higher inflation = lower real value
        "base_value": round(base_real, 2),
        "high_value": round(low_inf, 2),
        "impact_pct": round(((low_inf - high_inf) / base_real) * 100, 1)
    })

    return {
        "base_corpus": round(base_corpus, 2),
        "sensitivities": sensitivities
    }
