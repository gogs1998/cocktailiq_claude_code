"""
Cocktail Optimizer and Recommendation Engine
Provides intelligent suggestions to improve cocktail flavor balance.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import defaultdict

from ..analysis.molecular_profile import MolecularProfiler, CocktailAnalyzer


class CocktailModifier:
    """Modify cocktails and predict flavor impact."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize cocktail modifier.

        Args:
            data_dir: Directory containing data files
        """
        self.profiler = MolecularProfiler(data_dir)
        self.analyzer = CocktailAnalyzer(data_dir)

        # Load ingredient list for recommendations
        ingredient_file = Path("data/processed/ingredients_list.json")
        if ingredient_file.exists():
            with open(ingredient_file, 'r', encoding='utf-8') as f:
                self.available_ingredients = json.load(f)
        else:
            self.available_ingredients = []

    def modify_cocktail(self, cocktail_name: str, modifications: List[Dict]) -> Dict:
        """
        Apply modifications to a cocktail and predict the flavor impact.

        Args:
            cocktail_name: Name of base cocktail
            modifications: List of modifications, each a dict with:
                - action: 'add', 'remove', 'increase', 'decrease', 'substitute'
                - ingredient: ingredient name
                - amount: amount in ml (for add/increase/decrease)
                - substitute_with: new ingredient (for substitute action)

        Returns:
            Analysis of modified cocktail with before/after comparison
        """
        # Get original cocktail
        original_analysis = self.analyzer.analyze_cocktail(cocktail_name)

        if 'error' in original_analysis:
            return original_analysis

        # Apply modifications
        modified_ingredients = original_analysis['ingredients'].copy()
        modified_measures = [m.copy() for m in self.analyzer._find_cocktail(cocktail_name)['measures']]

        for mod in modifications:
            action = mod.get('action')
            ingredient = mod.get('ingredient')

            if action == 'add':
                modified_ingredients.append(ingredient)
                modified_measures.append({'value': mod.get('amount', 30.0), 'original': f"{mod.get('amount', 30.0)}ml"})

            elif action == 'remove':
                if ingredient in modified_ingredients:
                    idx = modified_ingredients.index(ingredient)
                    modified_ingredients.pop(idx)
                    modified_measures.pop(idx)

            elif action == 'increase':
                if ingredient in modified_ingredients:
                    idx = modified_ingredients.index(ingredient)
                    modified_measures[idx]['value'] += mod.get('amount', 10.0)

            elif action == 'decrease':
                if ingredient in modified_ingredients:
                    idx = modified_ingredients.index(ingredient)
                    modified_measures[idx]['value'] = max(0, modified_measures[idx]['value'] - mod.get('amount', 10.0))

            elif action == 'substitute':
                if ingredient in modified_ingredients:
                    idx = modified_ingredients.index(ingredient)
                    modified_ingredients[idx] = mod.get('substitute_with')

        # Analyze modified cocktail
        modified_profiles = [self.profiler.get_ingredient_profile(ing) for ing in modified_ingredients]
        modified_aggregated = self.analyzer._aggregate_profiles(modified_profiles, modified_measures)
        modified_balance = self.analyzer._compute_overall_balance(modified_aggregated['taste_scores'])
        modified_complexity = self.analyzer._compute_complexity(modified_profiles)

        # Generate comparison
        result = {
            'original': {
                'name': cocktail_name,
                'ingredients': original_analysis['ingredients'],
                'taste_scores': original_analysis['balance_scores'],
                'overall_balance': original_analysis['overall_balance'],
                'complexity': original_analysis['complexity_score'],
            },
            'modified': {
                'ingredients': modified_ingredients,
                'taste_scores': modified_aggregated['taste_scores'],
                'overall_balance': modified_balance,
                'complexity': modified_complexity,
            },
            'modifications_applied': modifications,
            'impact_analysis': self._analyze_impact(
                original_analysis['balance_scores'],
                modified_aggregated['taste_scores'],
                original_analysis['overall_balance'],
                modified_balance
            ),
        }

        return result

    def _analyze_impact(self, original_scores: Dict, modified_scores: Dict,
                       original_balance: float, modified_balance: float) -> Dict:
        """
        Analyze the impact of modifications.

        Args:
            original_scores: Original taste scores
            modified_scores: Modified taste scores
            original_balance: Original overall balance
            modified_balance: Modified overall balance

        Returns:
            Impact analysis dictionary
        """
        taste_changes = {}
        for dimension in original_scores:
            change = modified_scores[dimension] - original_scores[dimension]
            taste_changes[dimension] = {
                'change': float(change),
                'direction': 'increased' if change > 0 else 'decreased' if change < 0 else 'unchanged',
                'magnitude': abs(float(change)),
            }

        balance_change = modified_balance - original_balance

        return {
            'taste_dimension_changes': taste_changes,
            'balance_change': float(balance_change),
            'balance_improved': balance_change > 0,
            'summary': self._generate_impact_summary(taste_changes, balance_change),
        }

    def _generate_impact_summary(self, taste_changes: Dict, balance_change: float) -> str:
        """
        Generate human-readable summary of impact.

        Args:
            taste_changes: Dictionary of taste dimension changes
            balance_change: Change in overall balance

        Returns:
            Summary string
        """
        significant_changes = [(dim, change) for dim, change in taste_changes.items()
                              if change['magnitude'] > 0.1]

        if not significant_changes:
            return "Minor changes to flavor profile."

        summary_parts = []

        for dim, change in sorted(significant_changes, key=lambda x: x[1]['magnitude'], reverse=True):
            if change['direction'] != 'unchanged':
                summary_parts.append(f"{dim} {change['direction']} by {change['magnitude']:.2f}")

        summary = "; ".join(summary_parts[:3])  # Top 3 changes

        if balance_change > 0.01:
            summary += f". Overall balance improved by {balance_change:.3f}."
        elif balance_change < -0.01:
            summary += f". Overall balance decreased by {abs(balance_change):.3f}."

        return summary


class FlavorOptimizer:
    """Recommend improvements to cocktail balance."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize flavor optimizer.

        Args:
            data_dir: Directory containing data files
        """
        self.profiler = MolecularProfiler(data_dir)
        self.analyzer = CocktailAnalyzer(data_dir)
        self.modifier = CocktailModifier(data_dir)

        # Load ingredient list
        ingredient_file = Path("data/processed/ingredients_list.json")
        if ingredient_file.exists():
            with open(ingredient_file, 'r', encoding='utf-8') as f:
                self.available_ingredients = json.load(f)
        else:
            self.available_ingredients = []

    def recommend_improvements(self, cocktail_name: str, target_balance: Optional[str] = None) -> Dict:
        """
        Recommend modifications to improve cocktail balance.

        Args:
            cocktail_name: Name of cocktail to optimize
            target_balance: Optional target ('sweeter', 'more_sour', 'less_bitter', 'balanced')

        Returns:
            Dictionary with recommendations and predicted impacts
        """
        # Analyze current state
        analysis = self.analyzer.analyze_cocktail(cocktail_name)

        if 'error' in analysis:
            return analysis

        current_scores = analysis['balance_scores']
        current_balance = analysis['overall_balance']

        # Identify imbalances
        imbalances = self._identify_imbalances(current_scores, target_balance)

        # Generate recommendations
        recommendations = []

        for imbalance in imbalances:
            dimension = imbalance['dimension']
            issue_type = imbalance['type']  # 'too_high', 'too_low'

            # Find ingredients that can address this imbalance
            suggestions = self._find_corrective_ingredients(
                dimension, issue_type, current_scores, analysis['ingredients']
            )

            for suggestion in suggestions[:3]:  # Top 3 suggestions per imbalance
                recommendations.append({
                    'issue': f"{dimension} is {issue_type.replace('_', ' ')}",
                    'recommendation': suggestion,
                })

        return {
            'cocktail': cocktail_name,
            'current_balance': current_scores,
            'overall_balance_score': current_balance,
            'identified_issues': imbalances,
            'recommendations': recommendations,
        }

    def _identify_imbalances(self, taste_scores: Dict, target: Optional[str] = None) -> List[Dict]:
        """
        Identify flavor imbalances that should be addressed.

        Args:
            taste_scores: Current taste dimension scores
            target: Optional target balance

        Returns:
            List of imbalance dictionaries
        """
        imbalances = []

        if target:
            # User specified a target
            target_map = {
                'sweeter': ('sweet', 'increase'),
                'more_sour': ('sour', 'increase'),
                'less_bitter': ('bitter', 'decrease'),
                'more_aromatic': ('aromatic', 'increase'),
                'balanced': None,
            }

            if target in target_map and target_map[target]:
                dimension, direction = target_map[target]
                imbalances.append({
                    'dimension': dimension,
                    'type': 'too_low' if direction == 'increase' else 'too_high',
                    'priority': 'high',
                })

        # Auto-detect imbalances based on scores
        mean_score = np.mean(list(taste_scores.values()))
        std_score = np.std(list(taste_scores.values()))

        for dimension, score in taste_scores.items():
            # Too high if significantly above mean
            if score > mean_score + std_score:
                imbalances.append({
                    'dimension': dimension,
                    'type': 'too_high',
                    'priority': 'medium',
                    'current_value': score,
                })

            # Too low if significantly below mean AND below threshold
            elif score < mean_score - std_score and score < 0.3:
                imbalances.append({
                    'dimension': dimension,
                    'type': 'too_low',
                    'priority': 'medium',
                    'current_value': score,
                })

        return imbalances

    def _find_corrective_ingredients(self, dimension: str, issue_type: str,
                                    current_scores: Dict, existing_ingredients: List[str]) -> List[Dict]:
        """
        Find ingredients that can address a specific imbalance.

        Args:
            dimension: Taste dimension to correct
            issue_type: 'too_high' or 'too_low'
            current_scores: Current taste scores
            existing_ingredients: Ingredients already in cocktail

        Returns:
            List of ingredient suggestions with predicted impact
        """
        suggestions = []

        # Define ingredient categories by taste dimension
        dimension_ingredients = {
            'sweet': ['simple syrup', 'sugar', 'honey', 'agave syrup', 'grenadine', 'maple syrup'],
            'sour': ['lemon juice', 'lime juice', 'grapefruit juice', 'vinegar', 'citric acid'],
            'bitter': ['angostura bitters', 'campari', 'aperol', 'coffee', 'tonic water'],
            'aromatic': ['mint', 'basil', 'rosemary', 'thyme', 'bitters', 'orange bitters'],
            'savory': ['olive brine', 'celery', 'tomato juice', 'worcestershire sauce'],
        }

        # Determine action based on issue type
        if issue_type == 'too_low':
            # Need to increase this dimension
            action = 'add'
            candidate_ingredients = dimension_ingredients.get(dimension, [])
        else:
            # Need to decrease this dimension (dilute or add contrasting flavors)
            action = 'add_contrasting'
            # Find contrasting dimensions
            contrasting = {
                'sweet': 'sour',
                'sour': 'sweet',
                'bitter': 'sweet',
                'aromatic': 'sweet',
                'savory': 'sweet',
            }
            contrast_dim = contrasting.get(dimension, 'sweet')
            candidate_ingredients = dimension_ingredients.get(contrast_dim, [])

        # Filter to available ingredients not already in cocktail
        available_candidates = [ing for ing in candidate_ingredients
                               if ing in self.available_ingredients
                               and ing.lower() not in [e.lower() for e in existing_ingredients]]

        # Score each candidate
        for ingredient in available_candidates:
            profile = self.profiler.get_ingredient_profile(ingredient)

            if profile['num_molecules'] == 0:
                continue

            # Calculate expected impact
            target_score = profile['taste_scores'][dimension]

            suggestion = {
                'action': 'add',
                'ingredient': ingredient,
                'amount': 15.0,  # ml
                'reason': f"Add {ingredient} to {'increase' if issue_type == 'too_low' else 'balance'} {dimension}",
                'predicted_impact': {
                    dimension: f"+{target_score * 0.2:.2f}",  # Estimated impact
                },
                'ingredient_taste_profile': profile['taste_scores'],
            }

            suggestions.append(suggestion)

        # Sort by relevance (how well it addresses the issue)
        suggestions.sort(key=lambda x: x['ingredient_taste_profile'][dimension], reverse=(issue_type == 'too_low'))

        return suggestions[:5]  # Top 5


def main():
    """Test cocktail modifier and optimizer."""
    print("=== Cocktail Modification & Optimization ===\n")

    # Test modification
    print("Testing Cocktail Modification...")
    modifier = CocktailModifier(data_dir="raw")

    test_cocktail = "Margarita"
    print(f"\nModifying {test_cocktail}:")

    modifications = [
        {'action': 'add', 'ingredient': 'orange juice', 'amount': 30.0},
        {'action': 'increase', 'ingredient': 'lime juice', 'amount': 10.0},
    ]

    result = modifier.modify_cocktail(test_cocktail, modifications)

    if 'error' not in result:
        print(f"Original ingredients: {result['original']['ingredients']}")
        print(f"Modified ingredients: {result['modified']['ingredients']}")
        print(f"\nOriginal balance: {result['original']['overall_balance']:.3f}")
        print(f"Modified balance: {result['modified']['overall_balance']:.3f}")
        print(f"\nImpact: {result['impact_analysis']['summary']}")

    # Test optimization
    print("\n\n=== Flavor Optimization Recommendations ===\n")
    optimizer = FlavorOptimizer(data_dir="raw")

    test_cocktails = ['Martini', 'Mojito']

    for cocktail in test_cocktails:
        print(f"\n{cocktail.upper()}:")
        recommendations = optimizer.recommend_improvements(cocktail)

        if 'error' not in recommendations:
            print(f"Current balance score: {recommendations['overall_balance_score']:.3f}")
            print(f"Current taste profile: {recommendations['current_balance']}")

            if recommendations['identified_issues']:
                print(f"\nIdentified issues:")
                for issue in recommendations['identified_issues']:
                    print(f"  - {issue['dimension']} is {issue['type'].replace('_', ' ')}")

            if recommendations['recommendations']:
                print(f"\nTop recommendations:")
                for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                    print(f"  {i}. {rec['recommendation']['reason']}")
                    print(f"     Amount: {rec['recommendation']['amount']}ml")

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
