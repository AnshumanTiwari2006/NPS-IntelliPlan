"""
Gemini AI Integration for NPS IntelliPlan

Provides AI-powered retirement advice, scenario narratives,
risk assessment, and personalized recommendations using Google Gemini.
"""

import os
import json
from typing import Dict, Optional


def get_gemini_client():
    """Get Gemini API client. Returns None if API key not set."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro")
        return model
    except ImportError:
        return None
    except Exception:
        return None


def generate_retirement_advice(forecast_data: Dict) -> str:
    """
    Generate personalized retirement advice using Gemini.
    Falls back to rule-based advice if API unavailable.
    """
    model = get_gemini_client()
    
    if model is None:
        return generate_rule_based_advice(forecast_data)
    
    try:
        prompt = f"""You are an expert Indian financial advisor specializing in NPS (National Pension System).
Based on the following retirement forecast data, provide concise, actionable advice in 4-5 bullet points.
Be specific with numbers and mention relevant NPS regulations.

Forecast Data:
- Current Age: {forecast_data.get('current_age', 'N/A')}
- Retirement Age: {forecast_data.get('retirement_age', 'N/A')}
- Monthly Contribution: ₹{forecast_data.get('monthly_contribution', 'N/A')}
- Risk Profile: {forecast_data.get('risk_profile', 'N/A')}
- Projected Corpus: ₹{forecast_data.get('nominal_corpus', 'N/A')}
- Monthly Pension: ₹{forecast_data.get('monthly_pension', 'N/A')}
- Real Corpus (inflation-adjusted): ₹{forecast_data.get('real_corpus', 'N/A')}
- Growth Multiplier: {forecast_data.get('growth_multiplier', 'N/A')}x
- Total Contributions: ₹{forecast_data.get('total_contributions', 'N/A')}

Provide advice that is:
1. Specific and actionable (mention exact amounts)
2. Considers NPS tax benefits (80CCD)
3. Mentions if contribution seems adequate or needs increase
4. Suggests risk profile adjustments if appropriate
5. Brief — each point should be 1-2 sentences max

Format as a JSON array of strings, each being one advice point."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse JSON from response
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        advice_list = json.loads(text)
        return advice_list
    except Exception as e:
        return generate_rule_based_advice(forecast_data)


def generate_scenario_narrative(scenario_data: Dict) -> str:
    """
    Generate a plain-English narrative explaining a forecast scenario.
    """
    model = get_gemini_client()
    
    if model is None:
        return generate_rule_based_narrative(scenario_data)
    
    try:
        prompt = f"""Write a brief 3-4 sentence analysis of this NPS retirement forecast.
Explain what the numbers mean in simple terms for an Indian subscriber.
Mention if the plan is on track or needs adjustment.

Data: {json.dumps(scenario_data, indent=2)}

Be concise and conversational. No bullet points. Return plain text only."""

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return generate_rule_based_narrative(scenario_data)


def generate_risk_assessment(answers: Dict) -> Dict:
    """
    Generate a risk profile recommendation based on questionnaire answers.
    """
    model = get_gemini_client()
    
    # Score-based assessment (always works)
    score = 0
    total = 0
    
    risk_factors = {
        "age": answers.get("age", 30),
        "investment_horizon": answers.get("investment_horizon", 20),
        "income_stability": answers.get("income_stability", "stable"),
        "risk_tolerance": answers.get("risk_tolerance", "moderate"),
        "existing_savings": answers.get("existing_savings", "moderate"),
        "dependents": answers.get("dependents", 1),
        "financial_goals": answers.get("financial_goals", "retirement")
    }
    
    # Age factor
    age = risk_factors["age"]
    if age < 30: score += 3
    elif age < 40: score += 2
    elif age < 50: score += 1
    total += 3
    
    # Horizon factor
    horizon = risk_factors["investment_horizon"]
    if horizon > 20: score += 3
    elif horizon > 10: score += 2
    elif horizon > 5: score += 1
    total += 3
    
    # Risk tolerance factor
    tolerance = risk_factors.get("risk_tolerance", "moderate")
    if tolerance == "high": score += 3
    elif tolerance == "moderate": score += 2
    elif tolerance == "low": score += 1
    total += 3
    
    # Income stability
    stability = risk_factors.get("income_stability", "stable")
    if stability == "very_stable": score += 3
    elif stability == "stable": score += 2
    elif stability == "unstable": score += 1
    total += 3
    
    # Calculate risk score percentage
    risk_pct = (score / total) * 100
    
    if risk_pct >= 70:
        profile = "aggressive"
        description = "Your profile suggests high risk tolerance with a long investment horizon."
    elif risk_pct >= 40:
        profile = "moderate"
        description = "Your profile suggests a balanced approach with moderate risk tolerance."
    else:
        profile = "conservative"
        description = "Your profile suggests a preference for capital preservation with lower risk."
    
    # Try to get AI-enhanced assessment
    ai_insight = ""
    if model:
        try:
            prompt = f"""Based on this investor profile, give one sentence of personalized NPS advice:
Age: {age}, Horizon: {horizon} years, Risk tolerance: {tolerance}, Income: {stability}
Recommended profile: {profile}

One sentence only, specific to NPS India."""
            response = model.generate_content(prompt)
            ai_insight = response.text.strip()
        except Exception:
            pass
    
    return {
        "recommended_profile": profile,
        "risk_score": round(risk_pct, 1),
        "description": description,
        "ai_insight": ai_insight,
        "factors_considered": risk_factors
    }


def generate_goal_gap_analysis(
    current_plan: Dict,
    target_pension: float
) -> Dict:
    """
    Analyze the gap between current plan and target pension.
    """
    current_pension = current_plan.get("monthly_pension_nominal", 0)
    gap = target_pension - current_pension
    gap_pct = (gap / target_pension * 100) if target_pension > 0 else 0
    
    if gap <= 0:
        status = "on_track"
        message = f"Smart Move! Your current plan is projected to exceed your target pension by ₹{abs(gap):,.0f}/month. Note: This is a nominal value; in today's money (inflation-adjusted), this feels like ₹{current_plan.get('real_corpus',0)/200:,.0f}/month."
    elif gap_pct < 20:
        status = "close"
        message = f"AI Insight: You're almost there! A small ₹{gap * 5:,.0f}/month boost puts you on target. Inflation eats ~6% of value annually, so aim for a surplus."
    elif gap_pct < 50:
        status = "needs_adjustment"
        message = f"AI Assessment: There's a ₹{gap:,.0f}/month gap. Suggesting a 10% annual step-up to neutralize inflation and hit your target."
    else:
        status = "significant_gap"
        message = f"AI Warning: Major gap of ₹{gap:,.0f}/month. Your contributions aren't keeping pace with inflation. Consider a higher risk profile or increased monthly savings."
    
    recommendations = []
    if gap > 0:
        # Suggest contribution increase
        estimated_increase = gap * 5  # rough estimate
        recommendations.append(f"Increase monthly contribution by ₹{estimated_increase:,.0f}")
        
        if current_plan.get("risk_profile") == "conservative":
            recommendations.append("Consider switching to moderate risk profile for higher returns")
        
        recommendations.append("Utilize Section 80CCD(1B) for additional ₹50,000 tax benefit")
        
        if current_plan.get("annual_step_up", 0) == 0:
            recommendations.append("Enable 10% annual step-up to grow contributions with salary")
    
    return {
        "target_pension": target_pension,
        "projected_pension": round(current_pension, 2),
        "gap_amount": round(gap, 2),
        "gap_percentage": round(gap_pct, 1),
        "status": status,
        "message": message,
        "recommendations": recommendations
    }


def generate_what_if_analysis(
    base_projection: Dict,
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    risk_profile: str,
    inflation_rate: float,
    initial_balance: float,
    annual_step_up: float = 0.0,
    employer_contribution: float = 0.0
) -> Dict:
    """
    Generate what-if scenarios to show impact of different choices.
    """
    from backend.engine.corpus_calculator import calculate_retirement_projection
    
    scenarios = {}
    
    # What if retire 2 years later?
    if retirement_age + 2 <= 75:
        later = calculate_retirement_projection(
            current_age, retirement_age + 2, monthly_contribution,
            risk_profile, inflation_rate, initial_balance,
            annual_step_up, employer_contribution
        )
        scenarios["retire_later"] = {
            "label": f"Retire at {retirement_age + 2} instead of {retirement_age}",
            "corpus": round(later["nominal_corpus"], 2),
            "pension": round(later["monthly_pension_nominal"], 2),
            "corpus_change_pct": round(
                ((later["nominal_corpus"] - base_projection["nominal_corpus"]) / 
                 base_projection["nominal_corpus"]) * 100, 1
            )
        }
    
    # What if contribute 50% more?
    more = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution * 1.5,
        risk_profile, inflation_rate, initial_balance,
        annual_step_up, employer_contribution
    )
    scenarios["contribute_more"] = {
        "label": f"Contribute ₹{monthly_contribution * 1.5:,.0f}/month (+50%)",
        "corpus": round(more["nominal_corpus"], 2),
        "pension": round(more["monthly_pension_nominal"], 2),
        "corpus_change_pct": round(
            ((more["nominal_corpus"] - base_projection["nominal_corpus"]) / 
             base_projection["nominal_corpus"]) * 100, 1
        )
    }
    
    # What if 10% annual step-up?
    stepup = calculate_retirement_projection(
        current_age, retirement_age, monthly_contribution,
        risk_profile, inflation_rate, initial_balance,
        annual_step_up=10.0
    )
    scenarios["with_stepup"] = {
        "label": "10% annual step-up in contribution",
        "corpus": round(stepup["nominal_corpus"], 2),
        "pension": round(stepup["monthly_pension_nominal"], 2),
        "corpus_change_pct": round(
            ((stepup["nominal_corpus"] - base_projection["nominal_corpus"]) / 
             base_projection["nominal_corpus"]) * 100, 1
        )
    }
    
    # What if switch to aggressive?
    if risk_profile != "aggressive":
        agg = calculate_retirement_projection(
            current_age, retirement_age, monthly_contribution,
            "aggressive", inflation_rate, initial_balance,
            annual_step_up, employer_contribution
        )
        scenarios["go_aggressive"] = {
            "label": "Switch to Aggressive strategy",
            "corpus": round(agg["nominal_corpus"], 2),
            "pension": round(agg["monthly_pension_nominal"], 2),
            "corpus_change_pct": round(
                ((agg["nominal_corpus"] - base_projection["nominal_corpus"]) / 
                 base_projection["nominal_corpus"]) * 100, 1
            )
        }
    
    return scenarios


def generate_peer_comparison(forecast_data: Dict) -> Dict:
    """
    AI-powered peer group comparison.
    """
    model = get_gemini_client()
    age = forecast_data.get("current_age", 30)
    contrib = forecast_data.get("monthly_contribution", 5000)
    
    # Benchmarks (internal rule-based)
    avg_contrib = 4500 if age < 30 else 8500 if age < 45 else 12500
    percentile = 50
    if contrib > avg_contrib * 2: percentile = 90
    elif contrib > avg_contrib * 1.5: percentile = 75
    elif contrib > avg_contrib: percentile = 60
    elif contrib < avg_contrib * 0.5: percentile = 25
    
    comparisons = {
        "peer_average_contribution": avg_contrib,
        "user_percentile": percentile,
        "cohort_description": f"Indian professionals aged {age-2}-{age+2}",
        "benchmark_label": "National NPS Average"
    }

    if model:
        try:
            prompt = f"""Compare this NPS contributor to their peers:
Age: {age}, Monthly Contribution: ₹{contrib}, Peer Average: ₹{avg_contrib}
Provide 2-3 bullet points of AI context on where they stand and one 'Smart Move' to get ahead.
Be encouraging but realistic. Format as plain text with bullet points."""
            response = model.generate_content(prompt)
            comparisons["ai_context"] = response.text.strip()
        except Exception:
            comparisons["ai_context"] = "You are doing well compared to your cohort. Increasing by 10% could put you in the top 20% of contributors."
    else:
        comparisons["ai_context"] = "You are doing well compared to your cohort. Increasing by 10% could put you in the top 20% of contributors."

    return comparisons


# ── Rule-based fallbacks (when Gemini unavailable) ───────────

def generate_rule_based_advice(data: Dict) -> list:
    """Fallback advice when Gemini is unavailable."""
    advice = []
    
    contrib = data.get("monthly_contribution", 5000)
    age = data.get("current_age", 30)
    profile = data.get("risk_profile", "moderate")
    corpus = data.get("nominal_corpus", 0)
    
    if contrib < 10000:
        advice.append(f"Consider increasing your contribution to at least ₹10,000/month. Even ₹{10000 - contrib:,.0f} more can significantly boost your corpus due to compounding.")
    
    if age < 35 and profile != "aggressive":
        advice.append("At your age, an aggressive strategy could yield substantially higher returns over 25+ years. Consider switching from Auto Choice to Active Choice with higher equity allocation.")
    
    advice.append(f"You're eligible for additional ₹50,000 tax deduction under Section 80CCD(1B) exclusively for NPS. This could save you up to ₹15,600 in taxes annually (30% slab + cess).")
    
    if data.get("employer_contribution", 0) == 0:
        advice.append("If your employer offers NPS co-contribution, enroll immediately — employer contributions up to 10% of basic salary get Section 80CCD(2) deduction with NO upper limit.")
    
    advice.append(f"Enable annual step-up of 10% to align contributions with salary growth. This single change can increase your final corpus by 40-60% over 30 years.")
    
    return advice


def generate_rule_based_narrative(data: Dict) -> str:
    """Fallback narrative when Gemini is unavailable."""
    corpus = data.get("nominal_corpus", 0)
    pension = data.get("monthly_pension_nominal", 0)
    years = data.get("years_invested", 0)
    multiplier = data.get("growth_multiplier", 0)
    
    return (
        f"Over {years} years of disciplined investing, your NPS corpus is projected to grow to "
        f"₹{corpus / 1e7:.1f} crore — a {multiplier:.1f}x return on your total contributions. "
        f"This translates to an estimated monthly pension of ₹{pension:,.0f} after the mandatory "
        f"40% annuity purchase. The remaining 60% (₹{corpus * 0.6 / 1e7:.1f} crore) will be "
        f"available as a tax-free lumpsum withdrawal."
    )
