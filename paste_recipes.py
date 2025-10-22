"""
Simple Copy-Paste Recipe Entry
Copy recipes from your ebook and paste here.
"""

import json
import re
from pathlib import Path
from typing import List, Dict


def parse_pasted_recipes(text: str, book_title: str) -> List[Dict]:
    """
    Parse recipes from pasted text.

    Format examples:

    MARGARITA
    2 oz tequila
    1 oz lime juice
    0.75 oz triple sec
    Shake, strain into coupe

    Or:

    **Old Fashioned**
    - 2 oz bourbon
    - 1 barspoon simple syrup
    - 2 dashes bitters
    Stir, serve in rocks glass

    Args:
        text: Pasted recipe text
        book_title: Name of book

    Returns:
        List of parsed recipes
    """
    recipes = []

    # Split by double newlines (recipe separator)
    blocks = re.split(r'\n\s*\n', text.strip())

    for block in blocks:
        recipe = parse_single_recipe(block, book_title)
        if recipe:
            recipes.append(recipe)

    return recipes


def parse_single_recipe(text: str, book_title: str) -> Dict:
    """
    Parse a single recipe from text block.

    Args:
        text: Recipe text
        book_title: Book title

    Returns:
        Recipe dict or None
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    if not lines:
        return None

    # First non-empty line is usually the name
    name = lines[0]
    # Clean up markdown formatting
    name = re.sub(r'[*#\-]+', '', name).strip()

    ingredients = []
    technique = 'unknown'
    glass = 'unknown'
    notes = []

    ingredient_pattern = r'[\-\*]?\s*(\d+(?:\.\d+)?|\d+/\d+)\s*(oz|ml|dash|dashes|barspoon|tsp|tbsp|part|splash|drops?)\s+(.+)'

    for line in lines[1:]:
        # Try to match ingredient
        match = re.search(ingredient_pattern, line, re.IGNORECASE)

        if match:
            amount_str = match.group(1)
            unit = match.group(2).lower()
            ingredient_name = match.group(3).strip()

            # Parse fractions
            if '/' in amount_str:
                parts = amount_str.split('/')
                amount = float(parts[0]) / float(parts[1])
            else:
                amount = float(amount_str)

            # Clean ingredient name
            ingredient_name = re.sub(r'\(.*?\)', '', ingredient_name).strip()
            ingredient_name = re.sub(r'[\*\-]+', '', ingredient_name).strip()

            # Convert to ml
            amount_ml = convert_to_ml(amount, unit)

            ingredients.append({
                'name': ingredient_name.lower(),
                'amount': amount_ml,
                'unit': 'ml',
                'original': f"{amount_str} {unit}"
            })
        else:
            # Check for technique/glass/notes
            line_lower = line.lower()

            if any(word in line_lower for word in ['shake', 'stir', 'build', 'blend', 'strain']):
                # Technique line
                if 'shake' in line_lower:
                    technique = 'shaken'
                elif 'stir' in line_lower:
                    technique = 'stirred'
                elif 'build' in line_lower:
                    technique = 'built'
                elif 'blend' in line_lower:
                    technique = 'blended'

                notes.append(line)
            elif any(glass_word in line_lower for glass_word in ['coupe', 'rocks', 'highball', 'collins', 'glass']):
                # Glass line
                if 'coupe' in line_lower:
                    glass = 'coupe'
                elif 'rocks' in line_lower or 'old fashioned' in line_lower:
                    glass = 'rocks'
                elif 'highball' in line_lower:
                    glass = 'highball'
                elif 'collins' in line_lower:
                    glass = 'collins'
                elif 'martini' in line_lower:
                    glass = 'martini'

                notes.append(line)
            else:
                # General note
                notes.append(line)

    if not ingredients:
        return None

    return {
        'name': name,
        'source_book': book_title,
        'ingredients': ingredients,
        'technique': technique,
        'glass': glass,
        'notes': ' | '.join(notes) if notes else '',
        'expert_validated': True,
    }


def convert_to_ml(amount: float, unit: str) -> float:
    """Convert to ml."""
    conversions = {
        'oz': 30.0,
        'ml': 1.0,
        'dash': 1.0,
        'dashes': 1.0,
        'barspoon': 5.0,
        'tsp': 5.0,
        'tbsp': 15.0,
        'part': 30.0,
        'splash': 5.0,
        'drop': 0.05,
        'drops': 0.05,
    }
    return amount * conversions.get(unit.lower(), 30.0)


def main():
    """Interactive paste interface."""
    print("="*60)
    print("PASTE RECIPES FROM EBOOK")
    print("="*60)

    book_title = input("\nBook title: ").strip()

    print("\nPaste recipes below (supports multiple recipes).")
    print("Format:")
    print("  Name")
    print("  2 oz ingredient")
    print("  1 oz ingredient")
    print("  Shake and strain")
    print("  [blank line between recipes]")
    print("\nPaste recipes, then type 'DONE' on a new line:\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'DONE':
                break
            lines.append(line)
        except EOFError:
            break

    text = '\n'.join(lines)

    recipes = parse_pasted_recipes(text, book_title)

    if not recipes:
        print("\nNo recipes found. Check format.")
        return

    print(f"\n{'='*60}")
    print(f"FOUND {len(recipes)} RECIPES")
    print(f"{'='*60}")

    for i, recipe in enumerate(recipes, 1):
        print(f"\n{i}. {recipe['name']}")
        print(f"   Ingredients: {len(recipe['ingredients'])}")
        for ing in recipe['ingredients']:
            print(f"     - {ing['amount']:.1f}ml {ing['name']}")
        if recipe['notes']:
            print(f"   Notes: {recipe['notes'][:50]}...")

    save = input(f"\nSave {len(recipes)} recipes? (y/n): ").strip().lower()

    if save == 'y':
        output_file = Path("data/book_cocktails.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing
        existing = []
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # Merge
        existing_names = {r['name'].lower() for r in existing}
        new_recipes = [r for r in recipes if r['name'].lower() not in existing_names]

        all_recipes = existing + new_recipes

        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, indent=2)

        print(f"\n✓ Saved {len(new_recipes)} new recipes")
        print(f"✓ Total recipes: {len(all_recipes)}")
    else:
        print("\nNot saved.")


if __name__ == "__main__":
    main()
