"""
Contribution Optimization Engine

This module implements algorithms to calculate required contributions
to achieve target retirement goals with specified probability thresholds.
"""

import numpy as np
from typing import Dict, Optional
from backend.engine.monte_carlo import MonteCarloSimulator
from backend.engine.corpus_calculator import calculate_retirement_projection
from backend.engine.nps_config import (
    EXPECTED_RETURNS,
    ANNUITY_RATE_SINGLE_LIFE,
    NPS_MIN_CONTRIBUTION_MONTHLY
)


class ContributionOptimizer:
    """
    Optimizer to find required monthly contribution for retirement goals.
    
    Uses binary search with Monte Carlo validation to find contribution
    amount that achieves target pension with desired probability.
    """
    
    def __init__(self, simulation_iterations: int = 5000):
        """
        Initialize optimizer.
        
        Args:
            simulation_iterations: Number of Monte Carlo iterations per test
        """
        self.simulator = MonteCarloSimulator(iterations=simulation_iterations)
    
    def find_required_contribution(
        self,
        current_age: int,
        retirement_age: int,
        target_monthly_pension: float,
        risk_profile: str = "moderate",
        target_probability: float = 70.0,
        initial_balance: float = 0,
        max_contribution: float = 100000
    ) -> Dict:
        """
        Find monthly contribution required to achieve target pension.
        
        Uses binary search to find contribution amount that achieves
        target pension with specified probability threshold.
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            target_monthly_pension: Desired monthly pension
            risk_profile: Investment risk profile
            target_probability: Desired probability of achieving goal (e.g., 70%)
            initial_balance: Current NPS balance
            max_contribution: Maximum monthly contribution to test
        
        Returns:
            Optimization results with required contribution
        """
        # Convert target pension to required corpus
        required_corpus = self._pension_to_corpus(target_monthly_pension)
        
        # Binary search bounds
        min_contribution = NPS_MIN_CONTRIBUTION_MONTHLY
        max_contribution = max_contribution
        
        # Binary search parameters
        tolerance = 100  # INR tolerance
        max_iterations = 20
        best_contribution = None
        best_probability = 0
        
        for iteration in range(max_iterations):
            # Test midpoint
            test_contribution = (min_contribution + max_contribution) / 2
            
            # Run simulation with this contribution
            result = self.simulator.calculate_goal_probability(
                current_age,
                retirement_age,
                test_contribution,
                target_monthly_pension,
                risk_profile,
                initial_balance
            )
            
            probability = result["probability_of_success"]
            
            # Track best result
            if probability >= target_probability and (
                best_contribution is None or test_contribution < best_contribution
            ):
                best_contribution = test_contribution
                best_probability = probability
            
            # Check if we've found good enough solution
            if abs(probability - target_probability) < 2:  # Within 2% of target
                break
            
            # Adjust search bounds
            if probability < target_probability:
                min_contribution = test_contribution
            else:
                max_contribution = test_contribution
            
            # Check if bounds are too close
            if max_contribution - min_contribution < tolerance:
                break
        
        # If no solution found within bounds, return max tested
        if best_contribution is None:
            best_contribution = max_contribution
            result = self.simulator.calculate_goal_probability(
                current_age,
                retirement_age,
                best_contribution,
                target_monthly_pension,
                risk_profile,
                initial_balance
            )
            best_probability = result["probability_of_success"]
        
        # Calculate what deterministic calculation would suggest
        deterministic_contribution = self._deterministic_required_contribution(
            current_age,
            retirement_age,
            required_corpus,
            risk_profile,
            initial_balance
        )
        
        return {
            "required_monthly_contribution": round(best_contribution, 2),
            "achieved_probability": round(best_probability, 2),
            "target_probability": target_probability,
            "target_pension": target_monthly_pension,
            "required_corpus": round(required_corpus, 2),
            "deterministic_estimate": round(deterministic_contribution, 2),
            "risk_adjusted_multiplier": round(best_contribution / deterministic_contribution, 3) if deterministic_contribution > 0 else 1.0,
            "is_achievable": best_probability >= (target_probability - 5),
            "recommendation": self._generate_optimization_recommendation(
                best_contribution,
                best_probability,
                target_probability,
                target_monthly_pension
            )
        }
    
    def compare_contribution_levels(
        self,
        current_age: int,
        retirement_age: int,
        contribution_amounts: list[float],
        risk_profile: str = "moderate",
        initial_balance: float = 0
    ) -> Dict:
        """
        Compare outcomes for different contribution levels.
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            contribution_amounts: List of contribution amounts to compare
            risk_profile: Risk profile
            initial_balance: Current balance
        
        Returns:
            Comparison results for each contribution level
        """
        results = {}
        
        for contribution in contribution_amounts:
            sim_result = self.simulator.simulate_retirement_corpus(
                current_age,
                retirement_age,
                contribution,
                risk_profile,
                initial_balance
            )
            
            results[f"contribution_{int(contribution)}"] = {
                "monthly_contribution": contribution,
                "median_corpus": sim_result["corpus_statistics"]["median"],
                "median_pension": sim_result["pension_statistics"]["median_pension"],
                "percentile_10_pension": sim_result["pension_statistics"]["percentile_10"],
                "percentile_90_pension": sim_result["pension_statistics"]["percentile_90"]
            }
        
        return results
    
    def _pension_to_corpus(self, monthly_pension: float) -> float:
        """Convert target monthly pension to required corpus amount."""
        # pension = corpus * 0.4 * annuity_rate / 12
        # corpus = (pension * 12) / (0.4 * annuity_rate)
        required_corpus = (monthly_pension * 12) / (0.4 * ANNUITY_RATE_SINGLE_LIFE / 100)
        return required_corpus
    
    def _deterministic_required_contribution(
        self,
        current_age: int,
        retirement_age: int,
        target_corpus: float,
        risk_profile: str,
        initial_balance: float
    ) -> float:
        """
        Calculate required contribution using deterministic formula.
        
        This provides a baseline estimate without Monte Carlo simulation.
        """
        years = retirement_age - current_age
        months = years * 12
        
        mean_return = EXPECTED_RETURNS[risk_profile]["mean"]
        monthly_rate = mean_return / 100 / 12
        
        # Account for initial balance future value
        fv_initial = initial_balance * ((1 + monthly_rate) ** months)
        remaining_target = target_corpus - fv_initial
        
        if remaining_target <= 0:
            return 0  # Initial balance is enough
        
        # Calculate required monthly contribution
        if monthly_rate > 0:
            required_contribution = remaining_target / (
                ((1 + monthly_rate) ** months - 1) / monthly_rate * (1 + monthly_rate)
            )
        else:
            required_contribution = remaining_target / months
        
        return max(required_contribution, NPS_MIN_CONTRIBUTION_MONTHLY)
    
    def _generate_optimization_recommendation(
        self,
        contribution: float,
        probability: float,
        target_prob: float,
        pension: float
    ) -> str:
        """Generate recommendation based on optimization results."""
        if probability >= target_prob:
            return f"Monthly contribution of ₹{int(contribution)} gives you {probability:.1f}% probability of achieving ₹{int(pension)} monthly pension."
        elif probability >= (target_prob - 10):
            return f"Almost there! ₹{int(contribution)}/month gives {probability:.1f}% probability. Small increase can reach your target."
        else:
            shortfall_pct = target_prob - probability
            return f"Current strategy has {probability:.1f}% probability. Consider higher contribution or adjusting retirement expectations."
