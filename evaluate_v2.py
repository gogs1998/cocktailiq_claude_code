"""
Evaluate Optimizer V2 (Improved)
Test adaptive amounts and smart thresholds.
"""

import json
import numpy as np
from pathlib import Path

from src.analysis.molecular_profile import CocktailAnalyzer
from src.recommendation.optimizer_v2 import FlavorOptimizerV2
from src.recommendation.optimizer import CocktailModifier


def evaluate_v2():
    """Evaluate improved optimizer."""
    print("="*70)
    print("OPTIMIZER V2 EVALUATION - ADAPTIVE AMOUNTS & SMART THRESHOLDS")
    print("="*70)

    analyzer = CocktailAnalyzer(data_dir="raw")
    optimizer = FlavorOptimizerV2(data_dir="raw")
    modifier = CocktailModifier(data_dir="raw")

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

    print(f"\nTesting {len(test_cocktails)} cocktails...")
    print("-"*70)

    for cocktail_name in test_cocktails:
        try:
            # Analyze original
            original = analyzer.analyze_cocktail(cocktail_name)
            if 'error' in original:
                print(f"SKIP {cocktail_name}: {original['error']}")
                continue

            original_balance = original['overall_balance']

            # Get V2 recommendations (with smart thresholds)
            recs = optimizer.recommend_improvements(cocktail_name)

            if 'error' in recs:
                print(f"SKIP {cocktail_name}: Error in recommendations")
                continue

            # Check if recommendations exist
            if not recs.get('recommendations'):
                print(f"NO REC      {cocktail_name:20s} {original_balance:.3f} "
                      f"(already excellent - no changes needed)")
                no_recommendation += 1
                results.append({
                    'cocktail': cocktail_name,
                    'original_balance': original_balance,
                    'new_balance': original_balance,
                    'change': 0.0,
                    'recommendation': 'none',
                    'amount': 0.0,
                    'improved': False,
                    'status': 'no_rec_needed'
                })
                continue

            # Apply top recommendation
            top_rec = recs['recommendations'][0]['recommendation']
            modification = [{
                'action': 'add',
                'ingredient': top_rec['ingredient'],
                'amount': top_rec['amount']
            }]

            result = modifier.modify_cocktail(cocktail_name, modification)
            if 'error' in result:
                print(f"SKIP {cocktail_name}: Modification failed")
                continue

            # Check if balance improved
            new_balance = result['modified']['overall_balance']
            balance_change = new_balance - original_balance

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
                  f"({balance_change:+.3f}) +{top_rec['ingredient'][:20]:20s} ({top_rec['amount']}ml)")

            results.append({
                'cocktail': cocktail_name,
                'original_balance': original_balance,
                'new_balance': new_balance,
                'change': balance_change,
                'recommendation': top_rec['ingredient'],
                'amount': top_rec['amount'],
                'improved': balance_change > 0,
                'status': outcome.lower()
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

    print(f"\nRESULTS:")
    print(f"  Total cocktails:         {total_with_recs}")
    print(f"  No rec needed (excellent): {no_recommendation}")
    print(f"  Tested with modifications: {total_tested}")
    print(f"")
    print(f"  Improvements:  {improvements}/{total_tested} ({improvement_rate:.1%})")
    print(f"  Degradations:  {degradations}/{total_tested} ({degradation_rate:.1%})")
    print(f"  No change:     {no_change}/{total_tested}")
    print(f"  Avg change:    {avg_change:+.4f}")
    print(f"  Avg |change|:  {avg_absolute_change:.4f}")

    # Save results
    output_file = Path("data/processed/balance_improvement_evaluation_v2.json")
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
            },
            'detailed_results': results
        }, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    print("\n" + "="*70)
    print("COMPARISON: V1 vs V2")
    print("="*70)
    print("\nV1 (Original):")
    print("  Balance Improvement: 11.1% (1/9)")
    print("  Issue: Fixed amounts, no thresholds")
    print("\nV2 (Improved):")
    print(f"  Balance Improvement: {improvement_rate:.1%} ({improvements}/{total_tested})")
    print(f"  Smart thresholds: {no_recommendation} cocktails flagged as already excellent")
    print(f"  Adaptive amounts: 5-30ml based on balance")

    if improvement_rate > 0.11:
        improvement_pct = ((improvement_rate - 0.11) / 0.11) * 100
        print(f"\n  IMPROVEMENT: +{improvement_pct:.0f}% better than V1!")

    return {
        'improvement_rate': improvement_rate,
        'total_tested': total_tested,
        'no_rec_needed': no_recommendation
    }


if __name__ == "__main__":
    evaluate_v2()
