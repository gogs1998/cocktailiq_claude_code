"""
Flavor Database Loader
Parses FlavorDB JSON and creates molecular flavor profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
import pandas as pd


class FlavorLoader:
    """Load and parse molecular flavor data from FlavorDB."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize flavor loader.

        Args:
            data_dir: Directory containing FlavorDB JSON file
        """
        self.data_dir = Path(data_dir)
        self.flavor_db = None
        self.molecules_by_source = defaultdict(list)
        self.all_molecules = []
        self.molecule_index = {}  # Index by pubchem_id or common_name

    def load_flavor_db(self) -> pd.DataFrame:
        """
        Load FlavorDB from JSON file.

        Returns:
            DataFrame with molecular data
        """
        flavor_file = self.data_dir / "flavourDB2.json"

        if not flavor_file.exists():
            raise FileNotFoundError(f"FlavorDB file not found: {flavor_file}")

        print("Loading FlavorDB...")
        with open(flavor_file, 'r', encoding='utf-8') as f:
            flavor_data = json.load(f)

        print(f"Loaded {len(flavor_data)} flavor categories")

        # Parse all molecules and organize by natural source
        for category_data in flavor_data:
            category = category_data.get('category_readable', '')
            natural_source = category_data.get('natural_source_name', '')
            entity_alias = category_data.get('entity_alias', '')

            molecules = category_data.get('molecules', [])

            for molecule in molecules:
                # Add category info to molecule
                molecule['category'] = category
                molecule['natural_source'] = natural_source
                molecule['entity_alias'] = entity_alias

                self.all_molecules.append(molecule)

                # Index by source name
                if natural_source:
                    self.molecules_by_source[natural_source.lower()].append(molecule)
                if entity_alias:
                    self.molecules_by_source[entity_alias.lower()].append(molecule)

                # Index by ID
                pubchem_id = molecule.get('pubchem_id')
                if pubchem_id:
                    self.molecule_index[f"pubchem_{pubchem_id}"] = molecule

                common_name = molecule.get('common_name', '')
                if common_name:
                    self.molecule_index[common_name.lower()] = molecule

        print(f"Parsed {len(self.all_molecules)} total molecules")
        print(f"Found {len(self.molecules_by_source)} unique natural sources")

        return pd.DataFrame(self.all_molecules)

    def get_molecules_for_ingredient(self, ingredient_name: str) -> List[Dict]:
        """
        Find molecules associated with an ingredient.

        Args:
            ingredient_name: Ingredient name (e.g., "gin", "lemon", "sugar")

        Returns:
            List of molecule dictionaries
        """
        ingredient_lower = ingredient_name.lower()

        # Direct lookup
        molecules = self.molecules_by_source.get(ingredient_lower, [])

        # If no direct match, try fuzzy matching based on keywords
        if not molecules:
            molecules = self._fuzzy_match_ingredient(ingredient_lower)

        return molecules

    def _fuzzy_match_ingredient(self, ingredient: str) -> List[Dict]:
        """
        Attempt to match ingredient using keyword matching.

        Args:
            ingredient: Ingredient name

        Returns:
            List of matching molecules
        """
        molecules = []

        # Define common mappings
        keyword_mappings = {
            'lemon': ['citrus', 'lemon'],
            'lime': ['citrus', 'lime'],
            'orange': ['citrus', 'orange'],
            'gin': ['juniper'],
            'vodka': ['grain', 'potato'],
            'rum': ['sugar cane', 'molasses'],
            'whiskey': ['grain', 'malt'],
            'whisky': ['grain', 'malt'],
            'tequila': ['agave'],
            'brandy': ['grape'],
            'cognac': ['grape'],
            'vermouth': ['wine', 'herbs'],
            'coffee': ['coffee'],
            'tea': ['tea'],
            'mint': ['mint'],
            'sugar': ['sugar'],
            'honey': ['honey'],
            'chocolate': ['cocoa'],
            'cocoa': ['cocoa'],
            'vanilla': ['vanilla'],
            'cinnamon': ['cinnamon'],
            'ginger': ['ginger'],
            'apple': ['apple'],
            'pineapple': ['pineapple'],
            'coconut': ['coconut'],
            'cherry': ['cherry'],
            'cranberry': ['cranberry'],
            'grape': ['grape'],
            'peach': ['peach'],
            'strawberry': ['strawberry'],
            'raspberry': ['raspberry'],
            'blackberry': ['blackberry'],
            'cream': ['milk', 'dairy'],
            'milk': ['milk', 'dairy'],
            'butter': ['milk', 'dairy'],
        }

        # Check if ingredient contains any known keywords
        for keyword, sources in keyword_mappings.items():
            if keyword in ingredient:
                for source in sources:
                    molecules.extend(self.molecules_by_source.get(source, []))

        return molecules

    def extract_flavor_profiles(self, molecules: List[Dict]) -> Dict:
        """
        Extract aggregated flavor profile from list of molecules.

        Args:
            molecules: List of molecule dictionaries

        Returns:
            Aggregated flavor profile with counts and properties
        """
        if not molecules:
            return {
                'num_molecules': 0,
                'flavor_keywords': {},
                'functional_groups': {},
                'avg_molecular_weight': 0,
                'avg_xlogp': 0,
                'taste_properties': {
                    'sweet': 0,
                    'bitter': 0,
                    'sour': 0,
                    'savory': 0,
                },
            }

        flavor_keywords = defaultdict(int)
        functional_groups = defaultdict(int)
        molecular_weights = []
        xlogp_values = []
        sweet_count = 0
        bitter_count = 0

        for mol in molecules:
            # Extract flavor profiles
            flavor_profile = mol.get('flavor_profile', '')
            if flavor_profile:
                for flavor in flavor_profile.split('@'):
                    if flavor.strip():
                        flavor_keywords[flavor.strip()] += 1

            # Extract functional groups
            func_groups = mol.get('functional_groups', '')
            if func_groups:
                for group in func_groups.split('@'):
                    if group.strip():
                        functional_groups[group.strip()] += 1

            # Numerical properties
            if mol.get('molecular_weight'):
                molecular_weights.append(mol['molecular_weight'])

            if mol.get('xlogp'):
                try:
                    xlogp_values.append(float(mol['xlogp']))
                except (ValueError, TypeError):
                    pass

            # Taste properties
            if mol.get('super_sweet'):
                sweet_count += 1
            if mol.get('bitter', 0) == 1:
                bitter_count += 1

        profile = {
            'num_molecules': len(molecules),
            'flavor_keywords': dict(sorted(flavor_keywords.items(), key=lambda x: x[1], reverse=True)),
            'functional_groups': dict(sorted(functional_groups.items(), key=lambda x: x[1], reverse=True)),
            'avg_molecular_weight': sum(molecular_weights) / len(molecular_weights) if molecular_weights else 0,
            'avg_xlogp': sum(xlogp_values) / len(xlogp_values) if xlogp_values else 0,
            'taste_properties': {
                'sweet': sweet_count,
                'bitter': bitter_count,
                'sour': 0,  # Not directly in DB, infer from flavor keywords
                'savory': 0,  # Not directly in DB, infer from flavor keywords
            },
        }

        # Infer taste from flavor keywords
        sour_keywords = {'sour', 'acidic', 'tart', 'citrus'}
        savory_keywords = {'savory', 'umami', 'meaty', 'brothy'}

        for keyword in flavor_keywords:
            if any(sk in keyword.lower() for sk in sour_keywords):
                profile['taste_properties']['sour'] += flavor_keywords[keyword]
            if any(sk in keyword.lower() for sk in savory_keywords):
                profile['taste_properties']['savory'] += flavor_keywords[keyword]

        return profile

    def save_processed_data(self, df: pd.DataFrame, output_dir: str = "data/processed"):
        """
        Save processed flavor data.

        Args:
            df: Molecule DataFrame
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save molecules
        molecules_file = output_path / "molecules_all.json"
        # Select key fields to reduce file size
        df_subset = df[[
            'pubchem_id', 'common_name', 'smile', 'molecular_weight',
            'flavor_profile', 'functional_groups', 'xlogp',
            'natural_source', 'category', 'bitter'
        ]].copy()
        df_subset.to_json(molecules_file, orient='records', indent=2)
        print(f"Saved molecules to {molecules_file}")

        # Save natural source index
        source_index = {
            source: len(molecules)
            for source, molecules in self.molecules_by_source.items()
        }
        source_file = output_path / "natural_source_index.json"
        with open(source_file, 'w', encoding='utf-8') as f:
            json.dump(source_index, f, indent=2)
        print(f"Saved natural source index to {source_file}")

        # Statistics
        stats = self._compute_statistics(df)
        stats_file = output_path / "flavor_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved statistics to {stats_file}")

    def _compute_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Compute statistics about FlavorDB.

        Args:
            df: Molecule DataFrame

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_molecules': len(df),
            'unique_categories': df['category'].nunique(),
            'unique_natural_sources': df['natural_source'].nunique(),
            'molecules_with_smiles': int(df['smile'].notna().sum()),
            'molecules_with_flavor_profile': int(df['flavor_profile'].notna().sum()),
            'avg_molecular_weight': float(df['molecular_weight'].mean()),
            'bitter_molecules': int(df['bitter'].sum()),
            'top_categories': df['category'].value_counts().head(10).to_dict(),
        }

        return stats


def main():
    """Main function to test flavor loader."""
    print("=== FlavorDB Loader ===\n")

    # Initialize loader
    loader = FlavorLoader(data_dir="raw")

    # Load FlavorDB
    print("Loading FlavorDB...")
    molecules_df = loader.load_flavor_db()

    # Display sample
    print("\n=== Sample Molecules ===")
    print(molecules_df[['common_name', 'category', 'flavor_profile']].head(10))

    # Test ingredient lookup
    print("\n=== Testing Ingredient Lookup ===")
    test_ingredients = ['lemon', 'gin', 'mint', 'sugar', 'vodka']

    for ingredient in test_ingredients:
        molecules = loader.get_molecules_for_ingredient(ingredient)
        profile = loader.extract_flavor_profiles(molecules)
        print(f"\n{ingredient.upper()}:")
        print(f"  Molecules found: {profile['num_molecules']}")
        if profile['flavor_keywords']:
            print(f"  Top flavors: {list(profile['flavor_keywords'].keys())[:5]}")

    # Save processed data
    print("\n=== Saving Processed Data ===")
    loader.save_processed_data(molecules_df)

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
