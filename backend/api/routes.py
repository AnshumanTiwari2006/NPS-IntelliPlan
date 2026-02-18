"""
API Routes — NPS IntelliPlan

Comprehensive REST API with forecast, comparison, optimization,
tax benefits, sensitivity analysis, Gemini AI advice, and more.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from backend.engine.corpus_calculator import (
    calculate_retirement_projection,
    compare_scenarios,
    calculate_tax_benefits,
    calculate_sensitivity,
    calculate_inflation_erosion
)
from backend.engine.monte_carlo import (
    MonteCarloSimulator,
    run_scenario_comparison
)
from backend.engine.optimizer import ContributionOptimizer
from backend.engine.gemini_ai import (
    generate_retirement_advice,
    generate_scenario_narrative,
    generate_risk_assessment,
    generate_goal_gap_analysis,
    generate_what_if_analysis,
    generate_peer_comparison
)
from backend.engine.nps_config import (
    NPS_MIN_ENTRY_AGE,
    NPS_MAX_ENTRY_AGE,
    NPS_MIN_CONTRIBUTION_MONTHLY,
    EXPECTED_RETURNS,
    ANNUITY_PROVIDERS,
    ASSET_ALLOCATION,
    DEFAULT_INFLATION_RATE,
    PARTIAL_WITHDRAWAL_PURPOSES
)

router = APIRouter()


# ── Request Models ───────────────────────────────────────────

class ForecastRequest(BaseModel):
    current_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=NPS_MAX_ENTRY_AGE)
    retirement_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=100)
    monthly_contribution: float = Field(..., ge=NPS_MIN_CONTRIBUTION_MONTHLY)
    risk_profile: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    inflation_rate: float = Field(default=6.0, ge=0, le=20)
    initial_balance: float = Field(default=0, ge=0)
    annual_step_up: float = Field(default=0, ge=0, le=50)
    employer_contribution: float = Field(default=0, ge=0)
    annuity_provider: str = Field(default="LIC")
    use_monte_carlo: bool = Field(default=True)

    @field_validator('retirement_age')
    @classmethod
    def check_retirement(cls, v, info):
        if 'current_age' in info.data and v <= info.data['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v


class ComparisonRequest(BaseModel):
    current_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=NPS_MAX_ENTRY_AGE)
    retirement_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=100)
    monthly_contribution: float = Field(..., ge=NPS_MIN_CONTRIBUTION_MONTHLY)
    inflation_rate: float = Field(default=6.0, ge=0, le=20)
    initial_balance: float = Field(default=0, ge=0)
    annual_step_up: float = Field(default=0, ge=0, le=50)
    employer_contribution: float = Field(default=0, ge=0)
    use_monte_carlo: bool = Field(default=True)


class OptimizationRequest(BaseModel):
    current_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=NPS_MAX_ENTRY_AGE)
    retirement_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=100)
    target_monthly_pension: float = Field(..., gt=0)
    risk_profile: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")
    target_probability: float = Field(default=70.0, ge=50, le=95)
    initial_balance: float = Field(default=0, ge=0)

    @field_validator('retirement_age')
    @classmethod
    def check_retirement(cls, v, info):
        if 'current_age' in info.data and v <= info.data['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v


class TaxRequest(BaseModel):
    annual_contribution: float = Field(..., gt=0)
    annual_employer_contribution: float = Field(default=0, ge=0)
    annual_salary: float = Field(default=0, ge=0)
    tax_regime: str = Field(default="old", pattern="^(old|new)$")


class RiskAssessmentRequest(BaseModel):
    age: int = Field(..., ge=18, le=70)
    investment_horizon: int = Field(..., ge=1, le=50)
    income_stability: str = Field(default="stable")
    risk_tolerance: str = Field(default="moderate")
    existing_savings: str = Field(default="moderate")
    dependents: int = Field(default=1, ge=0)


class GoalGapRequest(BaseModel):
    current_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=NPS_MAX_ENTRY_AGE)
    retirement_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=100)
    monthly_contribution: float = Field(..., ge=NPS_MIN_CONTRIBUTION_MONTHLY)
    risk_profile: str = Field(default="moderate")
    inflation_rate: float = Field(default=6.0)
    initial_balance: float = Field(default=0, ge=0)
    annual_step_up: float = Field(default=0, ge=0)
    employer_contribution: float = Field(default=0, ge=0)
    target_monthly_pension: float = Field(..., gt=0)


class WhatIfRequest(BaseModel):
    current_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=NPS_MAX_ENTRY_AGE)
    retirement_age: int = Field(..., ge=NPS_MIN_ENTRY_AGE, le=100)
    monthly_contribution: float = Field(..., ge=NPS_MIN_CONTRIBUTION_MONTHLY)
    risk_profile: str = Field(default="moderate")
    inflation_rate: float = Field(default=6.0)
    initial_balance: float = Field(default=0, ge=0)
    annual_step_up: float = Field(default=0, ge=0)
    employer_contribution: float = Field(default=0, ge=0)


# ── Endpoints ────────────────────────────────────────────────

@router.post("/forecast")
async def forecast(req: ForecastRequest):
    """Run retirement forecast with optional Monte Carlo simulation."""
    try:
        det = calculate_retirement_projection(
            current_age=req.current_age,
            retirement_age=req.retirement_age,
            monthly_contribution=req.monthly_contribution,
            risk_profile=req.risk_profile,
            inflation_rate=req.inflation_rate,
            initial_balance=req.initial_balance,
            annual_step_up=req.annual_step_up,
            employer_contribution=req.employer_contribution,
            annuity_provider=req.annuity_provider
        )

        result = {
            "method": "deterministic",
            "deterministic_projection": det,
            "asset_allocation": ASSET_ALLOCATION.get(req.risk_profile, {})
        }

        if req.use_monte_carlo:
            sim = MonteCarloSimulator()
            mc = sim.simulate_retirement_corpus(
                current_age=req.current_age,
                retirement_age=req.retirement_age,
                monthly_contribution=req.monthly_contribution,
                risk_profile=req.risk_profile,
                initial_balance=req.initial_balance
            )
            result["method"] = "monte_carlo"
            result["simulation_results"] = mc

        # Generate AI advice
        advice_data = {
            "current_age": req.current_age,
            "retirement_age": req.retirement_age,
            "monthly_contribution": req.monthly_contribution,
            "risk_profile": req.risk_profile,
            "nominal_corpus": det["nominal_corpus"],
            "monthly_pension": det["monthly_pension_nominal"],
            "real_corpus": det["real_corpus"],
            "growth_multiplier": det["growth_multiplier"],
            "total_contributions": det["total_contributions"],
            "employer_contribution": req.employer_contribution
        }
        result["ai_advice"] = generate_retirement_advice(advice_data)
        result["narrative"] = generate_scenario_narrative(det)

        return result

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare")
async def compare(req: ComparisonRequest):
    """Compare all risk profiles side by side."""
    try:
        if req.use_monte_carlo:
            scenarios = run_scenario_comparison(
                current_age=req.current_age,
                retirement_age=req.retirement_age,
                monthly_contribution=req.monthly_contribution,
                initial_balance=req.initial_balance
            )
        else:
            scenarios = compare_scenarios(
                current_age=req.current_age,
                retirement_age=req.retirement_age,
                monthly_contribution=req.monthly_contribution,
                inflation_rate=req.inflation_rate,
                initial_balance=req.initial_balance,
                annual_step_up=req.annual_step_up,
                employer_contribution=req.employer_contribution
            )
        
        return {
            "method": "monte_carlo" if req.use_monte_carlo else "deterministic",
            "scenarios": scenarios
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize")
async def optimize(req: OptimizationRequest):
    """Find required contribution for target pension."""
    try:
        optimizer = ContributionOptimizer()
        return optimizer.find_required_contribution(
            current_age=req.current_age,
            retirement_age=req.retirement_age,
            target_monthly_pension=req.target_monthly_pension,
            risk_profile=req.risk_profile,
            target_probability=req.target_probability,
            initial_balance=req.initial_balance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tax-benefits")
async def tax_benefits(req: TaxRequest):
    """Calculate NPS tax benefits under 80CCD."""
    try:
        return calculate_tax_benefits(
            annual_contribution=req.annual_contribution,
            annual_employer_contribution=req.annual_employer_contribution,
            annual_salary=req.annual_salary,
            tax_regime=req.tax_regime
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sensitivity")
async def sensitivity(req: WhatIfRequest):
    """Sensitivity analysis — impact of changing each variable."""
    try:
        return calculate_sensitivity(
            current_age=req.current_age,
            retirement_age=req.retirement_age,
            monthly_contribution=req.monthly_contribution,
            risk_profile=req.risk_profile,
            inflation_rate=req.inflation_rate,
            initial_balance=req.initial_balance
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risk-assessment")
async def risk_assessment(req: RiskAssessmentRequest):
    """AI-powered risk profile assessment."""
    try:
        return generate_risk_assessment(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/goal-gap")
async def goal_gap(req: GoalGapRequest):
    """Analyze gap between current plan and target pension."""
    try:
        projection = calculate_retirement_projection(
            current_age=req.current_age,
            retirement_age=req.retirement_age,
            monthly_contribution=req.monthly_contribution,
            risk_profile=req.risk_profile,
            inflation_rate=req.inflation_rate,
            initial_balance=req.initial_balance,
            annual_step_up=req.annual_step_up,
            employer_contribution=req.employer_contribution
        )
        return generate_goal_gap_analysis(projection, req.target_monthly_pension)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/what-if")
async def what_if(req: WhatIfRequest):
    """What-if scenario analysis."""
    try:
        base = calculate_retirement_projection(
            current_age=req.current_age,
            retirement_age=req.retirement_age,
            monthly_contribution=req.monthly_contribution,
            risk_profile=req.risk_profile,
            inflation_rate=req.inflation_rate,
            initial_balance=req.initial_balance,
            annual_step_up=req.annual_step_up,
            employer_contribution=req.employer_contribution
        )
        scenarios = generate_what_if_analysis(
            base, req.current_age, req.retirement_age,
            req.monthly_contribution, req.risk_profile,
            req.inflation_rate, req.initial_balance,
            req.annual_step_up, req.employer_contribution
        )
        return {
            "base_projection": {
                "corpus": round(base["nominal_corpus"], 2),
                "pension": round(base["monthly_pension_nominal"], 2)
            },
            "scenarios": scenarios
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/peer-comparison")
async def peer_comparison(req: ForecastRequest):
    """AI-powered comparison with peer cohorts."""
    try:
        return generate_peer_comparison(req.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/inflation-erosion")
async def inflation_erosion(
    amount: float = 100000,
    inflation_rate: float = 6.0,
    years: int = 30
):
    """Show how inflation erodes purchasing power."""
    try:
        return calculate_inflation_erosion(amount, inflation_rate, years)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/assumptions")
async def assumptions():
    """All modeling assumptions for transparency."""
    return {
        "return_assumptions": EXPECTED_RETURNS,
        "asset_allocation": ASSET_ALLOCATION,
        "annuity_providers": ANNUITY_PROVIDERS,
        "inflation": {
            "default_rate": DEFAULT_INFLATION_RATE,
            "std_deviation": 1.5
        },
        "nps_regulations": {
            "mandatory_annuity_pct": 40,
            "max_lumpsum_pct": 60,
            "min_monthly_contribution": NPS_MIN_CONTRIBUTION_MONTHLY,
            "partial_withdrawal_purposes": PARTIAL_WITHDRAWAL_PURPOSES
        },
        "simulation": {"iterations": 10000},
        "tax_benefits": {
            "sec_80ccd1_limit": 150000,
            "sec_80ccd1b_exclusive": 50000,
            "sec_80ccd2_employer": "10% of basic salary"
        },
        "disclaimer": "Projections are based on historical data and assumptions. Actual results may vary. This is a decision-support tool, not financial advice."
    }


@router.get("/annuity-providers")
async def annuity_providers():
    """List all annuity providers and their rates."""
    return ANNUITY_PROVIDERS
