"""
Molecular Profile Analyzer
Maps ingredients to molecules and builds comprehensive flavor profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import numpy as np

from ..data.flavor_loader import FlavorLoader


class MolecularProfiler:
    """Analyze ingredients at the molecular level."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize molecular profiler.

        Args:
            data_dir: Directory containing raw data files
        """
        self.flavor_loader = FlavorLoader(data_dir)
        self.flavor_loader.load_flavor_db()
        print(f"Loaded {len(self.flavor_loader.all_molecules)} molecules")

        # Cache for ingredient profiles
        self.profile_cache = {}

    def get_ingredient_profile(self, ingredient: str) -> Dict:
        """
        Get complete molecular profile for an ingredient.

        Args:
            ingredient: Ingredient name

        Returns:
            Dictionary containing molecular composition and flavor profile
        """
        if ingredient in self.profile_cache:
            return self.profile_cache[ingredient]

        # Get molecules for this ingredient
        molecules = self.flavor_loader.get_molecules_for_ingredient(ingredient)

        if not molecules:
            print(f"Warning: No molecules found for '{ingredient}'")
            return self._empty_profile()

        # Extract flavor profile
        flavor_profile = self.flavor_loader.extract_flavor_profiles(molecules)

        # Enhanced profile with detailed analysis
        profile = {
            'ingredient': ingredient,
            'num_molecules': len(molecules),
            'molecules': molecules[:20],  # Keep top 20 molecules
            'flavor_keywords': flavor_profile['flavor_keywords'],
            'functional_groups': flavor_profile['functional_groups'],
            'chemical_properties': {
                'avg_molecular_weight': flavor_profile['avg_molecular_weight'],
                'avg_logp': flavor_profile['avg_xlogp'],
            },
            'taste_scores': self._compute_taste_scores(molecules, flavor_profile),
            'aromatic_intensity': self._compute_aromatic_intensity(molecules),
            'volatility_estimate': self._estimate_volatility(molecules),
        }

        self.profile_cache[ingredient] = profile
        return profile

    def _empty_profile(self) -> Dict:
        """
        Return empty profile for ingredients with no molecular data.

        Returns:
            Empty profile dictionary
        """
        return {
            'ingredient': '',
            'num_molecules': 0,
            'molecules': [],
            'flavor_keywords': {},
            'functional_groups': {},
            'chemical_properties': {
                'avg_molecular_weight': 0,
                'avg_logp': 0,
            },
            'taste_scores': {
                'sweet': 0.0,
                'sour': 0.0,
                'bitter': 0.0,
                'savory': 0.0,
                'aromatic': 0.0,
            },
            'aromatic_intensity': 0.0,
            'volatility_estimate': 0.0,
        }

    def _compute_taste_scores(self, molecules: List[Dict], flavor_profile: Dict) -> Dict:
        """
        Compute quantitative taste dimension scores.

        Args:
            molecules: List of molecule dictionaries
            flavor_profile: Aggregated flavor profile

        Returns:
            Dictionary of taste scores (0-1 scale)
        """
        # Start with database annotations
        sweet = flavor_profile['taste_properties']['sweet']
        bitter = flavor_profile['taste_properties']['bitter']
        sour = flavor_profile['taste_properties']['sour']
        savory = flavor_profile['taste_properties']['savory']

        # Enhance with flavor keyword analysis
        flavor_keywords = flavor_profile['flavor_keywords']

        sweet_keywords = {'sweet', 'honey', 'caramel', 'sugar', 'syrup', 'vanilla', 'fruity'}
        bitter_keywords = {'bitter', 'astringent', 'tannic', 'harsh'}
        sour_keywords = {'sour', 'acidic', 'tart', 'citrus', 'vinegar', 'sharp'}
        savory_keywords = {'savory', 'umami', 'meaty', 'brothy', 'roasted'}
        aromatic_keywords = {'floral', 'aromatic', 'perfume', 'fragrant', 'herbal', 'spicy', 'woody', 'earthy'}

        for keyword, count in flavor_keywords.items():
            keyword_lower = keyword.lower()

            if any(sk in keyword_lower for sk in sweet_keywords):
                sweet += count * 2
            if any(bk in keyword_lower for bk in bitter_keywords):
                bitter += count * 2
            if any(sk in keyword_lower for sk in sour_keywords):
                sour += count * 2
            if any(sk in keyword_lower for sk in savory_keywords):
                savory += count * 2

        # Compute aromatic score from aromatic keywords and volatility
        aromatic = sum(count for keyword, count in flavor_keywords.items()
                      if any(ak in keyword.lower() for ak in aromatic_keywords))

        # Normalize scores (0-1 scale)
        # Using square root to dampen very high values
        max_score = max(sweet, bitter, sour, savory, aromatic, 1)

        scores = {
            'sweet': np.sqrt(sweet) / np.sqrt(max_score),
            'sour': np.sqrt(sour) / np.sqrt(max_score),
            'bitter': np.sqrt(bitter) / np.sqrt(max_score),
            'savory': np.sqrt(savory) / np.sqrt(max_score),
            'aromatic': np.sqrt(aromatic) / np.sqrt(max_score),
        }

        return scores

    def _compute_aromatic_intensity(self, molecules: List[Dict]) -> float:
        """
        Estimate aromatic intensity based on molecular properties.

        Args:
            molecules: List of molecule dictionaries

        Returns:
            Aromatic intensity score (0-1)
        """
        if not molecules:
            return 0.0

        aromatic_count = 0
        total_aromatic_weight = 0

        for mol in molecules:
            functional_groups = mol.get('functional_groups', '')

            # Check for aromatic compounds
            if 'aromatic' in functional_groups.lower():
                aromatic_count += 1

                # Weight by molecular properties that affect aroma
                # Lower molecular weight = more volatile = stronger aroma
                mw = mol.get('molecular_weight', 200)
                if mw < 300:  # Typical volatile range
                    total_aromatic_weight += 1.0 / (mw / 100.0)

        if aromatic_count == 0:
            return 0.0

        # Normalize
        intensity = (aromatic_count / len(molecules)) * np.tanh(total_aromatic_weight / aromatic_count)

        return float(min(intensity, 1.0))

    def _estimate_volatility(self, molecules: List[Dict]) -> float:
        """
        Estimate volatility based on molecular weight and structure.

        Args:
            molecules: List of molecule dictionaries

        Returns:
            Volatility estimate (0-1, higher = more volatile)
        """
        if not molecules:
            return 0.0

        volatilities = []

        for mol in molecules:
            mw = mol.get('molecular_weight', 0)

            if mw == 0:
                continue

            # Volatility inversely related to molecular weight
            # Typical volatile compounds: 50-250 Da
            # Heavy compounds: > 300 Da
            if mw < 100:
                vol = 1.0
            elif mw < 200:
                vol = 0.8
            elif mw < 300:
                vol = 0.5
            else:
                vol = 0.2

            # Adjust for functional groups
            func_groups = mol.get('functional_groups', '').lower()
            if 'ester' in func_groups or 'aldehyde' in func_groups:
                vol *= 1.2  # Esters and aldehydes tend to be more volatile
            if 'aromatic' in func_groups:
                vol *= 1.1

            volatilities.append(min(vol, 1.0))

        return float(np.mean(volatilities)) if volatilities else 0.0


class CocktailAnalyzer:
    """Analyze complete cocktails at the molecular level."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize cocktail analyzer.

        Args:
            data_dir: Directory containing data files
        """
        self.profiler = MolecularProfiler(data_dir)

        # Load processed cocktail data
        processed_cocktails = Path("data/processed/cocktails_processed.json")
        if processed_cocktails.exists():
            with open(processed_cocktails, 'r', encoding='utf-8') as f:
                self.cocktails = json.load(f)
            print(f"Loaded {len(self.cocktails)} cocktails")
        else:
            print("Warning: Processed cocktail data not found. Run cocktail_loader.py first.")
            self.cocktails = []

    def analyze_cocktail(self, cocktail_name: str) -> Dict:
        """
        Perform complete molecular analysis of a cocktail.

        Args:
            cocktail_name: Name of cocktail to analyze

        Returns:
            Comprehensive analysis dictionary
        """
        # Find cocktail
        cocktail = self._find_cocktail(cocktail_name)

        if not cocktail:
            return {'error': f"Cocktail '{cocktail_name}' not found"}

        # Analyze each ingredient
        ingredient_profiles = []
        for ingredient in cocktail['ingredients']:
            profile = self.profiler.get_ingredient_profile(ingredient)
            ingredient_profiles.append(profile)

        # Aggregate molecular profile
        aggregated = self._aggregate_profiles(ingredient_profiles, cocktail['measures'])

        analysis = {
            'cocktail_name': cocktail['name'],
            'category': cocktail.get('category', ''),
            'num_ingredients': len(cocktail['ingredients']),
            'ingredients': cocktail['ingredients'],
            'ingredient_profiles': ingredient_profiles,
            'aggregated_profile': aggregated,
            'balance_scores': aggregated['taste_scores'],
            'overall_balance': self._compute_overall_balance(aggregated['taste_scores']),
            'complexity_score': self._compute_complexity(ingredient_profiles),
        }

        return analysis

    def _find_cocktail(self, name: str) -> Dict:
        """
        Find cocktail by name (case-insensitive).

        Args:
            name: Cocktail name

        Returns:
            Cocktail dictionary or None
        """
        name_lower = name.lower()

        for cocktail in self.cocktails:
            if cocktail['name'].lower() == name_lower:
                return cocktail

        return None

    def _aggregate_profiles(self, profiles: List[Dict], measures: List[Dict]) -> Dict:
        """
        Aggregate ingredient profiles weighted by volume.

        Args:
            profiles: List of ingredient profiles
            measures: List of measurement dictionaries

        Returns:
            Aggregated profile
        """
        if not profiles:
            return {}

        # Extract volumes (default to equal weights if not available)
        volumes = [m.get('value', 30.0) for m in measures]
        total_volume = sum(volumes)

        if total_volume == 0:
            volumes = [1.0] * len(profiles)
            total_volume = len(profiles)

        # Weighted average of taste scores
        taste_dimensions = ['sweet', 'sour', 'bitter', 'savory', 'aromatic']
        aggregated_taste = {dim: 0.0 for dim in taste_dimensions}

        for profile, volume in zip(profiles, volumes):
            weight = volume / total_volume
            for dim in taste_dimensions:
                aggregated_taste[dim] += profile['taste_scores'][dim] * weight

        # Collect all flavor keywords (weighted by volume)
        all_flavor_keywords = defaultdict(float)
        all_functional_groups = defaultdict(float)

        for profile, volume in zip(profiles, volumes):
            weight = volume / total_volume

            for keyword, count in profile['flavor_keywords'].items():
                all_flavor_keywords[keyword] += count * weight

            for group, count in profile['functional_groups'].items():
                all_functional_groups[group] += count * weight

        # Aggregate chemical properties
        avg_mw = np.average([p['chemical_properties']['avg_molecular_weight']
                            for p in profiles if p['num_molecules'] > 0],
                           weights=[v for p, v in zip(profiles, volumes) if p['num_molecules'] > 0])

        return {
            'taste_scores': aggregated_taste,
            'flavor_keywords': dict(sorted(all_flavor_keywords.items(), key=lambda x: x[1], reverse=True)[:20]),
            'functional_groups': dict(sorted(all_functional_groups.items(), key=lambda x: x[1], reverse=True)[:10]),
            'avg_molecular_weight': float(avg_mw) if not np.isnan(avg_mw) else 0.0,
            'total_volume': total_volume,
        }

    def _compute_overall_balance(self, taste_scores: Dict) -> float:
        """
        Compute overall balance score (0-1, higher is more balanced).

        Args:
            taste_scores: Dictionary of taste dimension scores

        Returns:
            Balance score
        """
        # Good balance means no single dimension dominates too much
        # Calculate variance - lower variance = better balance
        scores = list(taste_scores.values())

        if not scores or all(s == 0 for s in scores):
            return 0.0

        mean_score = np.mean(scores)
        variance = np.var(scores)

        # Normalize variance to 0-1 scale
        # Lower variance = higher balance score
        balance = 1.0 / (1.0 + variance)

        return float(balance)

    def _compute_complexity(self, profiles: List[Dict]) -> float:
        """
        Compute complexity score based on molecular diversity.

        Args:
            profiles: List of ingredient profiles

        Returns:
            Complexity score (0-1)
        """
        if not profiles:
            return 0.0

        # Complexity factors:
        # 1. Number of unique flavor keywords
        # 2. Number of different functional groups
        # 3. Variety in molecular weights

        all_keywords = set()
        all_groups = set()

        for profile in profiles:
            all_keywords.update(profile['flavor_keywords'].keys())
            all_groups.update(profile['functional_groups'].keys())

        # Normalize (typical complex cocktail has 15-30 keywords, 5-10 groups)
        keyword_score = min(len(all_keywords) / 30.0, 1.0)
        group_score = min(len(all_groups) / 10.0, 1.0)

        # Average for overall complexity
        complexity = (keyword_score + group_score) / 2.0

        return float(complexity)


def main():
    """Test molecular profiler and cocktail analyzer."""
    print("=== Molecular Profile Analyzer ===\n")

    # Test ingredient profiling
    print("Testing Ingredient Profiling...")
    profiler = MolecularProfiler(data_dir="raw")

    test_ingredients = ['gin', 'lemon juice', 'sugar', 'vodka', 'orange juice']

    for ingredient in test_ingredients:
        print(f"\n{ingredient.upper()}:")
        profile = profiler.get_ingredient_profile(ingredient)
        print(f"  Molecules: {profile['num_molecules']}")
        print(f"  Taste scores: {profile['taste_scores']}")
        print(f"  Top flavors: {list(profile['flavor_keywords'].keys())[:5]}")

    # Test cocktail analysis
    print("\n\n=== Cocktail Analysis ===\n")
    analyzer = CocktailAnalyzer(data_dir="raw")

    test_cocktails = ['Margarita', 'Martini', 'Mojito', 'Old Fashioned']

    for cocktail_name in test_cocktails:
        print(f"\n{cocktail_name.upper()}:")
        analysis = analyzer.analyze_cocktail(cocktail_name)

        if 'error' in analysis:
            print(f"  {analysis['error']}")
            continue

        print(f"  Ingredients: {', '.join(analysis['ingredients'])}")
        print(f"  Balance scores: {analysis['balance_scores']}")
        print(f"  Overall balance: {analysis['overall_balance']:.3f}")
        print(f"  Complexity: {analysis['complexity_score']:.3f}")

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
