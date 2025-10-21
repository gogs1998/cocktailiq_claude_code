"""
Cocktail Optimizer V2 - IMPROVED
Adaptive amounts, smart thresholds, enhanced ingredient mappings.

Improvements over V1:
- Adaptive recommendation amounts based on current balance
- Threshold logic (don't fix excellent cocktails)
- Volume-aware scaling
- Spirit fallback mappings
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from collections import defaultdict

from ..analysis.molecular_profile import MolecularProfiler, CocktailAnalyzer
from ..recommendation.optimizer import CocktailModifier


# Enhanced spirit mappings for better ingredient coverage
SPIRIT_FALLBACK_MAPPINGS = {
    'rum': ['sugar cane', 'molasses'],
    'light rum': ['sugar cane', 'citrus'],
    'dark rum': ['molasses', 'caramel', 'vanilla'],
    'white rum': ['sugar cane'],
    'spiced rum': ['sugar cane', 'cinnamon', 'vanilla'],
    'tequila': ['agave'],
    'bourbon': ['corn', 'oak', 'vanilla'],
    'whiskey': ['grain', 'malt', 'oak'],
    'whisky': ['grain', 'malt', 'oak'],
    'scotch': ['malt', 'peat', 'oak'],
    'rye': ['grain', 'spice'],
    'vodka': ['grain'],
    'triple sec': ['orange', 'citrus'],
    'cointreau': ['orange', 'citrus'],
    'grand marnier': ['orange', 'cognac'],
    'campari': ['bitter orange', 'herbs'],
    'aperol': ['orange', 'herbs'],
    'angostura bitters': ['spice', 'herbs'],
    'orange bitters': ['orange'],
    'simple syrup': ['sugar'],
    'sugar syrup': ['sugar'],
    'soda water': ['water'],
    'club soda': ['water'],
}


class FlavorOptimizerV2:
    """
    Improved recommendation engine with adaptive amounts and smart thresholds.
    """

    def __init__(self, data_dir: str = "raw"):
        """Initialize improved optimizer."""
        self.profiler = MolecularProfiler(data_dir)
        self.analyzer = CocktailAnalyzer(data_dir)
        self.modifier = CocktailModifier(data_dir)

        # Enhance profiler with spirit mappings
        self._enhance_ingredient_mappings()

        # Load ingredient list
        ingredient_file = Path("data/processed/ingredients_list.json")
        if ingredient_file.exists():
            with open(ingredient_file, 'r', encoding='utf-8') as f:
                self.available_ingredients = json.load(f)
        else:
            self.available_ingredients = []

    def _enhance_ingredient_mappings(self):
        """Add fallback mappings for spirits and liqueurs."""
        # Extend the flavor loader's fuzzy matching
        original_fuzzy = self.profiler.flavor_loader._fuzzy_match_ingredient

        def enhanced_fuzzy_match(ingredient: str):
            # Try original
            molecules = original_fuzzy(ingredient)

            # If still empty, try spirit mappings
            if not molecules and ingredient.lower() in SPIRIT_FALLBACK_MAPPINGS:
                for base in SPIRIT_FALLBACK_MAPPINGS[ingredient.lower()]:
                    molecules.extend(
                        self.profiler.flavor_loader.molecules_by_source.get(base.lower(), [])
                    )

            return molecules

        # Monkey patch (not ideal but works for proof-of-concept)
        self.profiler.flavor_loader._fuzzy_match_ingredient = enhanced_fuzzy_match

    def _calculate_adaptive_amount(self, current_balance: float,
                                   imbalance_magnitude: float,
                                   total_volume: float) -> float:
        """
        Calculate context-aware recommendation amount.

        Args:
            current_balance: Current overall balance score (0-1)
            imbalance_magnitude: How far dimension is from mean
            total_volume: Total cocktail volume in ml

        Returns:
            Recommended amount in ml
        """
        # Base amount as percentage of total volume
        base_percentage = 0.12  # 12% of total volume

        # Balance factor - reduce for already-balanced cocktails
        if current_balance >= 0.98:
            balance_factor = 0.0  # Don't recommend anything
        elif current_balance >= 0.95:
            balance_factor = 0.25  # Very small adjustments only
        elif current_balance >= 0.90:
            balance_factor = 0.5  # Moderate adjustments
        elif current_balance >= 0.80:
            balance_factor = 0.75  # Larger adjustments
        else:
            balance_factor = 1.0  # Full adjustments

        # Severity factor - increase for severe imbalances
        severity_factor = min(imbalance_magnitude / 0.3, 2.0)

        # Calculate final amount
        amount = total_volume * base_percentage * balance_factor * severity_factor

        # Bounds: 5ml minimum, 30ml maximum
        return round(max(5.0, min(amount, 30.0)), 1)

    def should_recommend_changes(self, balance_score: float,
                                taste_scores: Dict) -> tuple[bool, str]:
        """
        Determine if cocktail actually needs changes.

        Args:
            balance_score: Overall balance score
            taste_scores: Individual dimension scores

        Returns:
            (should_recommend, message)
        """
        # Excellent cocktails - no changes
        if balance_score >= 0.98:
            return False, "Cocktail is already excellently balanced! No changes recommended."

        # Very good cocktails - only if clear issue
        if balance_score >= 0.95:
            # Check if any dimension is VERY far off
            mean = np.mean(list(taste_scores.values()))
            max_deviation = max(abs(score - mean) for score in taste_scores.values())

            if max_deviation < 0.25:
                return False, "Cocktail is very well balanced. Only minor refinements possible."

        # Good cocktails - suggest refinements
        if balance_score >= 0.85:
            return True, "Good cocktail with room for refinement"

        # Needs work
        return True, "Cocktail has imbalances that could be improved"

    def recommend_improvements(self, cocktail_name: str,
                              target_balance: Optional[str] = None) -> Dict:
        """
        Recommend improvements with adaptive amounts and smart thresholds.

        Args:
            cocktail_name: Name of cocktail
            target_balance: Optional target

        Returns:
            Recommendations with adaptive amounts
        """
        # Analyze current state
        analysis = self.analyzer.analyze_cocktail(cocktail_name)

        if 'error' in analysis:
            return analysis

        current_scores = analysis['balance_scores']
        current_balance = analysis['overall_balance']
        total_volume = analysis['aggregated_profile'].get('total_volume', 100.0)

        # SMART THRESHOLD CHECK
        should_rec, message = self.should_recommend_changes(current_balance, current_scores)

        if not should_rec:
            return {
                'cocktail': cocktail_name,
                'current_balance': current_scores,
                'overall_balance_score': current_balance,
                'message': message,
                'identified_issues': [],
                'recommendations': []
            }

        # Identify imbalances
        imbalances = self._identify_imbalances(current_scores, target_balance)

        # Generate recommendations with ADAPTIVE AMOUNTS
        recommendations = []

        for imbalance in imbalances:
            dimension = imbalance['dimension']
            issue_type = imbalance['type']

            # Calculate imbalance magnitude
            mean = np.mean(list(current_scores.values()))
            imbalance_mag = abs(current_scores[dimension] - mean)

            # Find corrective ingredients
            suggestions = self._find_corrective_ingredients(
                dimension, issue_type, current_scores, analysis['ingredients']
            )

            for suggestion in suggestions[:3]:
                # ADAPTIVE AMOUNT
                adaptive_amount = self._calculate_adaptive_amount(
                    current_balance,
                    imbalance_mag,
                    total_volume
                )

                suggestion['amount'] = adaptive_amount
                suggestion['reason'] = f"Add {suggestion['ingredient']} ({adaptive_amount}ml) to {'increase' if issue_type == 'too_low' else 'balance'} {dimension}"

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
        Identify flavor imbalances (same as V1).
        """
        imbalances = []

        if target:
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

        # Auto-detect imbalances
        mean_score = np.mean(list(taste_scores.values()))
        std_score = np.std(list(taste_scores.values()))

        for dimension, score in taste_scores.items():
            if score > mean_score + std_score * 0.7:  # Stricter threshold
                imbalances.append({
                    'dimension': dimension,
                    'type': 'too_high',
                    'priority': 'medium',
                    'current_value': score,
                })
            elif score < mean_score - std_score * 0.7 and score < 0.3:
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
        Find ingredients to correct imbalance (same as V1).
        """
        suggestions = []

        # Ingredient categories by dimension
        dimension_ingredients = {
            'sweet': ['simple syrup', 'honey', 'agave syrup', 'sugar'],
            'sour': ['lemon juice', 'lime juice', 'grapefruit juice'],
            'bitter': ['angostura bitters', 'campari', 'coffee'],
            'aromatic': ['mint', 'basil', 'bitters'],
            'savory': ['celery', 'tomato juice'],
        }

        if issue_type == 'too_low':
            candidate_ingredients = dimension_ingredients.get(dimension, [])
        else:
            # Add contrasting flavor
            contrasting = {
                'sweet': 'sour',
                'sour': 'sweet',
                'bitter': 'sweet',
                'aromatic': 'sweet',
                'savory': 'sweet',
            }
            contrast_dim = contrasting.get(dimension, 'sweet')
            candidate_ingredients = dimension_ingredients.get(contrast_dim, [])

        # Filter and score
        for ingredient in candidate_ingredients:
            if ingredient.lower() not in [e.lower() for e in existing_ingredients]:
                profile = self.profiler.get_ingredient_profile(ingredient)

                if profile['num_molecules'] > 0:
                    suggestion = {
                        'action': 'add',
                        'ingredient': ingredient,
                        'amount': 15.0,  # Will be overridden by adaptive amount
                        'predicted_impact': {dimension: f"+0.15"},
                        'ingredient_taste_profile': profile['taste_scores'],
                    }
                    suggestions.append(suggestion)

        # Sort by relevance
        suggestions.sort(
            key=lambda x: x['ingredient_taste_profile'][dimension],
            reverse=(issue_type == 'too_low')
        )

        return suggestions[:5]


def main():
    """Test improved optimizer."""
    print("="*70)
    print("OPTIMIZER V2 - IMPROVED WITH ADAPTIVE AMOUNTS")
    print("="*70)

    optimizer = FlavorOptimizerV2(data_dir="raw")

    test_cocktails = [
        ('Margarita', 0.993),  # Excellent balance
        ('Mojito', 0.973),     # Excellent balance
        ('Gimlet', 0.914),     # Good balance
        ('Manhattan', 0.878),  # Decent balance
    ]

    print("\nTesting threshold logic and adaptive amounts...")
    print("-"*70)

    for cocktail, expected_balance in test_cocktails:
        print(f"\n{cocktail.upper()}:")
        recs = optimizer.recommend_improvements(cocktail)

        if 'error' in recs:
            print(f"  Error: {recs['error']}")
            continue

        print(f"  Current balance: {recs['overall_balance_score']:.3f}")

        if 'message' in recs:
            print(f"  Status: {recs['message']}")

        if recs['recommendations']:
            print(f"  Top recommendation:")
            top = recs['recommendations'][0]['recommendation']
            print(f"    {top['reason']}")
            print(f"    Amount: {top['amount']}ml (adaptive)")
        else:
            print(f"  No recommendations (already excellent)")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
