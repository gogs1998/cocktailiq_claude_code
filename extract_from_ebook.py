"""
Ebook Recipe Extraction Tool
Extract cocktail recipes from PDF, EPUB, MOBI, etc.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import subprocess


class EbookExtractor:
    """Extract cocktail recipes from ebooks."""

    def __init__(self):
        """Initialize extractor."""
        self.recipes = []
        self.current_book = None

    def extract_from_pdf(self, pdf_path: str, book_title: str) -> List[Dict]:
        """
        Extract recipes from PDF ebook.

        Args:
            pdf_path: Path to PDF file
            book_title: Title of book

        Returns:
            List of extracted recipes
        """
        self.current_book = book_title
        print(f"Extracting from PDF: {book_title}")
        print(f"File: {pdf_path}")

        try:
            # Method 1: Try PyPDF2
            import PyPDF2

            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ""

                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}"

            # Parse recipes from text
            recipes = self._parse_recipes_from_text(full_text)

            print(f"\nExtracted {len(recipes)} recipes from {book_title}")
            return recipes

        except ImportError:
            print("\nPyPDF2 not installed. Install with: pip install PyPDF2")
            print("Or use alternative method...")
            return self._extract_pdf_alternative(pdf_path, book_title)

        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return []

    def extract_from_epub(self, epub_path: str, book_title: str) -> List[Dict]:
        """
        Extract recipes from EPUB ebook.

        Args:
            epub_path: Path to EPUB file
            book_title: Title of book

        Returns:
            List of extracted recipes
        """
        self.current_book = book_title
        print(f"Extracting from EPUB: {book_title}")

        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(epub_path)
            full_text = ""

            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    full_text += "\n\n" + text

            recipes = self._parse_recipes_from_text(full_text)

            print(f"\nExtracted {len(recipes)} recipes from {book_title}")
            return recipes

        except ImportError:
            print("\nebooklib not installed. Install with: pip install ebooklib beautifulsoup4")
            return []

        except Exception as e:
            print(f"Error extracting EPUB: {e}")
            return []

    def _extract_pdf_alternative(self, pdf_path: str, book_title: str) -> List[Dict]:
        """
        Alternative PDF extraction using pdftotext.

        Args:
            pdf_path: Path to PDF
            book_title: Book title

        Returns:
            Extracted recipes
        """
        print("\nTrying alternative method (copying text manually)...")
        print("\nPlease:")
        print(f"1. Open {pdf_path} in a PDF reader")
        print("2. Copy recipe text (Ctrl+A, Ctrl+C)")
        print("3. Paste below and press Enter twice when done:")

        lines = []
        print("\n[Paste text, then press Enter twice to finish]\n")

        while True:
            try:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            except EOFError:
                break

        full_text = "\n".join(lines)
        recipes = self._parse_recipes_from_text(full_text)

        return recipes

    def _parse_recipes_from_text(self, text: str) -> List[Dict]:
        """
        Parse cocktail recipes from extracted text.

        Args:
            text: Full text from ebook

        Returns:
            List of recipe dictionaries
        """
        recipes = []

        # Common recipe patterns
        # Pattern 1: Recipe name as header
        recipe_pattern = r'(?:^|\n)([A-Z][A-Za-z\s&\'-]+)\s*\n'

        # Pattern 2: Ingredients section
        ingredient_pattern = r'(\d+(?:\.\d+)?)\s*(oz|ml|dash|splash|part|barspoon|tsp|tbsp)\s+([a-z\s\-]+)'

        # Split text into potential recipe blocks
        blocks = re.split(r'\n\n+', text)

        for block in blocks:
            # Look for recipe indicators
            if self._looks_like_recipe(block):
                recipe = self._extract_recipe_from_block(block)
                if recipe:
                    recipe['source_book'] = self.current_book
                    recipe['expert_validated'] = True
                    recipes.append(recipe)

        return recipes

    def _looks_like_recipe(self, text: str) -> bool:
        """
        Check if text block looks like a recipe.

        Args:
            text: Text block

        Returns:
            True if likely a recipe
        """
        # Check for common indicators
        indicators = [
            r'\d+\s*(oz|ml)',  # Measurements
            r'(shake|stir|strain|build)',  # Techniques
            r'(glass|coupe|rocks)',  # Glassware
            r'garnish',  # Garnish mentions
        ]

        matches = sum(1 for pattern in indicators if re.search(pattern, text, re.IGNORECASE))

        # Likely recipe if has 2+ indicators
        return matches >= 2

    def _extract_recipe_from_block(self, text: str) -> Optional[Dict]:
        """
        Extract recipe details from text block.

        Args:
            text: Recipe text

        Returns:
            Recipe dictionary or None
        """
        lines = text.strip().split('\n')

        if not lines:
            return None

        # First line often the name
        name = lines[0].strip()

        # Extract ingredients with measurements
        ingredients = []
        ingredient_pattern = r'(\d+(?:\.\d+)?)\s*(oz|ml|dash|dashes|splash|part|barspoon|tsp|tbsp|drops?)\s+(.+)'

        for line in lines[1:]:
            match = re.search(ingredient_pattern, line, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                unit = match.group(2).lower()
                ingredient_name = match.group(3).strip()

                # Clean up ingredient name
                ingredient_name = re.sub(r'\(.*?\)', '', ingredient_name).strip()

                # Convert to ml
                amount_ml = self._convert_to_ml(float(amount_str), unit)

                ingredients.append({
                    'name': ingredient_name.lower(),
                    'amount': amount_ml,
                    'unit': 'ml',
                    'original': f"{amount_str} {unit}"
                })

        if not ingredients:
            return None

        # Extract technique
        technique = 'unknown'
        text_lower = text.lower()
        if 'shake' in text_lower:
            technique = 'shaken'
        elif 'stir' in text_lower:
            technique = 'stirred'
        elif 'build' in text_lower:
            technique = 'built'
        elif 'blend' in text_lower:
            technique = 'blended'

        # Extract glass
        glass = 'unknown'
        glass_patterns = [
            (r'coupe', 'coupe'),
            (r'rocks', 'rocks'),
            (r'old.fashioned', 'rocks'),
            (r'highball', 'highball'),
            (r'collins', 'collins'),
            (r'martini', 'martini'),
            (r'nick.?nora', 'nick and nora'),
        ]

        for pattern, glass_name in glass_patterns:
            if re.search(pattern, text_lower):
                glass = glass_name
                break

        return {
            'name': name,
            'ingredients': ingredients,
            'technique': technique,
            'glass': glass,
            'full_text': text,
        }

    def _convert_to_ml(self, amount: float, unit: str) -> float:
        """
        Convert measurement to ml.

        Args:
            amount: Amount value
            unit: Unit string

        Returns:
            Amount in ml
        """
        conversions = {
            'oz': 30.0,
            'ml': 1.0,
            'dash': 1.0,
            'dashes': 1.0,
            'splash': 5.0,
            'part': 30.0,
            'barspoon': 5.0,
            'tsp': 5.0,
            'tbsp': 15.0,
            'drop': 0.05,
            'drops': 0.05,
        }

        return amount * conversions.get(unit.lower(), 30.0)

    def save_recipes(self, recipes: List[Dict], output_file: str = "data/book_cocktails.json"):
        """
        Save extracted recipes to file.

        Args:
            recipes: List of recipes
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing recipes
        existing = []
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # Merge (avoid duplicates by name)
        existing_names = {r['name'].lower() for r in existing}
        new_recipes = [r for r in recipes if r['name'].lower() not in existing_names]

        all_recipes = existing + new_recipes

        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, indent=2)

        print(f"\nSaved {len(new_recipes)} new recipes to {output_file}")
        print(f"Total recipes: {len(all_recipes)}")

    def interactive_review(self, recipes: List[Dict]) -> List[Dict]:
        """
        Review extracted recipes interactively.

        Args:
            recipes: Extracted recipes

        Returns:
            Reviewed and approved recipes
        """
        print("\n" + "="*60)
        print("REVIEW EXTRACTED RECIPES")
        print("="*60)

        approved = []

        for i, recipe in enumerate(recipes, 1):
            print(f"\n--- Recipe {i}/{len(recipes)} ---")
            print(f"Name: {recipe['name']}")
            print(f"Ingredients ({len(recipe['ingredients'])}):")
            for ing in recipe['ingredients']:
                print(f"  - {ing['amount']:.1f}ml {ing['name']}")
            print(f"Technique: {recipe['technique']}")
            print(f"Glass: {recipe['glass']}")

            action = input("\nAction: (k)eep, (e)dit, (s)kip, (q)uit? ").strip().lower()

            if action == 'k':
                approved.append(recipe)
                print("✓ Kept")
            elif action == 'e':
                edited = self._edit_recipe(recipe)
                approved.append(edited)
                print("✓ Edited and kept")
            elif action == 's':
                print("✗ Skipped")
            elif action == 'q':
                break

        print(f"\n{len(approved)} recipes approved")
        return approved

    def _edit_recipe(self, recipe: Dict) -> Dict:
        """Edit a recipe interactively."""
        print("\nEditing recipe...")

        new_name = input(f"Name [{recipe['name']}]: ").strip()
        if new_name:
            recipe['name'] = new_name

        # Could add more editing options here
        return recipe


def main():
    """Main extraction interface."""
    print("="*60)
    print("EBOOK COCKTAIL RECIPE EXTRACTOR")
    print("="*60)

    extractor = EbookExtractor()

    print("\nSupported formats:")
    print("  - PDF (.pdf)")
    print("  - EPUB (.epub)")
    print("  - Text paste (manual)")

    file_path = input("\nEnter ebook file path: ").strip()
    book_title = input("Enter book title: ").strip()

    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        print(f"\nError: File not found: {file_path}")
        return

    # Extract based on format
    recipes = []

    if file_path.endswith('.pdf'):
        recipes = extractor.extract_from_pdf(file_path, book_title)
    elif file_path.endswith('.epub'):
        recipes = extractor.extract_from_epub(file_path, book_title)
    else:
        print(f"\nUnsupported format. Use PDF or EPUB.")
        return

    if not recipes:
        print("\nNo recipes extracted.")
        return

    # Review recipes
    print(f"\nExtracted {len(recipes)} potential recipes")
    review = input("Review before saving? (y/n): ").strip().lower()

    if review == 'y':
        recipes = extractor.interactive_review(recipes)

    # Save
    if recipes:
        extractor.save_recipes(recipes)
        print("\n✓ Done!")
    else:
        print("\nNo recipes to save.")


if __name__ == "__main__":
    main()
