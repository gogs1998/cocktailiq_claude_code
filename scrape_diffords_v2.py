"""
Difford's Guide Cocktail Scraper V2
Uses structured JSON-LD data for reliable extraction.

Difford's Guide has 3,000+ expert-curated recipes with ratings.
This scraper extracts recipes using JSON-LD structured data.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional


class DiffordsGuideScraperV2:
    """Scrape cocktail recipes from Difford's Guide using JSON-LD."""

    def __init__(self):
        """Initialize scraper."""
        self.base_url = "https://www.diffordsguide.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.book_file = Path("data/book_cocktails.json")
        self.book_file.parent.mkdir(parents=True, exist_ok=True)

    def search_cocktails(self, limit: int = 50) -> List[str]:
        """
        Get cocktail recipe URLs from homepage.

        Args:
            limit: Maximum number of recipes

        Returns:
            List of recipe URLs
        """
        print(f"\n[+] Searching Difford's Guide...")

        recipe_urls = []

        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all recipe links
            links = soup.find_all('a', href=re.compile(r'/cocktails/recipe/\d+'))

            for link in links[:limit]:
                url = link['href']
                if not url.startswith('http'):
                    url = self.base_url + url

                if url not in recipe_urls:
                    recipe_urls.append(url)

            print(f"[+] Found {len(recipe_urls)} recipe URLs")

        except Exception as e:
            print(f"[!] Error searching: {e}")

        return recipe_urls

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """
        Scrape a single recipe using JSON-LD structured data.

        Args:
            url: Recipe URL

        Returns:
            Recipe dictionary or None
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract JSON-LD structured data
            script = soup.find('script', type='application/ld+json')
            if not script:
                print(f"[!] No JSON-LD data found")
                return None

            recipe_data = json.loads(script.string)

            # Extract name
            name = recipe_data.get('name', '').strip()
            if not name:
                return None

            # Extract ingredients
            ingredients = []
            for ing_str in recipe_data.get('recipeIngredient', []):
                # Parse: "50 ml Vodka" or "8 drop Vanilla bitters"
                match = re.match(r'([\d.]+(?:/[\d]+)?)\s*(ml|cl|oz|dash|dashes|drop|drops|barspoon|tsp|tbsp|part|parts)\s+(.+)', ing_str, re.I)

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

                    # Convert to ml
                    amount_ml = self._convert_to_ml(amount, unit)

                    ingredients.append({
                        'name': ingredient_name.lower(),
                        'amount': amount_ml,
                        'unit': 'ml',
                        'original': ing_str
                    })

            if not ingredients:
                return None

            # Extract instructions to determine technique
            instructions = recipe_data.get('recipeInstructions', [])
            technique = 'unknown'
            glass = 'unknown'
            notes_list = []

            for inst in instructions:
                if isinstance(inst, dict):
                    text = inst.get('text', '').lower()
                else:
                    text = str(inst).lower()

                notes_list.append(text)

                # Determine technique
                if 'shake' in text:
                    technique = 'shaken'
                elif 'stir' in text:
                    technique = 'stirred'
                elif 'build' in text:
                    technique = 'built'
                elif 'blend' in text:
                    technique = 'blended'

                # Determine glass
                if 'martini' in text or 'cocktail glass' in text:
                    glass = 'martini'
                elif 'coupe' in text:
                    glass = 'coupe'
                elif 'rocks' in text or 'old fashioned' in text:
                    glass = 'rocks'
                elif 'highball' in text:
                    glass = 'highball'
                elif 'collins' in text:
                    glass = 'collins'

            # Extract rating (if available)
            rating = recipe_data.get('aggregateRating', {}).get('ratingValue')

            # Extract description
            description = recipe_data.get('description', '')

            recipe = {
                'name': name,
                'source_book': "Difford's Guide",
                'source_url': url,
                'ingredients': ingredients,
                'technique': technique,
                'glass': glass,
                'notes': ' | '.join(notes_list[:3]) if notes_list else description,
                'rating': float(rating) if rating else None,
                'expert_validated': True,
            }

            print(f"[+] {name} ({len(ingredients)} ingredients)")
            return recipe

        except Exception as e:
            print(f"[!] Error: {e}")
            return None

    def _convert_to_ml(self, amount: float, unit: str) -> float:
        """Convert measurement to ml."""
        conversions = {
            'oz': 30.0,
            'ml': 1.0,
            'cl': 10.0,
            'dash': 1.0,
            'dashes': 1.0,
            'drop': 0.05,
            'drops': 0.05,
            'barspoon': 5.0,
            'tsp': 5.0,
            'tbsp': 15.0,
            'part': 30.0,
            'parts': 30.0,
            'splash': 5.0,
        }
        return amount * conversions.get(unit.lower(), 30.0)

    def scrape_multiple(self, urls: List[str], delay: float = 2.0) -> List[Dict]:
        """
        Scrape multiple recipes with rate limiting.

        Args:
            urls: List of recipe URLs
            delay: Delay between requests (seconds)

        Returns:
            List of scraped recipes
        """
        recipes = []

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]", end=" ")

            recipe = self.scrape_recipe(url)

            if recipe:
                recipes.append(recipe)

            # Rate limiting
            if i < len(urls):
                time.sleep(delay)

        print(f"\n\n[+] Successfully scraped {len(recipes)}/{len(urls)} recipes")
        return recipes

    def save_recipes(self, recipes: List[Dict]):
        """
        Save scraped recipes to file.

        Args:
            recipes: List of recipes
        """
        # Load existing
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

    def scrape_top_cocktails(self, limit: int = 50) -> List[Dict]:
        """
        Scrape top cocktails.

        Args:
            limit: Number of cocktails to scrape

        Returns:
            List of recipes
        """
        print("="*70)
        print("SCRAPING DIFFORD'S GUIDE")
        print("="*70)

        # Get recipe URLs
        urls = self.search_cocktails(limit=limit)

        if not urls:
            print("[!] No recipes found")
            return []

        # Scrape recipes
        recipes = self.scrape_multiple(urls, delay=2.0)

        return recipes


def main():
    """Interactive scraping interface."""
    print("="*70)
    print("DIFFORD'S GUIDE COCKTAIL SCRAPER V2")
    print("="*70)

    scraper = DiffordsGuideScraperV2()

    limit = input("\nHow many recipes to scrape? (default: 10): ").strip()
    limit = int(limit) if limit.isdigit() else 10

    print(f"\n[!] This will scrape {limit} recipes from Difford's Guide")
    print(f"[!] Estimated time: ~{(limit * 2) / 60:.1f} minutes (2s delay per recipe)")
    confirm = input("Continue? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled")
        return

    recipes = scraper.scrape_top_cocktails(limit=limit)

    if recipes:
        scraper.save_recipes(recipes)
        print("\n[+] Done!")
        print(f"\n[+] Next steps:")
        print(f"    1. Run: python analyze_book_recipes.py")
        print(f"    2. Run: python src/recommendation/optimizer_v4.py")


if __name__ == "__main__":
    main()
