"""
Monte Carlo Simulation Engine for Retirement Forecasting

This module implements probabilistic retirement projections using Monte Carlo methods
to model market uncertainty and provide probability-based retirement planning insights.
"""

import numpy as np
from typing import Dict, List, Tuple
from backend.engine.nps_config import (
    EXPECTED_RETURNS,
    DEFAULT_SIMULATION_ITERATIONS,
    RANDOM_SEED
)
from backend.engine.corpus_calculator import (
    estimate_monthly_pension
)


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for retirement corpus projections.
    
    Simulates thousands of possible market return scenarios to generate
    probability distributions of retirement outcomes.
    """
    
    def __init__(self, iterations: int = DEFAULT_SIMULATION_ITERATIONS, seed: int = RANDOM_SEED):
        """
        Initialize simulator.
        
        Args:
            iterations: Number of simulation runs
            seed: Random seed for reproducibility
        """
        self.iterations = iterations
        self.seed = seed
        np.random.seed(seed)
    
    def simulate_retirement_corpus(
        self,
        current_age: int,
        retirement_age: int,
        monthly_contribution: float,
        risk_profile: str = "moderate",
        initial_balance: float = 0
    ) -> Dict:
        """
        Run Monte Carlo simulation for retirement corpus.
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            monthly_contribution: Monthly contribution amount
            risk_profile: Investment risk profile
            initial_balance: Current NPS balance
        
        Returns:
            Dictionary containing simulation results and statistics
        """
        years = retirement_age - current_age
        months = years * 12
        
        if years <= 0:
            raise ValueError("Retirement age must be greater than current age")
        
        # Get return distribution parameters for risk profile
        mean_return = EXPECTED_RETURNS[risk_profile]["mean"]
        std_dev = EXPECTED_RETURNS[risk_profile]["std_dev"]
        
        # Run simulations
        # Yearly paths to compute confidence bands
        yearly_paths = np.zeros((self.iterations, years + 1))
        yearly_paths[:, 0] = initial_balance
        
        for i in range(self.iterations):
            corpus = initial_balance
            
            # Simulate each year's return
            for year in range(years):
                # Generate random annual return from normal distribution
                annual_return = np.random.normal(mean_return, std_dev) / 100
                
                # Convert annual return to monthly rate
                monthly_rate = (1 + annual_return) ** (1/12) - 1
                
                # Apply monthly contributions and returns for 12 months
                for month in range(12):
                    corpus = corpus * (1 + monthly_rate) + monthly_contribution
                
                yearly_paths[i, year + 1] = max(corpus, 0)
        
        final_corpus_values = yearly_paths[:, -1]
        
        # Calculate statistics
        stats = self._calculate_statistics(final_corpus_values)
        
        # Calculate yearly percentile bands
        yearly_bands = {
            "p10": np.percentile(yearly_paths, 10, axis=0).tolist(),
            "p50": np.percentile(yearly_paths, 50, axis=0).tolist(),
            "p90": np.percentile(yearly_paths, 90, axis=0).tolist()
        }
        
        # Calculate pension statistics
        pension_stats = self._calculate_pension_statistics(final_corpus_values)
        
        # Generate distribution bins for charting
        distribution = self._generate_distribution(final_corpus_values)
        
        return {
            "corpus_statistics": stats,
            "pension_statistics": pension_stats,
            "distribution": distribution,
            "yearly_bands": yearly_bands,
            "simulations_run": self.iterations,
            "risk_profile": risk_profile,
            "all_outcomes": final_corpus_values.tolist()  # For further analysis
        }
    
    def calculate_goal_probability(
        self,
        current_age: int,
        retirement_age: int,
        monthly_contribution: float,
        target_monthly_pension: float,
        risk_profile: str = "moderate",
        initial_balance: float = 0
    ) -> Dict:
        """
        Calculate probability of achieving a target monthly pension.
        
        Args:
            current_age: Current age
            retirement_age: Target retirement age
            monthly_contribution: Monthly contribution
            target_monthly_pension: Desired monthly pension
            risk_profile: Risk profile
            initial_balance: Current balance
        
        Returns:
            Dictionary with probability metrics and recommendations
        """
        # Run simulation
        results = self.simulate_retirement_corpus(
            current_age,
            retirement_age,
            monthly_contribution,
            risk_profile,
            initial_balance
        )
        
        # Convert target pension to required corpus
        # Reverse calculation: pension = corpus * 0.4 * annuity_rate / 12
        # Therefore: required_corpus = (pension * 12) / (0.4 * annuity_rate)
        from backend.engine.nps_config import ANNUITY_RATE_SINGLE_LIFE
        required_corpus = (target_monthly_pension * 12) / (0.4 * ANNUITY_RATE_SINGLE_LIFE / 100)
        
        # Count how many simulations achieved the goal
        corpus_values = np.array(results["all_outcomes"])
        success_count = np.sum(corpus_values >= required_corpus)
        probability = (success_count / self.iterations) * 100
        
        # Calculate gap between median outcome and target
        median_corpus = results["corpus_statistics"]["median"]
        corpus_gap = required_corpus - median_corpus
        
        # Estimate additional contribution needed (rough approximation)
        years = retirement_age - current_age
        if corpus_gap > 0 and years > 0:
            # Using simplified FV formula for quick estimate
            mean_return = EXPECTED_RETURNS[risk_profile]["mean"] / 100
            monthly_rate = mean_return / 12
            total_months = years * 12
            
            if monthly_rate > 0:
                additional_contribution = corpus_gap / (
                    ((1 + monthly_rate) ** total_months - 1) / monthly_rate * (1 + monthly_rate)
                )
            else:
                additional_contribution = corpus_gap / total_months
        else:
            additional_contribution = 0
        
        return {
            "target_pension": target_monthly_pension,
            "required_corpus": round(required_corpus, 2),
            "probability_of_success": round(probability, 2),
            "median_corpus": round(median_corpus, 2),
            "corpus_gap": round(corpus_gap, 2),
            "additional_contribution_needed": round(max(0, additional_contribution), 2),
            "recommendation": self._generate_recommendation(probability, corpus_gap)
        }
    
    def _calculate_statistics(self, values: np.ndarray) -> Dict:
        """Calculate statistical metrics from simulation results."""
        return {
            "mean": round(np.mean(values), 2),
            "median": round(np.median(values), 2),
            "std_dev": round(np.std(values), 2),
            "min": round(np.min(values), 2),
            "max": round(np.max(values), 2),
            "percentile_10": round(np.percentile(values, 10), 2),
            "percentile_25": round(np.percentile(values, 25), 2),
            "percentile_75": round(np.percentile(values, 75), 2),
            "percentile_90": round(np.percentile(values, 90), 2)
        }
    
    def _calculate_pension_statistics(self, corpus_values: np.ndarray) -> Dict:
        """Calculate pension statistics from corpus values."""
        pension_values = np.array([
            estimate_monthly_pension(corpus)[0] for corpus in corpus_values
        ])
        
        return {
            "mean_pension": round(np.mean(pension_values), 2),
            "median_pension": round(np.median(pension_values), 2),
            "min_pension": round(np.min(pension_values), 2),
            "max_pension": round(np.max(pension_values), 2),
            "percentile_10": round(np.percentile(pension_values, 10), 2),
            "percentile_90": round(np.percentile(pension_values, 90), 2)
        }
    
    def _generate_distribution(self, values: np.ndarray, bins: int = 50) -> Dict:
        """Generate histogram data for probability distribution visualization."""
        hist, bin_edges = np.histogram(values, bins=bins)
        
        return {
            "bins": bin_edges.tolist(),
            "frequencies": hist.tolist(),
            "probabilities": (hist / self.iterations * 100).tolist()
        }
    
    def _generate_recommendation(self, probability: float, gap: float) -> str:
        """Generate human-readable recommendation based on probability."""
        if probability >= 80:
            return "Excellent! You have a strong probability of achieving your retirement goal."
        elif probability >= 60:
            return f"Good progress. Consider increasing monthly contribution by ₹{int(gap / 360)} to improve probability."
        elif probability >= 40:
            return f"Moderate risk. Increasing contribution or retirement age may help achieve your goal."
        else:
            return "Current plan has low probability of success. Significant increase in contribution or adjustment of expectations recommended."


def run_scenario_comparison(
    current_age: int,
    retirement_age: int,
    monthly_contribution: float,
    initial_balance: float = 0
) -> Dict:
    """
    Compare Monte Carlo simulations across all risk profiles.
    
    Args:
        current_age: Current age
        retirement_age: Target retirement age
        monthly_contribution: Monthly contribution
        initial_balance: Current balance
    
    Returns:
        Comparison results for all risk profiles
    """
    simulator = MonteCarloSimulator()
    comparison = {}
    
    for risk_profile in ["conservative", "moderate", "aggressive"]:
        comparison[risk_profile] = simulator.simulate_retirement_corpus(
            current_age,
            retirement_age,
            monthly_contribution,
            risk_profile,
            initial_balance
        )
    
    return comparison
