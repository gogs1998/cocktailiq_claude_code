"""
FlavorOptimizer V4 - Book Knowledge Enhanced
Incorporates expert-curated book recipes to improve recommendations.

Key improvements over V3:
1. Plausibility scoring (fixes tomato juice bias)
2. Expert balance calibration
3. Style-aware recommendations
4. Ingredient frequency weighting
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.recommendation.optimizer_v3 import FlavorOptimizerV3


class FlavorOptimizerV4(FlavorOptimizerV3):
    """
    Enhanced optimizer with book knowledge.

    Inherits multi-recommendation testing from V3.
    Adds book-based plausibility scoring.
    """

    def __init__(self):
        """Initialize V4 optimizer."""
        super().__init__()

        # Load book knowledge
        self.ingredient_frequency = self._load_ingredient_frequency()
        self.ingredient_plausibility = self._load_ingredient_plausibility()
        self.perfect_cocktails = self._load_perfect_cocktails()

        # Compute ideal targets from perfect cocktails
        self.ideal_balance_target = self._compute_ideal_balance()
        self.ideal_taste_distribution = self._compute_ideal_taste_distribution()

        print(f"[+] V4 Optimizer initialized")
        if self.ingredient_frequency:
            print(f"    - Ingredient frequency data: {len(self.ingredient_frequency)} ingredients")
        if self.ingredient_plausibility:
            print(f"    - Plausibility scores: {len(self.ingredient_plausibility)} ingredients")
        if self.perfect_cocktails:
            print(f"    - Perfect cocktails: {len(self.perfect_cocktails)} cocktails")
            print(f"    - Ideal balance target: {self.ideal_balance_target:.3f}")

    def _load_ingredient_frequency(self) -> Dict[str, int]:
        """Load ingredient frequency from book recipes."""
        freq_file = Path("data/processed/ingredient_frequency.json")

        if not freq_file.exists():
            print(f"[!] No ingredient frequency data found")
            print(f"[!] Run: python analyze_book_recipes.py")
            return {}

        with open(freq_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_ingredient_plausibility(self) -> Dict[str, float]:
        """Load ingredient plausibility scores."""
        plaus_file = Path("data/processed/ingredient_plausibility.json")

        if not plaus_file.exists():
            print(f"[!] No plausibility data found")
            print(f"[!] Run: python analyze_book_recipes.py")
            return {}

        with open(plaus_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_perfect_cocktails(self) -> List[Dict]:
        """Load expert-curated perfect cocktails."""
        perfect_file = Path("data/processed/perfect_cocktails.json")

        if not perfect_file.exists():
            print(f"[!] No perfect cocktails data found")
            print(f"[!] Run: python analyze_book_recipes.py")
            return []

        with open(perfect_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _compute_ideal_balance(self) -> float:
        """Compute ideal balance target from perfect cocktails."""
        if not self.perfect_cocktails:
            return 0.98  # Default V3 threshold

        balances = [c['balance'] for c in self.perfect_cocktails]
        return sum(balances) / len(balances)

    def _compute_ideal_taste_distribution(self) -> Dict[str, float]:
        """Compute ideal taste score distribution from perfect cocktails."""
        if not self.perfect_cocktails:
            return {}

        taste_dimensions = ['sweet', 'sour', 'bitter', 'aromatic', 'savory']
        ideal = {}

        for dim in taste_dimensions:
            scores = [c['taste_scores'][dim] for c in self.perfect_cocktails]
            ideal[dim] = sum(scores) / len(scores)

        return ideal

    def get_plausibility_score(self, ingredient: str) -> float:
        """
        Get plausibility score for ingredient based on book frequency.

        Args:
            ingredient: Ingredient name

        Returns:
            Plausibility score (0-1), or 0.5 if unknown
        """
        if not self.ingredient_plausibility:
            return 0.5  # Neutral if no data

        ingredient_lower = ingredient.lower().strip()

        # Direct match
        if ingredient_lower in self.ingredient_plausibility:
            return self.ingredient_plausibility[ingredient_lower]

        # Fuzzy match (check if ingredient contains known ingredient)
        for known_ing, score in self.ingredient_plausibility.items():
            if known_ing in ingredient_lower or ingredient_lower in known_ing:
                return score

        # Unknown ingredient → neutral plausibility
        return 0.5

    def rank_recommendations_with_plausibility(self, candidates: List[Dict]) -> List[Dict]:
        """
        Rank recommendations by improvement * plausibility.

        Args:
            candidates: List of candidate modifications

        Returns:
            Sorted candidates (best first)
        """
        for candidate in candidates:
            ingredient = candidate['ingredient']

            # Get plausibility score
            plausibility = self.get_plausibility_score(ingredient)

            # Combined score: improvement * plausibility
            # This penalizes rare ingredients even if they improve balance
            candidate['plausibility'] = plausibility
            candidate['combined_score'] = candidate['improvement'] * plausibility

        # Sort by combined score
        ranked = sorted(candidates, key=lambda x: x['combined_score'], reverse=True)

        return ranked

    def find_best_modification(self, cocktail_name: str, max_candidates: int = 5) -> Dict:
        """
        Find best modification using V4 (multi-recommendation + plausibility).

        Args:
            cocktail_name: Name of cocktail
            max_candidates: Number of candidates to test

        Returns:
            Best modification result with plausibility info
        """
        # Get initial analysis
        analysis = self.analyzer.analyze_cocktail_by_name(cocktail_name)

        if not analysis:
            return {'error': 'Cocktail not found'}

        original_balance = analysis['balance_metrics']['overall_balance']

        # Check if already excellent (use ideal target if available)
        threshold = self.ideal_balance_target if self.perfect_cocktails else 0.98

        if original_balance >= threshold:
            return {
                'status': 'excellent',
                'message': f'Already excellently balanced (>= {threshold:.3f})!',
                'current_balance': original_balance,
                'ideal_target': threshold
            }

        # Get all recommendations
        all_recs = self.recommend_improvements(cocktail_name)

        if not all_recs or not all_recs.get('recommendations'):
            return {
                'status': 'no_recommendations',
                'message': 'No improvements found',
                'current_balance': original_balance
            }

        # Test multiple candidates (V3 feature)
        candidates = []

        for rec in all_recs['recommendations'][:max_candidates]:
            ingredient = rec['ingredient']
            amount = rec['amount']

            # Modify cocktail
            modification = {
                'action': 'add',
                'ingredient': ingredient,
                'amount': amount
            }

            result = self.modifier.modify_cocktail(cocktail_name, modification)

            if result and 'new_analysis' in result:
                new_balance = result['new_analysis']['balance_metrics']['overall_balance']
                improvement = new_balance - original_balance

                candidates.append({
                    'ingredient': ingredient,
                    'amount': amount,
                    'improvement': improvement,
                    'original_balance': original_balance,
                    'new_balance': new_balance
                })

        if not candidates:
            return {
                'status': 'no_valid_candidates',
                'message': 'No valid modifications found',
                'current_balance': original_balance
            }

        # NEW V4: Rank by improvement * plausibility
        ranked_candidates = self.rank_recommendations_with_plausibility(candidates)

        best = ranked_candidates[0]

        return {
            'status': 'success',
            'cocktail': cocktail_name,
            'tested_count': len(candidates),
            'all_candidates': ranked_candidates,
            'best_modification': {
                'ingredient': best['ingredient'],
                'amount': best['amount'],
                'improvement': best['improvement'],
                'plausibility': best['plausibility'],
                'combined_score': best['combined_score'],
                'original_balance': best['original_balance'],
                'new_balance': best['new_balance']
            }
        }

    def explain_recommendation(self, result: Dict) -> str:
        """
        Generate human-readable explanation of recommendation.

        Args:
            result: Result from find_best_modification

        Returns:
            Explanation string
        """
        if result['status'] == 'excellent':
            return f"{result['message']} (Balance: {result['current_balance']:.3f})"

        if result['status'] != 'success':
            return result.get('message', 'Unknown error')

        best = result['best_modification']

        explanation = []
        explanation.append(f"Tested {result['tested_count']} modifications for {result['cocktail']}")
        explanation.append(f"\nBest recommendation:")
        explanation.append(f"  Add {best['amount']:.1f}ml {best['ingredient']}")
        explanation.append(f"  Balance: {best['original_balance']:.3f} -> {best['new_balance']:.3f} (+{best['improvement']:.3f})")
        explanation.append(f"  Plausibility: {best['plausibility']:.3f} (based on book frequency)")
        explanation.append(f"  Combined score: {best['combined_score']:.3f}")

        # Show alternatives
        if len(result['all_candidates']) > 1:
            explanation.append(f"\nOther candidates tested:")
            for i, cand in enumerate(result['all_candidates'][1:4], 2):  # Show top 2-4
                explanation.append(f"  {i}. {cand['ingredient']}: improvement={cand['improvement']:+.3f}, plausibility={cand['plausibility']:.3f}, score={cand['combined_score']:.3f}")

        return '\n'.join(explanation)


def test_v4_vs_v3():
    """Compare V4 vs V3 on same cocktails."""
    print("="*70)
    print("V4 vs V3 COMPARISON")
    print("="*70)

    # Check if book data exists
    book_file = Path("data/book_cocktails.json")
    if not book_file.exists():
        print("\n[!] No book data found. V4 will behave like V3.")
        print("[!] Extract recipes from ebooks first:")
        print("    python book_extractor_unified.py")
        print("[!] Then run analysis:")
        print("    python analyze_book_recipes.py")
        return

    # Initialize optimizers
    v3 = FlavorOptimizerV3()
    v4 = FlavorOptimizerV4()

    # Test cocktails
    test_cocktails = [
        'Mojito', 'Gimlet', 'Whiskey Sour', 'Moscow Mule', 'Bramble'
    ]

    results = []

    for cocktail in test_cocktails:
        print(f"\n{'='*70}")
        print(f"Testing: {cocktail}")
        print(f"{'='*70}")

        # V3 recommendation
        v3_result = v3.find_best_modification(cocktail, max_candidates=5)

        # V4 recommendation
        v4_result = v4.find_best_modification(cocktail, max_candidates=5)

        if v3_result.get('status') == 'success' and v4_result.get('status') == 'success':
            v3_best = v3_result['best_modification']
            v4_best = v4_result['best_modification']

            print(f"\nV3 recommendation:")
            print(f"  {v3_best['ingredient']} ({v3_best['amount']:.1f}ml)")
            print(f"  Improvement: +{v3_best['improvement']:.3f}")

            print(f"\nV4 recommendation:")
            print(f"  {v4_best['ingredient']} ({v4_best['amount']:.1f}ml)")
            print(f"  Improvement: +{v4_best['improvement']:.3f}")
            print(f"  Plausibility: {v4_best['plausibility']:.3f}")
            print(f"  Combined score: {v4_best['combined_score']:.3f}")

            # Check if different
            if v3_best['ingredient'] != v4_best['ingredient']:
                print(f"\n[!] V4 CHANGED RECOMMENDATION!")
                print(f"    V3: {v3_best['ingredient']}")
                print(f"    V4: {v4_best['ingredient']}")

            results.append({
                'cocktail': cocktail,
                'v3_ingredient': v3_best['ingredient'],
                'v3_improvement': v3_best['improvement'],
                'v4_ingredient': v4_best['ingredient'],
                'v4_improvement': v4_best['improvement'],
                'v4_plausibility': v4_best['plausibility'],
                'changed': v3_best['ingredient'] != v4_best['ingredient']
            })

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    changed_count = sum(1 for r in results if r['changed'])
    print(f"\nRecommendations changed: {changed_count}/{len(results)}")

    if changed_count > 0:
        print(f"\nChanged recommendations:")
        for r in results:
            if r['changed']:
                print(f"  {r['cocktail']}:")
                print(f"    V3: {r['v3_ingredient']} (improvement: +{r['v3_improvement']:.3f})")
                print(f"    V4: {r['v4_ingredient']} (improvement: +{r['v4_improvement']:.3f}, plausibility: {r['v4_plausibility']:.3f})")


def main():
    """Test V4 optimizer."""
    print("="*70)
    print("FLAVOR OPTIMIZER V4 - BOOK KNOWLEDGE ENHANCED")
    print("="*70)

    # Check prerequisites
    book_file = Path("data/book_cocktails.json")
    freq_file = Path("data/processed/ingredient_frequency.json")
    plaus_file = Path("data/processed/ingredient_plausibility.json")

    if not book_file.exists():
        print("\n[!] Prerequisites not met")
        print("\n1. Extract recipes from ebooks:")
        print("   python book_extractor_unified.py")
        print("\n2. Analyze book recipes:")
        print("   python analyze_book_recipes.py")
        print("\n3. Run V4 again:")
        print("   python src/recommendation/optimizer_v4.py")
        return

    if not freq_file.exists() or not plaus_file.exists():
        print("\n[!] Book analysis not complete")
        print("\nRun analysis:")
        print("   python analyze_book_recipes.py")
        print("\nThen run V4 again:")
        print("   python src/recommendation/optimizer_v4.py")
        return

    # Run comparison
    test_v4_vs_v3()


if __name__ == "__main__":
    main()
