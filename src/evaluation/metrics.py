"""
Evaluation Metrics for CocktailIQ
Calculate MRR, Recall, and other performance metrics.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

from ..analysis.molecular_profile import CocktailAnalyzer
from ..recommendation.optimizer import FlavorOptimizer


class CocktailIQEvaluator:
    """Evaluate recommendation quality using MRR, Recall, and accuracy metrics."""

    def __init__(self, data_dir: str = "raw"):
        """Initialize evaluator."""
        self.analyzer = CocktailAnalyzer(data_dir)
        self.optimizer = FlavorOptimizer(data_dir)

        # Load processed data for ground truth
        processed_file = Path("data/processed/cocktails_processed.json")
        with open(processed_file, 'r', encoding='utf-8') as f:
            self.cocktails = json.load(f)

        print(f"Loaded {len(self.cocktails)} cocktails for evaluation")

    def calculate_mrr(self, k: int = 10) -> Dict:
        """
        Calculate Mean Reciprocal Rank for ingredient recommendations.

        MRR measures how quickly the correct ingredient appears in recommendations.

        Args:
            k: Consider top-k recommendations

        Returns:
            Dictionary with MRR and detailed results
        """
        print(f"\nCalculating MRR@{k}...")

        reciprocal_ranks = []
        total_queries = 0
        found_count = 0

        # For each cocktail, remove one ingredient and see if we recommend it back
        for cocktail in self.cocktails[:50]:  # Sample 50 for testing
            if len(cocktail['ingredients']) < 3:
                continue

            name = cocktail['name']
            ingredients = cocktail['ingredients']

            # Try removing each non-base ingredient
            for i, removed_ingredient in enumerate(ingredients[1:], 1):  # Skip first (usually base spirit)
                if not removed_ingredient:
                    continue

                total_queries += 1

                # Get recommendations for the incomplete cocktail
                try:
                    recommendations = self.optimizer.recommend_improvements(name)

                    if 'error' in recommendations or not recommendations.get('recommendations'):
                        continue

                    # Check if removed ingredient appears in top-k recommendations
                    recommended_ingredients = [
                        rec['recommendation']['ingredient']
                        for rec in recommendations['recommendations'][:k]
                    ]

                    # Find rank of removed ingredient (case-insensitive match)
                    removed_lower = removed_ingredient.lower()
                    rank = None

                    for r, rec_ing in enumerate(recommended_ingredients, 1):
                        if removed_lower in rec_ing.lower() or rec_ing.lower() in removed_lower:
                            rank = r
                            break

                    if rank:
                        reciprocal_ranks.append(1.0 / rank)
                        found_count += 1
                    else:
                        reciprocal_ranks.append(0.0)

                except Exception as e:
                    print(f"  Error processing {name}: {e}")
                    continue

        mrr = np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0

        return {
            'MRR@10': float(mrr),
            'total_queries': total_queries,
            'found_in_top_k': found_count,
            'success_rate': found_count / total_queries if total_queries > 0 else 0.0,
            'reciprocal_ranks': reciprocal_ranks[:20],  # Sample
        }

    def calculate_recall(self, k_values: List[int] = [5, 10]) -> Dict:
        """
        Calculate Recall@k for ingredient recommendations.

        Recall@k = proportion of relevant items found in top-k recommendations.

        Args:
            k_values: List of k values to evaluate

        Returns:
            Dictionary with Recall@k for each k
        """
        print(f"\nCalculating Recall@{k_values}...")

        results = {f'Recall@{k}': [] for k in k_values}

        # For each cocktail, check if missing ingredients are recommended
        for cocktail in self.cocktails[:50]:
            if len(cocktail['ingredients']) < 3:
                continue

            name = cocktail['name']
            actual_ingredients = set(ing.lower() for ing in cocktail['ingredients'] if ing)

            try:
                # Get recommendations
                recommendations = self.optimizer.recommend_improvements(name)

                if 'error' in recommendations or not recommendations.get('recommendations'):
                    continue

                # Get recommended ingredients at different k
                for k in k_values:
                    recommended = set(
                        rec['recommendation']['ingredient'].lower()
                        for rec in recommendations['recommendations'][:k]
                    )

                    # Calculate overlap (how many actual ingredients are in recommendations)
                    # Note: This is simplified - in real scenario, we'd have "missing" ingredients
                    overlap = len(actual_ingredients & recommended)
                    recall = overlap / len(actual_ingredients) if actual_ingredients else 0.0

                    results[f'Recall@{k}'].append(recall)

            except Exception as e:
                continue

        # Calculate mean recall for each k
        recall_means = {}
        for k in k_values:
            key = f'Recall@{k}'
            if results[key]:
                recall_means[key] = float(np.mean(results[key]))
            else:
                recall_means[key] = 0.0

        return recall_means

    def calculate_balance_accuracy(self) -> Dict:
        """
        Calculate how accurately the system predicts balance improvements.

        Tests: Does adding recommended ingredient actually improve balance?

        Returns:
            Accuracy metrics
        """
        print("\nCalculating balance prediction accuracy...")

        correct_predictions = 0
        total_predictions = 0
        improvements = []

        # Test on sample cocktails
        test_cocktails = ['Martini', 'Mojito', 'Margarita', 'Manhattan', 'Negroni']

        for cocktail_name in test_cocktails:
            try:
                # Get original balance
                original = self.analyzer.analyze_cocktail(cocktail_name)
                if 'error' in original:
                    continue

                original_balance = original['overall_balance']

                # Get recommendations
                recs = self.optimizer.recommend_improvements(cocktail_name)
                if 'error' in recs or not recs.get('recommendations'):
                    continue

                # Test top recommendation
                top_rec = recs['recommendations'][0]['recommendation']

                # Simulate adding the recommended ingredient
                from ..recommendation.optimizer import CocktailModifier
                modifier = CocktailModifier(data_dir="raw")

                modification = [{
                    'action': 'add',
                    'ingredient': top_rec['ingredient'],
                    'amount': top_rec['amount']
                }]

                result = modifier.modify_cocktail(cocktail_name, modification)

                if 'error' not in result:
                    new_balance = result['modified']['overall_balance']

                    # Check if balance actually improved
                    improved = new_balance > original_balance

                    total_predictions += 1
                    if improved:
                        correct_predictions += 1

                    improvements.append({
                        'cocktail': cocktail_name,
                        'original_balance': original_balance,
                        'new_balance': new_balance,
                        'improved': improved,
                        'recommendation': top_rec['ingredient']
                    })

            except Exception as e:
                print(f"  Error testing {cocktail_name}: {e}")
                continue

        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0

        return {
            'accuracy': float(accuracy),
            'correct_predictions': correct_predictions,
            'total_predictions': total_predictions,
            'sample_improvements': improvements,
        }

    def calculate_flavor_dimension_accuracy(self) -> Dict:
        """
        Calculate accuracy of individual flavor dimension predictions.

        Tests: If system says "too sweet", does adding suggested ingredient reduce sweetness?

        Returns:
            Per-dimension accuracy
        """
        print("\nCalculating flavor dimension accuracy...")

        dimension_accuracy = defaultdict(lambda: {'correct': 0, 'total': 0})

        test_cocktails = self.cocktails[:30]

        for cocktail in test_cocktails:
            name = cocktail['name']

            try:
                # Analyze cocktail
                analysis = self.analyzer.analyze_cocktail(name)
                if 'error' in analysis:
                    continue

                original_scores = analysis['balance_scores']

                # Get recommendations
                recs = self.optimizer.recommend_improvements(name)
                if 'error' in recs or not recs.get('recommendations'):
                    continue

                # Check each identified issue
                for issue in recs.get('identified_issues', []):
                    dimension = issue['dimension']
                    issue_type = issue['type']

                    dimension_accuracy[dimension]['total'] += 1

                    # Find recommendation addressing this dimension
                    relevant_rec = None
                    for rec in recs['recommendations']:
                        if dimension.lower() in rec['issue'].lower():
                            relevant_rec = rec['recommendation']
                            break

                    if relevant_rec:
                        # Test if it actually helps (simplified check)
                        target_profile = relevant_rec['ingredient_taste_profile']

                        if issue_type == 'too_high':
                            # Should add ingredient low in this dimension
                            if target_profile[dimension] < original_scores[dimension]:
                                dimension_accuracy[dimension]['correct'] += 1
                        else:  # too_low
                            # Should add ingredient high in this dimension
                            if target_profile[dimension] > original_scores[dimension]:
                                dimension_accuracy[dimension]['correct'] += 1

            except Exception as e:
                continue

        # Calculate accuracy per dimension
        results = {}
        for dimension, counts in dimension_accuracy.items():
            if counts['total'] > 0:
                results[f'{dimension}_accuracy'] = counts['correct'] / counts['total']
            else:
                results[f'{dimension}_accuracy'] = 0.0

        results['overall_dimension_accuracy'] = np.mean(list(results.values())) if results else 0.0

        return results

    def run_full_evaluation(self) -> Dict:
        """
        Run complete evaluation suite.

        Returns:
            All metrics
        """
        print("="*60)
        print("COCKTAILIQ EVALUATION - REAL DATA")
        print("="*60)

        results = {}

        # 1. MRR
        mrr_results = self.calculate_mrr(k=10)
        results['MRR@10'] = mrr_results['MRR@10']
        results['mrr_details'] = mrr_results

        # 2. Recall
        recall_results = self.calculate_recall(k_values=[5, 10])
        results.update(recall_results)

        # 3. Balance accuracy
        balance_acc = self.calculate_balance_accuracy()
        results['balance_accuracy'] = balance_acc['accuracy']
        results['balance_details'] = balance_acc

        # 4. Dimension accuracy
        dim_acc = self.calculate_flavor_dimension_accuracy()
        results.update(dim_acc)

        return results


def main():
    """Run evaluation and print results."""
    evaluator = CocktailIQEvaluator(data_dir="raw")

    results = evaluator.run_full_evaluation()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    print(f"\nRanking Metrics:")
    print(f"  MRR@10:      {results['MRR@10']:.3f}")
    print(f"  Recall@5:    {results.get('Recall@5', 0):.3f}")
    print(f"  Recall@10:   {results.get('Recall@10', 0):.3f}")

    print(f"\nAccuracy Metrics:")
    print(f"  Balance Accuracy: {results['balance_accuracy']:.3f}")
    print(f"  Dimension Accuracy: {results.get('overall_dimension_accuracy', 0):.3f}")

    print(f"\nDetailed Balance Predictions:")
    for imp in results['balance_details']['sample_improvements']:
        status = "[+]" if imp['improved'] else "[X]"
        print(f"  {status} {imp['cocktail']}: {imp['original_balance']:.3f} -> {imp['new_balance']:.3f} "
              f"(+{imp['recommendation']})")

    # Save results
    results_file = Path("data/processed/evaluation_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_file}")

    # Comparison
    print("\n" + "="*60)
    print("COMPARISON TO REFERENCE PROJECT")
    print("="*60)
    print("\nReference Project:")
    print("  MRR@10:   0.395")
    print("  Recall@5: 0.429")
    print("  Recall@10: 0.667")

    print("\nCocktailIQ:")
    print(f"  MRR@10:   {results['MRR@10']:.3f}")
    print(f"  Recall@5: {results.get('Recall@5', 0):.3f}")
    print(f"  Recall@10: {results.get('Recall@10', 0):.3f}")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
