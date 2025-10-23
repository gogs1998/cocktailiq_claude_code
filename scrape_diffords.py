"""
Difford's Guide Cocktail Scraper
Scrapes expert-curated cocktail recipes from Difford's Guide (diffordsguide.com)

Features:
- Scrapes recipe details (ingredients, amounts, technique, glass)
- Includes ratings and difficulty levels
- Respects rate limiting
- Saves to book_cocktails.json format
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin


class DiffordsGuideScraper:
    """Scrape cocktail recipes from Difford's Guide."""

    def __init__(self):
        """Initialize scraper."""
        self.base_url = "https://www.diffordsguide.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.book_file = Path("data/book_cocktails.json")
        self.book_file.parent.mkdir(parents=True, exist_ok=True)

    def search_cocktails(self, query: str = "", limit: int = 50) -> List[str]:
        """
        Search for cocktails and return recipe URLs.

        Args:
            query: Search query (empty = browse all)
            limit: Maximum number of recipes to return

        Returns:
            List of recipe URLs
        """
        print(f"\n[+] Searching Difford's Guide for cocktails...")

        # Difford's Guide browse/search URLs
        if query:
            search_url = f"{self.base_url}/cocktails/search?q={query}"
        else:
            search_url = f"{self.base_url}/cocktails/browse"

        recipe_urls = []

        try:
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find recipe links (adjust selectors based on site structure)
            recipe_links = soup.find_all('a', href=re.compile(r'/cocktails/recipe/'))

            for link in recipe_links[:limit]:
                url = urljoin(self.base_url, link['href'])
                if url not in recipe_urls:
                    recipe_urls.append(url)

            print(f"[+] Found {len(recipe_urls)} recipe URLs")

        except Exception as e:
            print(f"[!] Error searching: {e}")

        return recipe_urls

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """
        Scrape a single recipe from Difford's Guide.

        Args:
            url: Recipe URL

        Returns:
            Recipe dictionary or None
        """
        try:
            print(f"[+] Scraping: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract recipe name
            name_tag = soup.find('h1', class_='recipe-title') or soup.find('h1')
            if not name_tag:
                print(f"[!] Could not find recipe name")
                return None

            name = name_tag.get_text().strip()

            # Extract ingredients
            ingredients = []
            ingredient_list = soup.find_all('li', class_='ingredient') or soup.find_all('div', class_='ingredient')

            for ing in ingredient_list:
                # Try to extract amount and ingredient name
                text = ing.get_text().strip()

                # Pattern: "2 oz Vodka" or "45ml Gin" or "1 dash Bitters"
                match = re.match(r'([\d.]+(?:/[\d]+)?)\s*(oz|ml|cl|dash|dashes|barspoon|tsp|part|parts|drops?)\s+(.+)', text, re.IGNORECASE)

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
                        'original': text
                    })

            if not ingredients:
                print(f"[!] No ingredients found")
                return None

            # Extract technique
            technique = 'unknown'
            technique_tag = soup.find('div', class_='method') or soup.find('p', class_='method')
            if technique_tag:
                method_text = technique_tag.get_text().lower()
                if 'shake' in method_text:
                    technique = 'shaken'
                elif 'stir' in method_text:
                    technique = 'stirred'
                elif 'build' in method_text:
                    technique = 'built'
                elif 'blend' in method_text:
                    technique = 'blended'

            # Extract glass
            glass = 'unknown'
            glass_tag = soup.find('span', class_='glass-type') or soup.find('div', class_='glass')
            if glass_tag:
                glass_text = glass_tag.get_text().lower()
                if 'coupe' in glass_text:
                    glass = 'coupe'
                elif 'rocks' in glass_text or 'old fashioned' in glass_text:
                    glass = 'rocks'
                elif 'highball' in glass_text:
                    glass = 'highball'
                elif 'collins' in glass_text:
                    glass = 'collins'
                elif 'martini' in glass_text or 'cocktail' in glass_text:
                    glass = 'martini'

            # Extract rating
            rating = None
            rating_tag = soup.find('span', class_='rating') or soup.find('div', class_='rating')
            if rating_tag:
                rating_text = rating_tag.get_text()
                rating_match = re.search(r'([\d.]+)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))

            # Extract description/notes
            notes = ""
            desc_tag = soup.find('div', class_='description') or soup.find('p', class_='description')
            if desc_tag:
                notes = desc_tag.get_text().strip()[:200]  # First 200 chars

            recipe = {
                'name': name,
                'source_book': "Difford's Guide",
                'source_url': url,
                'ingredients': ingredients,
                'technique': technique,
                'glass': glass,
                'notes': notes,
                'rating': rating,
                'expert_validated': True,
            }

            print(f"[+] Scraped: {name} ({len(ingredients)} ingredients)")
            return recipe

        except Exception as e:
            print(f"[!] Error scraping {url}: {e}")
            return None

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
            print(f"\n[{i}/{len(urls)}]")

            recipe = self.scrape_recipe(url)

            if recipe:
                recipes.append(recipe)

            # Rate limiting
            if i < len(urls):
                print(f"[+] Waiting {delay}s before next request...")
                time.sleep(delay)

        print(f"\n[+] Successfully scraped {len(recipes)}/{len(urls)} recipes")
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
        Scrape top-rated cocktails.

        Args:
            limit: Number of cocktails to scrape

        Returns:
            List of recipes
        """
        print("="*70)
        print("SCRAPING DIFFORD'S GUIDE TOP COCKTAILS")
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
    print("DIFFORD'S GUIDE COCKTAIL SCRAPER")
    print("="*70)

    scraper = DiffordsGuideScraper()

    print("\nOptions:")
    print("  1. Scrape top cocktails (recommended)")
    print("  2. Search and scrape specific cocktails")
    print("  3. Scrape specific URLs")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == '1':
        limit = input("\nHow many recipes to scrape? (default: 50): ").strip()
        limit = int(limit) if limit.isdigit() else 50

        print(f"\n[!] This will scrape {limit} recipes from Difford's Guide")
        print("[!] Estimated time: ~{:.1f} minutes (2s delay per recipe)".format(limit * 2 / 60))
        confirm = input("Continue? (y/n): ").strip().lower()

        if confirm != 'y':
            print("Cancelled")
            return

        recipes = scraper.scrape_top_cocktails(limit=limit)

        if recipes:
            scraper.save_recipes(recipes)
            print("\n[+] Done!")

    elif choice == '2':
        query = input("\nSearch query: ").strip()
        limit = input("Max results (default: 20): ").strip()
        limit = int(limit) if limit.isdigit() else 20

        urls = scraper.search_cocktails(query=query, limit=limit)

        if not urls:
            print("[!] No recipes found")
            return

        print(f"\n[+] Found {len(urls)} recipes")
        confirm = input("Scrape all? (y/n): ").strip().lower()

        if confirm != 'y':
            print("Cancelled")
            return

        recipes = scraper.scrape_multiple(urls, delay=2.0)

        if recipes:
            scraper.save_recipes(recipes)
            print("\n[+] Done!")

    elif choice == '3':
        print("\nEnter recipe URLs (one per line, blank to finish):")
        urls = []
        while True:
            url = input().strip()
            if not url:
                break
            urls.append(url)

        if not urls:
            print("[!] No URLs provided")
            return

        recipes = scraper.scrape_multiple(urls, delay=2.0)

        if recipes:
            scraper.save_recipes(recipes)
            print("\n[+] Done!")

    else:
        print("[!] Invalid option")


if __name__ == "__main__":
    main()
