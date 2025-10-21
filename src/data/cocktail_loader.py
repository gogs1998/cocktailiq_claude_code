"""
Cocktail Data Loader
Parses TheCocktailDB JSON files and normalizes cocktail recipes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


class CocktailLoader:
    """Load and parse cocktail data from TheCocktailDB."""

    def __init__(self, data_dir: str = "raw"):
        """
        Initialize cocktail loader.

        Args:
            data_dir: Directory containing cocktail JSON files
        """
        self.data_dir = Path(data_dir)
        self.cocktails = []
        self.ingredients_set = set()

    def load_all_cocktails(self) -> pd.DataFrame:
        """
        Load all cocktails from the expanded JSON file.

        Returns:
            DataFrame with normalized cocktail data
        """
        cocktail_file = self.data_dir / "all_cocktails_expanded.json"

        if not cocktail_file.exists():
            raise FileNotFoundError(f"Cocktail file not found: {cocktail_file}")

        with open(cocktail_file, 'r', encoding='utf-8') as f:
            cocktails_raw = json.load(f)

        print(f"Loaded {len(cocktails_raw)} raw cocktail recipes")

        # Parse each cocktail
        parsed_cocktails = []
        for cocktail in cocktails_raw:
            parsed = self._parse_cocktail(cocktail)
            if parsed:
                parsed_cocktails.append(parsed)

        print(f"Successfully parsed {len(parsed_cocktails)} cocktails")
        print(f"Found {len(self.ingredients_set)} unique ingredients")

        return pd.DataFrame(parsed_cocktails)

    def _parse_cocktail(self, cocktail: Dict) -> Optional[Dict]:
        """
        Parse a single cocktail from raw JSON format.

        Args:
            cocktail: Raw cocktail dictionary

        Returns:
            Normalized cocktail dictionary or None if parsing fails
        """
        try:
            # Extract basic info
            cocktail_id = cocktail.get('idDrink')
            name = cocktail.get('strDrink')
            category = cocktail.get('strCategory')
            glass = cocktail.get('strGlass')
            instructions = cocktail.get('strInstructions')
            alcoholic = cocktail.get('strAlcoholic')

            # Extract ingredients and measures
            ingredients = []
            measures = []

            for i in range(1, 16):  # Up to 15 ingredients
                ingredient = cocktail.get(f'strIngredient{i}')
                measure = cocktail.get(f'strMeasure{i}')

                if ingredient and ingredient.strip():
                    # Normalize ingredient name
                    ingredient_normalized = self._normalize_ingredient(ingredient)
                    self.ingredients_set.add(ingredient_normalized)

                    # Parse measure
                    measure_normalized = self._normalize_measure(measure)

                    ingredients.append(ingredient_normalized)
                    measures.append(measure_normalized)

            if not ingredients:
                return None

            return {
                'id': cocktail_id,
                'name': name,
                'category': category,
                'glass': glass,
                'alcoholic': alcoholic,
                'instructions': instructions,
                'ingredients': ingredients,
                'measures': measures,
                'num_ingredients': len(ingredients)
            }

        except Exception as e:
            print(f"Error parsing cocktail {cocktail.get('strDrink', 'unknown')}: {e}")
            return None

    def _normalize_ingredient(self, ingredient: str) -> str:
        """
        Normalize ingredient name.

        Args:
            ingredient: Raw ingredient name

        Returns:
            Normalized ingredient name (lowercase, stripped)
        """
        if not ingredient:
            return ""

        # Convert to lowercase and strip whitespace
        normalized = ingredient.lower().strip()

        # Remove trailing 's' for plural forms (optional - can be refined)
        # For now, keep as-is to maintain original naming

        return normalized

    def _normalize_measure(self, measure: str) -> Dict[str, float]:
        """
        Parse and normalize measurement to standard units (ml).

        Args:
            measure: Raw measurement string (e.g., "1 oz", "2 shots", "1/2 cup")

        Returns:
            Dictionary with 'value' in ml and 'original' string
        """
        if not measure or not measure.strip():
            return {'value': 0.0, 'original': '', 'unit': None}

        measure = measure.strip()

        # Conversion factors to ml
        conversions = {
            'oz': 30.0,
            'shot': 45.0,
            'jigger': 45.0,
            'cup': 240.0,
            'tbsp': 15.0,
            'tsp': 5.0,
            'ml': 1.0,
            'cl': 10.0,
            'dash': 1.0,
            'splash': 5.0,
            'part': 30.0,  # Assuming 1 part = 1 oz
        }

        # Extract numeric value and unit
        # Pattern: optional number, optional fraction, optional unit
        pattern = r'(\d+\.?\d*)\s*(\d+/\d+)?\s*([a-zA-Z]+)?'
        match = re.search(pattern, measure.lower())

        if match:
            whole = float(match.group(1)) if match.group(1) else 0.0
            fraction = self._parse_fraction(match.group(2)) if match.group(2) else 0.0
            unit = match.group(3) if match.group(3) else None

            total_value = whole + fraction

            # Convert to ml
            if unit and unit in conversions:
                value_ml = total_value * conversions[unit]
            else:
                # Assume oz if no unit specified
                value_ml = total_value * conversions['oz']

            return {
                'value': value_ml,
                'original': measure,
                'unit': unit
            }

        # If parsing fails, return 0
        return {'value': 0.0, 'original': measure, 'unit': None}

    def _parse_fraction(self, fraction_str: str) -> float:
        """
        Parse fraction string to float.

        Args:
            fraction_str: Fraction like "1/2" or "3/4"

        Returns:
            Float value
        """
        if not fraction_str:
            return 0.0

        try:
            parts = fraction_str.split('/')
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                return numerator / denominator
        except:
            pass

        return 0.0

    def get_ingredient_list(self) -> List[str]:
        """
        Get sorted list of all unique ingredients.

        Returns:
            Sorted list of ingredient names
        """
        return sorted(list(self.ingredients_set))

    def save_processed_data(self, df: pd.DataFrame, output_dir: str = "data/processed"):
        """
        Save processed cocktail data.

        Args:
            df: Processed cocktail DataFrame
            output_dir: Output directory path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save full cocktail data
        cocktail_file = output_path / "cocktails_processed.json"
        df.to_json(cocktail_file, orient='records', indent=2)
        print(f"Saved processed cocktails to {cocktail_file}")

        # Save ingredient list
        ingredients_file = output_path / "ingredients_list.json"
        with open(ingredients_file, 'w', encoding='utf-8') as f:
            json.dump(self.get_ingredient_list(), f, indent=2)
        print(f"Saved ingredient list to {ingredients_file}")

        # Save statistics
        stats = self._compute_statistics(df)
        stats_file = output_path / "cocktail_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"Saved statistics to {stats_file}")

    def _compute_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Compute statistics about the cocktail database.

        Args:
            df: Cocktail DataFrame

        Returns:
            Dictionary of statistics
        """
        stats = {
            'total_cocktails': int(len(df)),
            'total_unique_ingredients': len(self.ingredients_set),
            'avg_ingredients_per_cocktail': float(df['num_ingredients'].mean()),
            'min_ingredients': int(df['num_ingredients'].min()),
            'max_ingredients': int(df['num_ingredients'].max()),
            'categories': {k: int(v) for k, v in df['category'].value_counts().to_dict().items()} if 'category' in df.columns else {},
            'alcoholic_distribution': {k: int(v) for k, v in df['alcoholic'].value_counts().to_dict().items()} if 'alcoholic' in df.columns else {},
        }

        return stats


def main():
    """Main function to test cocktail loader."""
    print("=== CocktailIQ Data Loader ===\n")

    # Initialize loader
    loader = CocktailLoader(data_dir="raw")

    # Load cocktails
    print("Loading cocktails...")
    cocktails_df = loader.load_all_cocktails()

    # Display sample
    print("\n=== Sample Cocktails ===")
    print(cocktails_df[['name', 'category', 'num_ingredients']].head(10))

    # Save processed data
    print("\n=== Saving Processed Data ===")
    loader.save_processed_data(cocktails_df)

    print("\n=== Complete ===")


if __name__ == "__main__":
    main()
