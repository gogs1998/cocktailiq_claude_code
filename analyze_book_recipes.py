"""
Book Recipe Analyzer
Analyze cocktail recipes from books to:
1. Build ingredient frequency database
2. Identify expert-curated 'perfect' cocktails
3. Extract balance patterns
4. Fix recommendation bias
"""

import json
from pathlib import Path
from typing import List, Dict
from collections import Counter, defaultdict
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from analysis.molecular_profile import CocktailAnalyzer


class BookRecipeAnalyzer:
    """Analyze cocktail recipes from expert books."""

    def __init__(self):
        """Initialize analyzer."""
        self.book_file = Path("data/book_cocktails.json")
        self.db_file = Path("data/processed/cocktails.json")
        self.analyzer = CocktailAnalyzer()

        self.book_recipes = []
        self.db_recipes = []

        self._load_data()

    def _load_data(self):
        """Load book and database recipes."""
        # Load book recipes
        if self.book_file.exists():
            with open(self.book_file, 'r', encoding='utf-8') as f:
                self.book_recipes = json.load(f)
            print(f"[+] Loaded {len(self.book_recipes)} book recipes")
        else:
            print(f"[!] No book recipes found at {self.book_file}")
            print("[!] Run book_extractor_unified.py first to add recipes")

        # Load database recipes
        if self.db_file.exists():
            with open(self.db_file, 'r', encoding='utf-8') as f:
                self.db_recipes = json.load(f)
            print(f"[+] Loaded {len(self.db_recipes)} database recipes")

    def analyze_ingredient_frequency(self) -> Dict[str, int]:
        """
        Build ingredient frequency database from book recipes.

        Returns:
            Dictionary of ingredient -> count
        """
        print("\n" + "="*60)
        print("INGREDIENT FREQUENCY ANALYSIS")
        print("="*60)

        ingredient_counts = Counter()

        for recipe in self.book_recipes:
            for ing in recipe.get('ingredients', []):
                name = ing['name'].lower().strip()
                ingredient_counts[name] += 1

        print(f"\nTotal unique ingredients: {len(ingredient_counts)}")
        print(f"\nTop 30 most common ingredients:")
        print(f"{'Ingredient':<30} {'Count':>10} {'Frequency':>12}")
        print("-"*60)

        total_recipes = len(self.book_recipes)
        for ingredient, count in ingredient_counts.most_common(30):
            frequency = (count / total_recipes) * 100
            print(f"{ingredient:<30} {count:>10} {frequency:>11.1f}%")

        # Save to file
        output_file = Path("data/processed/ingredient_frequency.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dict(ingredient_counts), f, indent=2)

        print(f"\n[+] Saved to {output_file}")

        return dict(ingredient_counts)

    def identify_perfect_cocktails(self, balance_threshold: float = 0.98) -> List[Dict]:
        """
        Identify expert-curated 'perfect' cocktails from books.

        Args:
            balance_threshold: Minimum balance score

        Returns:
            List of perfect cocktails with analysis
        """
        print("\n" + "="*60)
        print("EXPERT-CURATED PERFECT COCKTAILS")
        print("="*60)

        perfect_cocktails = []

        for recipe in self.book_recipes:
            # Analyze molecular profile
            analysis = self.analyzer.analyze_cocktail(recipe)

            balance = analysis['balance_metrics']['overall_balance']

            if balance >= balance_threshold:
                perfect_cocktails.append({
                    'name': recipe['name'],
                    'source_book': recipe.get('source_book', 'Unknown'),
                    'balance': balance,
                    'complexity': analysis['balance_metrics']['complexity'],
                    'taste_scores': analysis['taste_scores'],
                    'ingredients': recipe.get('ingredients', [])
                })

        print(f"\nFound {len(perfect_cocktails)} perfectly balanced cocktails (>={balance_threshold})")

        if perfect_cocktails:
            print(f"\n{'Cocktail':<30} {'Book':<25} {'Balance':>10}")
            print("-"*70)
            for cocktail in sorted(perfect_cocktails, key=lambda x: x['balance'], reverse=True):
                print(f"{cocktail['name']:<30} {cocktail['source_book']:<25} {cocktail['balance']:>10.3f}")

            # Compute ideal balance ranges from these cocktails
            avg_balance = sum(c['balance'] for c in perfect_cocktails) / len(perfect_cocktails)
            avg_complexity = sum(c['complexity'] for c in perfect_cocktails) / len(perfect_cocktails)

            print(f"\nIdeal targets from expert cocktails:")
            print(f"  Average balance: {avg_balance:.3f}")
            print(f"  Average complexity: {avg_complexity:.3f}")

            # Average taste score distribution
            taste_dimensions = ['sweet', 'sour', 'bitter', 'aromatic', 'savory']
            avg_taste_scores = {}

            for dim in taste_dimensions:
                scores = [c['taste_scores'][dim] for c in perfect_cocktails]
                avg_taste_scores[dim] = sum(scores) / len(scores)

            print(f"\n  Ideal taste score distribution:")
            for dim, score in sorted(avg_taste_scores.items(), key=lambda x: x[1], reverse=True):
                print(f"    {dim.capitalize():<15} {score:.3f}")

        # Save
        output_file = Path("data/processed/perfect_cocktails.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(perfect_cocktails, f, indent=2)

        print(f"\n[+] Saved to {output_file}")

        return perfect_cocktails

    def compare_book_vs_database(self):
        """Compare book recipes vs database recipes."""
        print("\n" + "="*60)
        print("BOOK vs DATABASE COMPARISON")
        print("="*60)

        # Analyze book recipes
        book_balances = []
        for recipe in self.book_recipes:
            analysis = self.analyzer.analyze_cocktail(recipe)
            book_balances.append(analysis['balance_metrics']['overall_balance'])

        # Analyze database recipes (sample)
        db_balances = []
        for recipe in self.db_recipes[:100]:  # Sample 100
            try:
                analysis = self.analyzer.analyze_cocktail(recipe)
                db_balances.append(analysis['balance_metrics']['overall_balance'])
            except:
                pass

        if book_balances:
            avg_book = sum(book_balances) / len(book_balances)
            print(f"\nBook recipes average balance: {avg_book:.3f}")

        if db_balances:
            avg_db = sum(db_balances) / len(db_balances)
            print(f"Database recipes average balance: {avg_db:.3f}")

        if book_balances and db_balances:
            diff = avg_book - avg_db
            print(f"\nDifference: {diff:+.3f} (book recipes are {'better' if diff > 0 else 'worse'})")

    def identify_missing_styles(self):
        """Identify cocktail styles underrepresented in database."""
        print("\n" + "="*60)
        print("STYLE ANALYSIS")
        print("="*60)

        # Classify by base spirit
        book_spirits = defaultdict(int)
        db_spirits = defaultdict(int)

        spirit_keywords = {
            'vodka': 'vodka',
            'gin': 'gin',
            'rum': 'rum',
            'tequila': 'tequila',
            'whiskey': 'whiskey',
            'bourbon': 'whiskey',
            'scotch': 'whiskey',
            'brandy': 'brandy',
            'cognac': 'brandy',
            'mezcal': 'mezcal',
        }

        for recipe in self.book_recipes:
            for ing in recipe.get('ingredients', []):
                name = ing['name'].lower()
                for keyword, spirit in spirit_keywords.items():
                    if keyword in name:
                        book_spirits[spirit] += 1
                        break

        for recipe in self.db_recipes:
            for ing in recipe.get('ingredients', []):
                name = ing['name'].lower()
                for keyword, spirit in spirit_keywords.items():
                    if keyword in name:
                        db_spirits[spirit] += 1
                        break

        print(f"\n{'Spirit':<15} {'Book Count':>12} {'DB Count':>12} {'Difference':>12}")
        print("-"*60)

        all_spirits = set(book_spirits.keys()) | set(db_spirits.keys())
        for spirit in sorted(all_spirits):
            book_count = book_spirits.get(spirit, 0)
            db_count = db_spirits.get(spirit, 0)
            diff = book_count - db_count
            print(f"{spirit:<15} {book_count:>12} {db_count:>12} {diff:>12}")

    def build_plausibility_scores(self, ingredient_frequency: Dict[str, int]) -> Dict[str, float]:
        """
        Build plausibility scores for ingredients based on book frequency.

        Args:
            ingredient_frequency: Ingredient -> count from books

        Returns:
            Ingredient -> plausibility score (0-1)
        """
        print("\n" + "="*60)
        print("PLAUSIBILITY SCORES")
        print("="*60)

        if not ingredient_frequency:
            print("[!] No ingredient frequency data")
            return {}

        max_count = max(ingredient_frequency.values())

        plausibility = {}
        for ingredient, count in ingredient_frequency.items():
            # Log-scaled plausibility
            # Common ingredients (count >> 1) → score near 1.0
            # Rare ingredients (count = 1) → score near 0.0
            import math
            score = math.log(count + 1) / math.log(max_count + 1)
            plausibility[ingredient] = score

        print(f"\nComputed plausibility scores for {len(plausibility)} ingredients")

        # Show examples
        print(f"\nHigh plausibility (common in books):")
        sorted_by_score = sorted(plausibility.items(), key=lambda x: x[1], reverse=True)
        for ingredient, score in sorted_by_score[:10]:
            count = ingredient_frequency[ingredient]
            print(f"  {ingredient:<30} {score:.3f} (appears in {count} recipes)")

        print(f"\nLow plausibility (rare in books):")
        for ingredient, score in sorted_by_score[-10:]:
            count = ingredient_frequency[ingredient]
            print(f"  {ingredient:<30} {score:.3f} (appears in {count} recipes)")

        # Save
        output_file = Path("data/processed/ingredient_plausibility.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plausibility, f, indent=2)

        print(f"\n[+] Saved to {output_file}")

        return plausibility

    def generate_full_report(self):
        """Generate comprehensive analysis report."""
        print("\n" + "="*70)
        print("BOOK RECIPE ANALYSIS - FULL REPORT")
        print("="*70)

        if not self.book_recipes:
            print("\n[!] No book recipes found. Run book_extractor_unified.py first.")
            return

        # 1. Ingredient frequency
        ingredient_frequency = self.analyze_ingredient_frequency()

        # 2. Perfect cocktails
        perfect_cocktails = self.identify_perfect_cocktails(balance_threshold=0.98)

        # 3. Compare book vs database
        self.compare_book_vs_database()

        # 4. Style analysis
        self.identify_missing_styles()

        # 5. Plausibility scores
        plausibility = self.build_plausibility_scores(ingredient_frequency)

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\nBook recipes: {len(self.book_recipes)}")
        print(f"Unique ingredients: {len(ingredient_frequency)}")
        print(f"Perfect cocktails (>=0.98): {len(perfect_cocktails)}")
        print(f"Plausibility scores computed: {len(plausibility)}")

        print("\nKey insights for V4 optimizer:")
        print("  [+] Use ingredient_frequency.json to weight recommendations")
        print("  [+] Use perfect_cocktails.json to calibrate balance targets")
        print("  [+] Use ingredient_plausibility.json to penalize rare ingredients")

        print("\nExpected improvements:")
        print("  [+] Fix tomato juice bias (low plausibility score)")
        print("  [+] Prioritize common cocktail ingredients")
        print("  [+] Better balance targets from expert cocktails")


def main():
    """Run analysis."""
    analyzer = BookRecipeAnalyzer()

    if not analyzer.book_recipes:
        print("\n" + "="*70)
        print("NO BOOK RECIPES FOUND")
        print("="*70)
        print("\nPlease extract recipes from your ebooks first:")
        print("  python book_extractor_unified.py")
        print("\nThen run this analysis again:")
        print("  python analyze_book_recipes.py")
        return

    analyzer.generate_full_report()


if __name__ == "__main__":
    main()
