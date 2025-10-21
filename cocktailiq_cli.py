"""
CocktailIQ Command Line Interface
Interactive tool for cocktail analysis and optimization.
"""

import sys
import json
from pathlib import Path

from src.analysis.molecular_profile import CocktailAnalyzer
from src.recommendation.optimizer import CocktailModifier, FlavorOptimizer


class CocktailIQCLI:
    """Interactive CLI for CocktailIQ."""

    def __init__(self):
        """Initialize CLI components."""
        print("Initializing CocktailIQ...")
        self.analyzer = CocktailAnalyzer(data_dir="raw")
        self.modifier = CocktailModifier(data_dir="raw")
        self.optimizer = FlavorOptimizer(data_dir="raw")
        print("Ready!\n")

    def analyze_cocktail(self, name: str):
        """
        Analyze a cocktail and display flavor profile.

        Args:
            name: Cocktail name
        """
        print(f"\n{'='*60}")
        print(f"ANALYZING: {name}")
        print(f"{'='*60}\n")

        analysis = self.analyzer.analyze_cocktail(name)

        if 'error' in analysis:
            print(f"Error: {analysis['error']}")
            return

        # Display basic info
        print(f"Category: {analysis['category']}")
        print(f"Ingredients ({analysis['num_ingredients']}):")
        for i, ing in enumerate(analysis['ingredients'], 1):
            print(f"  {i}. {ing}")

        # Display flavor scores
        print(f"\n{'-'*60}")
        print("FLAVOR BALANCE SCORES (0-1 scale)")
        print(f"{'-'*60}")

        scores = analysis['balance_scores']
        for dimension, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            bar = '#' * int(score * 40)
            print(f"  {dimension.capitalize():10s} [{score:.3f}] {bar}")

        # Overall metrics
        print(f"\n{'-'*60}")
        print("OVERALL METRICS")
        print(f"{'-'*60}")
        print(f"  Balance Score:    {analysis['overall_balance']:.3f} ", end='')
        self._print_rating(analysis['overall_balance'])
        print(f"  Complexity Score: {analysis['complexity_score']:.3f} ", end='')
        self._print_rating(analysis['complexity_score'])

        # Top flavor keywords
        if analysis['aggregated_profile']['flavor_keywords']:
            print(f"\n{'-'*60}")
            print("TOP FLAVOR NOTES")
            print(f"{'-'*60}")
            top_flavors = list(analysis['aggregated_profile']['flavor_keywords'].items())[:8]
            for flavor, intensity in top_flavors:
                print(f"  • {flavor}")

    def get_recommendations(self, name: str, target: str = None):
        """
        Get improvement recommendations for a cocktail.

        Args:
            name: Cocktail name
            target: Optional target ('sweeter', 'more_sour', 'less_bitter', 'balanced')
        """
        print(f"\n{'='*60}")
        print(f"RECOMMENDATIONS FOR: {name}")
        if target:
            print(f"Target: {target}")
        print(f"{'='*60}\n")

        recommendations = self.optimizer.recommend_improvements(name, target)

        if 'error' in recommendations:
            print(f"Error: {recommendations['error']}")
            return

        # Current state
        print("CURRENT STATE")
        print(f"{'-'*60}")
        print(f"Overall Balance: {recommendations['overall_balance_score']:.3f}")

        scores = recommendations['current_balance']
        print("\nTaste Profile:")
        for dimension, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {dimension.capitalize():10s} [{score:.3f}]")

        # Identified issues
        if recommendations['identified_issues']:
            print(f"\n{'-'*60}")
            print("IDENTIFIED ISSUES")
            print(f"{'-'*60}")
            for issue in recommendations['identified_issues']:
                symbol = '!' if issue['priority'] == 'high' else '*'
                print(f"  {symbol} {issue['dimension'].upper()} is {issue['type'].replace('_', ' ')}")

        # Recommendations
        if recommendations['recommendations']:
            print(f"\n{'-'*60}")
            print("SUGGESTED MODIFICATIONS")
            print(f"{'-'*60}")

            for i, rec in enumerate(recommendations['recommendations'][:5], 1):
                suggestion = rec['recommendation']
                print(f"\n  {i}. {suggestion['reason'].upper()}")
                print(f"     Ingredient: {suggestion['ingredient']}")
                print(f"     Amount:     {suggestion['amount']} ml")
                print(f"     Impact:     {suggestion['predicted_impact']}")
        else:
            print(f"\n✓ Cocktail is well-balanced! No major changes recommended.")

    def modify_and_compare(self, name: str, modifications: list):
        """
        Apply modifications and show before/after comparison.

        Args:
            name: Cocktail name
            modifications: List of modification dictionaries
        """
        print(f"\n{'='*60}")
        print(f"MODIFYING: {name}")
        print(f"{'='*60}\n")

        result = self.modifier.modify_cocktail(name, modifications)

        if 'error' in result:
            print(f"Error: {result['error']}")
            return

        # Show modifications
        print("MODIFICATIONS APPLIED:")
        for mod in modifications:
            if mod['action'] == 'add':
                print(f"  + Add {mod['ingredient']} ({mod['amount']}ml)")
            elif mod['action'] == 'increase':
                print(f"  ↑ Increase {mod['ingredient']} by {mod['amount']}ml")
            elif mod['action'] == 'decrease':
                print(f"  ↓ Decrease {mod['ingredient']} by {mod['amount']}ml")

        # Comparison
        print(f"\n{'-'*60}")
        print("BEFORE vs AFTER COMPARISON")
        print(f"{'-'*60}")

        orig = result['original']
        mod = result['modified']

        print(f"\n{'Dimension':<12} {'Original':>10} {'Modified':>10} {'Change':>10}")
        print(f"{'-'*50}")

        for dimension in orig['taste_scores']:
            orig_val = orig['taste_scores'][dimension]
            mod_val = mod['taste_scores'][dimension]
            change = mod_val - orig_val

            change_str = f"{change:+.3f}"
            print(f"{dimension.capitalize():<12} {orig_val:>10.3f} {mod_val:>10.3f} {change_str:>10}")

        print(f"{'-'*50}")
        print(f"{'Balance':<12} {orig['overall_balance']:>10.3f} {mod['overall_balance']:>10.3f} "
              f"{mod['overall_balance'] - orig['overall_balance']:+.3f}")

        # Impact summary
        print(f"\n{'-'*60}")
        print("IMPACT SUMMARY")
        print(f"{'-'*60}")
        print(f"  {result['impact_analysis']['summary']}")

        if result['impact_analysis']['balance_improved']:
            print(f"\n  [+] BALANCE IMPROVED!")
        else:
            print(f"\n  ! Balance decreased slightly. Try different modifications.")

    def _print_rating(self, score: float):
        """Print a rating based on score."""
        if score >= 0.95:
            print("(Excellent)")
        elif score >= 0.90:
            print("(Very Good)")
        elif score >= 0.80:
            print("(Good)")
        elif score >= 0.70:
            print("(Fair)")
        else:
            print("(Needs Improvement)")

    def list_cocktails(self):
        """List available cocktails."""
        print(f"\n{'='*60}")
        print("AVAILABLE COCKTAILS")
        print(f"{'='*60}\n")

        cocktails = sorted([c['name'] for c in self.analyzer.cocktails])
        for i, name in enumerate(cocktails[:50], 1):  # Show first 50
            print(f"{i:3d}. {name}")

        if len(cocktails) > 50:
            print(f"\n... and {len(cocktails) - 50} more")

        print(f"\nTotal: {len(cocktails)} cocktails")


def main():
    """Main CLI function."""
    print("="*60)
    print("                   COCKTAILIQ v0.1")
    print("        Molecular Cocktail Analysis & Optimization")
    print("="*60 + "\n")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cocktailiq_cli.py analyze <cocktail_name>")
        print("  python cocktailiq_cli.py recommend <cocktail_name> [target]")
        print("  python cocktailiq_cli.py list")
        print("\nExamples:")
        print("  python cocktailiq_cli.py analyze Margarita")
        print("  python cocktailiq_cli.py recommend Martini sweeter")
        print("  python cocktailiq_cli.py list")
        sys.exit(1)

    cli = CocktailIQCLI()
    command = sys.argv[1].lower()

    if command == 'analyze':
        if len(sys.argv) < 3:
            print("Error: Please specify a cocktail name")
            sys.exit(1)
        cocktail_name = ' '.join(sys.argv[2:])
        cli.analyze_cocktail(cocktail_name)

    elif command == 'recommend':
        if len(sys.argv) < 3:
            print("Error: Please specify a cocktail name")
            sys.exit(1)
        cocktail_name = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        cli.get_recommendations(cocktail_name, target)

    elif command == 'list':
        cli.list_cocktails()

    elif command == 'demo':
        # Demo mode - show full capabilities
        print("\nDEMO MODE - Showcasing CocktailIQ capabilities\n")

        # 1. Analyze a cocktail
        cli.analyze_cocktail("Mojito")

        # 2. Get recommendations
        cli.get_recommendations("Mojito")

        # 3. Show modification
        print("\n\nDEMO: Modifying Mojito to be sweeter")
        modifications = [
            {'action': 'add', 'ingredient': 'simple syrup', 'amount': 15.0}
        ]
        cli.modify_and_compare("Mojito", modifications)

    else:
        print(f"Unknown command: {command}")
        print("Available commands: analyze, recommend, list, demo")
        sys.exit(1)


if __name__ == "__main__":
    main()
