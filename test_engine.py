"""
Quick Test Script for NPS IntelliPlan

This script tests the core financial modeling engine to verify calculations
are working correctly before deploying.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.engine.corpus_calculator import calculate_retirement_projection, compare_scenarios
from backend.engine.monte_carlo import MonteCarloSimulator
from backend.engine.optimizer import ContributionOptimizer


def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def test_basic_calculation():
    """Test basic retirement projection"""
    print_separator("Test 1: Basic Retirement Projection")
    
    result = calculate_retirement_projection(
        current_age=30,
        retirement_age=60,
        monthly_contribution=5000,
        risk_profile="moderate",
        inflation_rate=6.0,
        initial_balance=0
    )
    
    print(f"Input: Age 30, Retire 60, ₹5,000/month, Moderate risk")
    print(f"\nResults:")
    print(f"  Nominal Corpus:      ₹{result['nominal_corpus']:,.0f}")
    print(f"  Real Corpus:         ₹{result['real_corpus']:,.0f}")
    print(f"  Monthly Pension:     ₹{result['monthly_pension_nominal']:,.0f}")
    print(f"  Total Contributed:   ₹{result['total_contributions']:,.0f}")
    print(f"  Growth Multiplier:   {result['growth_multiplier']:.2f}x")
    print(f"  Expected Return:     {result['expected_return_rate']:.1f}%")
    
    # Sanity check
    assert result['nominal_corpus'] > result['total_contributions'], "Corpus should be > contributions"
    assert result['real_corpus'] < result['nominal_corpus'], "Real corpus should be < nominal"
    assert result['monthly_pension_nominal'] > 0, "Pension should be positive"
    
    print("\n✓ Test PASSED")


def test_monte_carlo_simulation():
    """Test Monte Carlo simulation"""
    print_separator("Test 2: Monte Carlo Simulation")
    
    simulator = MonteCarloSimulator(iterations=1000)  # Reduced for speed
    
    result = simulator.simulate_retirement_corpus(
        current_age=30,
        retirement_age=60,
        monthly_contribution=5000,
        risk_profile="moderate",
        initial_balance=0
    )
    
    print(f"Running 1,000 simulations...")
    print(f"\nCorpus Statistics:")
    print(f"  Median:              ₹{result['corpus_statistics']['median']:,.0f}")
    print(f"  10th Percentile:     ₹{result['corpus_statistics']['percentile_10']:,.0f}")
    print(f"  90th Percentile:     ₹{result['corpus_statistics']['percentile_90']:,.0f}")
    print(f"  Best Case:           ₹{result['corpus_statistics']['max']:,.0f}")
    print(f"  Worst Case:          ₹{result['corpus_statistics']['min']:,.0f}")
    
    print(f"\nPension Statistics:")
    print(f"  Median Pension:      ₹{result['pension_statistics']['median_pension']:,.0f}/month")
    print(f"  10th Percentile:     ₹{result['pension_statistics']['percentile_10']:,.0f}/month")
    print(f"  90th Percentile:     ₹{result['pension_statistics']['percentile_90']:,.0f}/month")
    
    # Sanity checks
    assert result['corpus_statistics']['median'] > 0, "Median corpus should be positive"
    assert result['corpus_statistics']['percentile_90'] > result['corpus_statistics']['percentile_10'], "90th > 10th"
    assert len(result['all_outcomes']) == 1000, "Should have 1000 outcomes"
    
    print("\n✓ Test PASSED")


def test_scenario_comparison():
    """Test scenario comparison"""
    print_separator("Test 3: Risk Profile Comparison")
    
    scenarios = compare_scenarios(
        current_age=30,
        retirement_age=60,
        monthly_contribution=5000,
        inflation_rate=6.0,
        initial_balance=0
    )
    
    print(f"Comparing Conservative vs Moderate vs Aggressive\n")
    
    for profile in ['conservative', 'moderate', 'aggressive']:
        result = scenarios[profile]
        print(f"{profile.capitalize():12} → Corpus: ₹{result['nominal_corpus']:>12,.0f}  "
              f"Pension: ₹{result['monthly_pension_nominal']:>8,.0f}/mo  "
              f"Return: {result['expected_return_rate']:.1f}%")
    
    # Sanity check: aggressive should have highest expected corpus
    assert scenarios['aggressive']['nominal_corpus'] > scenarios['conservative']['nominal_corpus'], \
        "Aggressive should yield higher corpus"
    
    print("\n✓ Test PASSED")


def test_contribution_optimizer():
    """Test contribution optimization"""
    print_separator("Test 4: Contribution Optimizer")
    
    optimizer = ContributionOptimizer(simulation_iterations=500)  # Reduced for speed
    
    print(f"Finding contribution for ₹30,000/month pension target...")
    
    result = optimizer.find_required_contribution(
        current_age=30,
        retirement_age=60,
        target_monthly_pension=30000,
        risk_profile="moderate",
        target_probability=70.0,
        initial_balance=0
    )
    
    print(f"\nOptimization Results:")
    print(f"  Required Contribution:   ₹{result['required_monthly_contribution']:,.0f}/month")
    print(f"  Achieved Probability:    {result['achieved_probability']:.1f}%")
    print(f"  Target Probability:      {result['target_probability']:.1f}%")
    print(f"  Target Pension:          ₹{result['target_pension']:,.0f}/month")
    print(f"  Required Corpus:         ₹{result['required_corpus']:,.0f}")
    print(f"  Is Achievable:           {result['is_achievable']}")
    
    # Sanity check
    assert result['required_monthly_contribution'] >= 500, "Should be >= minimum contribution"
    assert result['achieved_probability'] > 0, "Should have some probability"
    
    print("\n✓ Test PASSED")


def run_all_tests():
    """Run all tests"""
    print_separator("NPS IntelliPlan - Core Engine Tests")
    print("Testing financial modeling and simulation components\n")
    
    try:
        test_basic_calculation()
        test_monte_carlo_simulation()
        test_scenario_comparison()
        test_contribution_optimizer()
        
        print_separator("All Tests PASSED ✓")
        print("\nCore engine is working correctly!")
        print("You can now start the server with: python main.py")
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
