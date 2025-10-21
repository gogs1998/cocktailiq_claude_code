"""
Evaluate Optimizer V3 - Multi-Recommendation Testing
Tests: Does selecting the BEST recommendation improve results?
"""

import json
import numpy as np
from pathlib import Path

from src.analysis.molecular_profile import CocktailAnalyzer
from src.recommendation.optimizer_v3 import FlavorOptimizerV3


def evaluate_v3_multi_recommendation():
    """
    Test V3's ability to find the BEST modification from multiple candidates.
    """
    print("="*70)
    print("OPTIMIZER V3 EVALUATION - MULTI-RECOMMENDATION SELECTION")
    print("Testing: Does picking the BEST option improve results?")
    print("="*70)

    analyzer = CocktailAnalyzer(data_dir="raw")
    optimizer = FlavorOptimizerV3(data_dir="raw")

    test_cocktails = [
        'Margarita', 'Mojito', 'Daiquiri', 'Gimlet', 'Cosmopolitan',
        'Caipirinha', 'Whiskey Sour', 'Tom Collins', 'Moscow Mule',
        'Bramble', 'Paloma', 'Sidecar', 'Manhattan', 'Negroni'
    ]

    results = []
    improvements = 0
    degradations = 0
    no_recommendation = 0
    no_change = 0

    print(f"\nTesting {len(test_cocktails)} cocktails with BEST-OF-5 selection...")
    print("-"*70)

    for cocktail_name in test_cocktails:
        try:
            # Get original balance
            original = analyzer.analyze_cocktail(cocktail_name)
            if 'error' in original:
                print(f"SKIP {cocktail_name}: {original['error']}")
                continue

            original_balance = original['overall_balance']

            # Use V3's find_best_modification (tests 5 candidates, picks best)
            best_result = optimizer.find_best_modification(cocktail_name, max_candidates=5)

            if 'error' in best_result or not best_result.get('best_modification'):
                message = best_result.get('message', 'No modifications')
                print(f"NO REC      {cocktail_name:20s} {original_balance:.3f} ({message})")
                no_recommendation += 1
                results.append({
                    'cocktail': cocktail_name,
                    'original_balance': original_balance,
                    'new_balance': original_balance,
                    'change': 0.0,
                    'recommendation': 'none',
                    'amount': 0.0,
                    'improved': False,
                    'status': 'no_rec_needed',
                    'candidates_tested': 0
                })
                continue

            # Get best modification
            best = best_result['best_modification']
            new_balance = best['new_balance']
            balance_change = best['improvement']

            if balance_change > 0.001:
                outcome = "IMPROVED"
                improvements += 1
            elif balance_change < -0.001:
                outcome = "DEGRADED"
                degradations += 1
            else:
                outcome = "NO CHANGE"
                no_change += 1

            print(f"{outcome:12s} {cocktail_name:20s} "
                  f"{original_balance:.3f} -> {new_balance:.3f} "
                  f"({balance_change:+.3f}) +{best['ingredient'][:20]:20s} ({best['amount']}ml) "
                  f"[best of {best_result['tested_count']}]")

            results.append({
                'cocktail': cocktail_name,
                'original_balance': original_balance,
                'new_balance': new_balance,
                'change': balance_change,
                'recommendation': best['ingredient'],
                'amount': best['amount'],
                'improved': balance_change > 0,
                'status': outcome.lower(),
                'candidates_tested': best_result['tested_count'],
                'best_rank': best['rank']
            })

        except Exception as e:
            print(f"ERROR {cocktail_name}: {e}")
            continue

    print("-"*70)

    # Calculate metrics
    total_tested = len([r for r in results if r['status'] != 'no_rec_needed'])
    total_with_recs = len(results)

    if total_tested == 0:
        print("\nNo cocktails tested (all were already excellent)")
        return None

    improvement_rate = improvements / total_tested if total_tested > 0 else 0
    degradation_rate = degradations / total_tested if total_tested > 0 else 0

    avg_change = np.mean([r['change'] for r in results if r['status'] != 'no_rec_needed'])
    avg_absolute_change = np.mean([abs(r['change']) for r in results if r['status'] != 'no_rec_needed'])
    avg_candidates = np.mean([r['candidates_tested'] for r in results if r['candidates_tested'] > 0])

    print(f"\nRESULTS:")
    print(f"  Total cocktails:         {total_with_recs}")
    print(f"  No rec needed (excellent): {no_recommendation}")
    print(f"  Tested with modifications: {total_tested}")
    print(f"  Avg candidates tested:     {avg_candidates:.1f}")
    print(f"")
    print(f"  Improvements:  {improvements}/{total_tested} ({improvement_rate:.1%})")
    print(f"  Degradations:  {degradations}/{total_tested} ({degradation_rate:.1%})")
    print(f"  No change:     {no_change}/{total_tested}")
    print(f"  Avg change:    {avg_change:+.4f}")
    print(f"  Avg |change|:  {avg_absolute_change:.4f}")

    # Analyze which ranks won
    ranks_that_won = [r['best_rank'] for r in results if r['improved'] and r.get('best_rank')]
    if ranks_that_won:
        print(f"\n  Winning ranks: {ranks_that_won}")
        print(f"  (Shows if testing multiple options helps find better solutions)")

    # Save results
    output_file = Path("data/processed/balance_improvement_evaluation_v3.json")
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_cocktails': total_with_recs,
                'no_rec_needed': no_recommendation,
                'total_tested': total_tested,
                'improvements': improvements,
                'degradations': degradations,
                'improvement_rate': improvement_rate,
                'avg_balance_change': avg_change,
                'avg_candidates_tested': avg_candidates,
            },
            'detailed_results': results
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    print("\n" + "="*70)
    print("COMPARISON: V1 vs V2 vs V3")
    print("="*70)
    print("\nV1 (Fixed amounts):")
    print("  Balance Improvement: 11.1% (1/9)")
    print("\nV2 (Adaptive amounts + thresholds):")
    print("  Balance Improvement: 20.0% (2/10)")
    print(f"\nV3 (Multi-recommendation + expanded mappings):")
    print(f"  Balance Improvement: {improvement_rate:.1%} ({improvements}/{total_tested})")
    print(f"  Smart thresholds: {no_recommendation} cocktails flagged as excellent")
    print(f"  Multi-testing: Average {avg_candidates:.1f} candidates per cocktail")

    if improvement_rate > 0.20:
        improvement_vs_v2 = ((improvement_rate - 0.20) / 0.20) * 100
        print(f"\n  IMPROVEMENT over V2: +{improvement_vs_v2:.0f}%!")
    elif improvement_rate > 0.11:
        improvement_vs_v1 = ((improvement_rate - 0.11) / 0.11) * 100
        print(f"\n  IMPROVEMENT over V1: +{improvement_vs_v1:.0f}%")

    return {
        'improvement_rate': improvement_rate,
        'total_tested': total_tested,
        'no_rec_needed': no_recommendation,
        'avg_candidates': avg_candidates
    }


if __name__ == "__main__":
    evaluate_v3_multi_recommendation()
