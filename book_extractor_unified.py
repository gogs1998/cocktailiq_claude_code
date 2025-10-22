"""
Unified Ebook Recipe Extraction Tool
Supports PDF, EPUB, and manual paste methods.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional


class UnifiedBookExtractor:
    """Extract cocktail recipes from various ebook formats."""

    def __init__(self):
        """Initialize extractor."""
        self.book_file = Path("data/book_cocktails.json")
        self.book_file.parent.mkdir(parents=True, exist_ok=True)

    def extract_recipes(self, method: str, **kwargs) -> List[Dict]:
        """
        Extract recipes using specified method.

        Args:
            method: 'pdf', 'epub', or 'paste'
            **kwargs: Method-specific arguments

        Returns:
            List of extracted recipes
        """
        if method == 'pdf':
            return self._extract_from_pdf(kwargs['file_path'], kwargs['book_title'])
        elif method == 'epub':
            return self._extract_from_epub(kwargs['file_path'], kwargs['book_title'])
        elif method == 'paste':
            return self._extract_from_paste(kwargs['text'], kwargs['book_title'])
        else:
            raise ValueError(f"Unknown method: {method}")

    def _extract_from_pdf(self, pdf_path: str, book_title: str) -> List[Dict]:
        """Extract recipes from PDF."""
        print(f"\nExtracting from PDF: {pdf_path}")

        try:
            import PyPDF2

            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ""

                print(f"Processing {len(reader.pages)} pages...")
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    full_text += f"\n{text}"

            recipes = self._parse_recipes_from_text(full_text, book_title)
            print(f"\nExtracted {len(recipes)} recipes from {book_title}")
            return recipes

        except ImportError:
            print("\n[!] PyPDF2 not installed. Install with: pip install PyPDF2")
            print("\nFallback: Use manual paste method instead.")
            return self._manual_paste_fallback(book_title)

        except Exception as e:
            print(f"[!] Error extracting PDF: {e}")
            return []

    def _extract_from_epub(self, epub_path: str, book_title: str) -> List[Dict]:
        """Extract recipes from EPUB."""
        print(f"\nExtracting from EPUB: {epub_path}")

        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup

            book = epub.read_epub(epub_path)
            full_text = ""

            print("Processing EPUB chapters...")
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text = soup.get_text()
                    full_text += "\n\n" + text

            recipes = self._parse_recipes_from_text(full_text, book_title)
            print(f"\nExtracted {len(recipes)} recipes from {book_title}")
            return recipes

        except ImportError:
            print("\n[!] ebooklib not installed. Install with: pip install ebooklib beautifulsoup4")
            print("\nFallback: Use manual paste method instead.")
            return self._manual_paste_fallback(book_title)

        except Exception as e:
            print(f"[!] Error extracting EPUB: {e}")
            return []

    def _extract_from_paste(self, text: str, book_title: str) -> List[Dict]:
        """Extract recipes from pasted text."""
        recipes = self._parse_recipes_from_text(text, book_title)
        print(f"\nParsed {len(recipes)} recipes from pasted text")
        return recipes

    def _manual_paste_fallback(self, book_title: str) -> List[Dict]:
        """Manual paste fallback when libraries unavailable."""
        print("\n" + "="*60)
        print("MANUAL PASTE MODE")
        print("="*60)
        print("\nCopy recipes from your ebook and paste below.")
        print("Format:")
        print("  Recipe Name")
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
        return self._parse_recipes_from_text(text, book_title)

    def _parse_recipes_from_text(self, text: str, book_title: str) -> List[Dict]:
        """
        Parse cocktail recipes from text.

        Supports formats like:
        - MARGARITA
          2 oz tequila
          1 oz lime juice
          0.75 oz triple sec
          Shake, strain into coupe

        Args:
            text: Raw text from ebook
            book_title: Name of source book

        Returns:
            List of parsed recipes
        """
        recipes = []

        # Split by double newlines (recipe separator)
        blocks = re.split(r'\n\s*\n', text.strip())

        for block in blocks:
            recipe = self._parse_single_recipe(block, book_title)
            if recipe:
                recipes.append(recipe)

        return recipes

    def _parse_single_recipe(self, text: str, book_title: str) -> Optional[Dict]:
        """
        Parse a single recipe from text block.

        Args:
            text: Recipe text
            book_title: Source book

        Returns:
            Recipe dict or None
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        if not lines:
            return None

        # Check if looks like a recipe (has measurements)
        has_measurements = any(re.search(r'\d+(?:\.\d+)?(?:/\d+)?\s*(oz|ml|dash|part|barspoon)', line, re.IGNORECASE)
                              for line in lines)

        if not has_measurements:
            return None

        # First line is usually the name
        name = lines[0]
        # Clean up markdown formatting
        name = re.sub(r'[*#\-]+', '', name).strip()

        # Skip if name is too long (probably not a recipe title)
        if len(name) > 50:
            return None

        ingredients = []
        technique = 'unknown'
        glass = 'unknown'
        notes = []

        # Pattern for ingredients with measurements
        ingredient_pattern = r'[\-\*]?\s*(\d+(?:\.\d+)?|\d+/\d+)\s*(oz|ml|dash|dashes|barspoon|tsp|tbsp|part|parts|splash|drops?|cl)\s+(.+)'

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
                ingredient_name = re.sub(r',.*$', '', ingredient_name).strip()  # Remove notes after comma

                # Convert to ml
                amount_ml = self._convert_to_ml(amount, unit)

                ingredients.append({
                    'name': ingredient_name.lower(),
                    'amount': amount_ml,
                    'unit': 'ml',
                    'original': f"{amount_str} {unit}"
                })
            else:
                # Check for technique/glass/notes
                line_lower = line.lower()

                if any(word in line_lower for word in ['shake', 'stir', 'build', 'blend', 'strain', 'muddle']):
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

                elif any(glass_word in line_lower for glass_word in ['coupe', 'rocks', 'highball', 'collins', 'glass', 'martini']):
                    # Glass line
                    if 'coupe' in line_lower:
                        glass = 'coupe'
                    elif 'rocks' in line_lower or 'old fashioned' in line_lower:
                        glass = 'rocks'
                    elif 'highball' in line_lower:
                        glass = 'highball'
                    elif 'collins' in line_lower:
                        glass = 'collins'
                    elif 'martini' in line_lower or 'cocktail glass' in line_lower:
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

    def _convert_to_ml(self, amount: float, unit: str) -> float:
        """Convert measurement to ml."""
        conversions = {
            'oz': 30.0,
            'ml': 1.0,
            'cl': 10.0,
            'dash': 1.0,
            'dashes': 1.0,
            'barspoon': 5.0,
            'tsp': 5.0,
            'tbsp': 15.0,
            'part': 30.0,
            'parts': 30.0,
            'splash': 5.0,
            'drop': 0.05,
            'drops': 0.05,
        }
        return amount * conversions.get(unit.lower(), 30.0)

    def save_recipes(self, recipes: List[Dict]):
        """
        Save extracted recipes to file.

        Args:
            recipes: List of recipes to save
        """
        # Load existing recipes
        existing = []
        if self.book_file.exists():
            with open(self.book_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # Merge (avoid duplicates by name)
        existing_names = {r['name'].lower() for r in existing}
        new_recipes = [r for r in recipes if r['name'].lower() not in existing_names]

        all_recipes = existing + new_recipes

        # Save
        with open(self.book_file, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, indent=2)

        print(f"\n[+] Saved {len(new_recipes)} new recipes to {self.book_file}")
        print(f"[+] Total recipes: {len(all_recipes)}")

    def review_recipes(self, recipes: List[Dict]) -> List[Dict]:
        """
        Review extracted recipes interactively.

        Args:
            recipes: Extracted recipes

        Returns:
            Approved recipes
        """
        print("\n" + "="*60)
        print("REVIEW EXTRACTED RECIPES")
        print("="*60)

        approved = []

        for i, recipe in enumerate(recipes, 1):
            print(f"\n--- Recipe {i}/{len(recipes)} ---")
            print(f"Name: {recipe['name']}")
            print(f"Book: {recipe['source_book']}")
            print(f"Ingredients ({len(recipe['ingredients'])}):")
            for ing in recipe['ingredients']:
                print(f"  - {ing['amount']:.1f}ml {ing['name']} ({ing['original']})")
            print(f"Technique: {recipe['technique']}")
            print(f"Glass: {recipe['glass']}")
            if recipe['notes']:
                print(f"Notes: {recipe['notes'][:80]}...")

            action = input("\nAction: (k)eep, (s)kip, (q)uit? ").strip().lower()

            if action == 'k':
                approved.append(recipe)
                print("[+] Kept")
            elif action == 's':
                print("[-] Skipped")
            elif action == 'q':
                break

        print(f"\n{len(approved)} recipes approved")
        return approved


def main():
    """Interactive extraction interface."""
    print("="*60)
    print("EBOOK COCKTAIL RECIPE EXTRACTOR")
    print("="*60)

    extractor = UnifiedBookExtractor()

    print("\nExtraction methods:")
    print("  1. PDF file")
    print("  2. EPUB file")
    print("  3. Manual paste")

    method = input("\nSelect method (1-3): ").strip()

    if method == '1':
        file_path = input("Enter PDF file path: ").strip().strip('"')
        book_title = input("Enter book title: ").strip()

        if not Path(file_path).exists():
            print(f"\n[!] Error: File not found: {file_path}")
            return

        recipes = extractor.extract_recipes('pdf', file_path=file_path, book_title=book_title)

    elif method == '2':
        file_path = input("Enter EPUB file path: ").strip().strip('"')
        book_title = input("Enter book title: ").strip()

        if not Path(file_path).exists():
            print(f"\n[!] Error: File not found: {file_path}")
            return

        recipes = extractor.extract_recipes('epub', file_path=file_path, book_title=book_title)

    elif method == '3':
        book_title = input("Enter book title: ").strip()

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
        recipes = extractor.extract_recipes('paste', text=text, book_title=book_title)

    else:
        print("\n[!] Invalid option")
        return

    if not recipes:
        print("\n[!] No recipes found. Check format.")
        return

    print(f"\n{'='*60}")
    print(f"FOUND {len(recipes)} RECIPES")
    print(f"{'='*60}")

    for i, recipe in enumerate(recipes[:5], 1):  # Show first 5
        print(f"\n{i}. {recipe['name']}")
        print(f"   Ingredients: {len(recipe['ingredients'])}")
        for ing in recipe['ingredients'][:3]:  # Show first 3 ingredients
            print(f"     - {ing['amount']:.1f}ml {ing['name']}")

    if len(recipes) > 5:
        print(f"\n... and {len(recipes) - 5} more")

    # Review
    review = input(f"\nReview before saving? (y/n): ").strip().lower()

    if review == 'y':
        recipes = extractor.review_recipes(recipes)

    # Save
    if recipes:
        extractor.save_recipes(recipes)
        print("\n[+] Done!")
    else:
        print("\n[!] No recipes to save.")


if __name__ == "__main__":
    main()
