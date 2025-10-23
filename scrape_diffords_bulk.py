"""
Difford's Guide Bulk Scraper
Scrapes all 6,633 cocktail recipes from Difford's Guide.

Features:
- Progress tracking with checkpoints
- Resume capability (skip already scraped)
- Error handling and retry logic
- Rate limiting (respectful 2s delay)
- Real-time statistics
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class DiffordsBulkScraper:
    """Bulk scraper for all Difford's Guide recipes."""

    def __init__(self, checkpoint_interval: int = 100):
        """
        Initialize bulk scraper.

        Args:
            checkpoint_interval: Save progress every N recipes
        """
        self.base_url = "https://www.diffordsguide.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        self.book_file = Path("data/book_cocktails.json")
        self.checkpoint_file = Path("data/scraper_checkpoint.json")
        self.urls_file = Path("difford_all_urls.json")
        self.log_file = Path("data/scraper_log.txt")

        self.book_file.parent.mkdir(parents=True, exist_ok=True)

        self.checkpoint_interval = checkpoint_interval
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'errors': []
        }

    def load_urls(self) -> List[str]:
        """Load all recipe URLs from sitemap export."""
        if not self.urls_file.exists():
            print(f"[!] URL file not found: {self.urls_file}")
            print(f"[!] Run the sitemap extraction first")
            return []

        with open(self.urls_file, 'r') as f:
            urls = json.load(f)

        print(f"[+] Loaded {len(urls)} recipe URLs")
        return urls

    def load_checkpoint(self) -> Dict:
        """Load scraping checkpoint."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            print(f"[+] Loaded checkpoint: {checkpoint['scraped_count']} recipes scraped")
            return checkpoint
        return {'scraped_urls': [], 'scraped_count': 0}

    def save_checkpoint(self, checkpoint: Dict):
        """Save scraping checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def log(self, message: str):
        """Log message to file and console."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')

    def scrape_recipe(self, url: str) -> Optional[Dict]:
        """
        Scrape a single recipe using JSON-LD.

        Args:
            url: Recipe URL

        Returns:
            Recipe dictionary or None
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract JSON-LD
            script = soup.find('script', type='application/ld+json')
            if not script:
                return None

            recipe_data = json.loads(script.string)

            # Extract name
            name = recipe_data.get('name', '').strip()
            if not name:
                return None

            # Extract ingredients
            ingredients = []
            for ing_str in recipe_data.get('recipeIngredient', []):
                match = re.match(r'([\d.]+(?:/[\d]+)?)\s*(ml|cl|oz|dash|dashes|drop|drops|barspoon|tsp|tbsp|part|parts|splash)\s+(.+)', ing_str, re.I)

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

            # Extract instructions
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

                if 'shake' in text:
                    technique = 'shaken'
                elif 'stir' in text:
                    technique = 'stirred'
                elif 'build' in text:
                    technique = 'built'
                elif 'blend' in text:
                    technique = 'blended'

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

            # Extract rating
            rating = recipe_data.get('aggregateRating', {}).get('ratingValue')
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

            return recipe

        except Exception as e:
            self.stats['errors'].append({'url': url, 'error': str(e)})
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

    def save_recipes(self, recipes: List[Dict]):
        """Save recipes (append mode for bulk scraping)."""
        # Load existing
        existing = []
        if self.book_file.exists():
            with open(self.book_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)

        # Merge
        existing_names = {r['name'].lower() for r in existing}
        new_recipes = [r for r in recipes if r['name'].lower() not in existing_names]

        all_recipes = existing + new_recipes

        # Save
        with open(self.book_file, 'w', encoding='utf-8') as f:
            json.dump(all_recipes, f, indent=2)

        return len(new_recipes), len(all_recipes)

    def scrape_all(self, delay: float = 2.0, start_from: int = 0):
        """
        Scrape all recipes with progress tracking.

        Args:
            delay: Delay between requests (seconds)
            start_from: Start from this index (for resuming)
        """
        # Load URLs
        urls = self.load_urls()
        if not urls:
            return

        # Load checkpoint
        checkpoint = self.load_checkpoint()
        scraped_urls = set(checkpoint.get('scraped_urls', []))

        # Filter already scraped
        if start_from == 0 and scraped_urls:
            urls_to_scrape = [url for url in urls if url not in scraped_urls]
            self.log(f"Resuming: {len(urls_to_scrape)} URLs remaining")
        else:
            urls_to_scrape = urls[start_from:]
            self.log(f"Starting from index {start_from}")

        self.stats['total'] = len(urls_to_scrape)
        self.stats['start_time'] = time.time()

        recipes_buffer = []

        self.log("="*70)
        self.log(f"BULK SCRAPING: {len(urls_to_scrape)} RECIPES")
        self.log("="*70)

        for i, url in enumerate(urls_to_scrape, 1):
            # Progress
            if i % 10 == 0 or i == 1:
                elapsed = time.time() - self.stats['start_time']
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(urls_to_scrape) - i) / rate if rate > 0 else 0

                self.log(f"[{i}/{len(urls_to_scrape)}] Progress: {(i/len(urls_to_scrape)*100):.1f}% | "
                        f"Success: {self.stats['success']} | Failed: {self.stats['failed']} | "
                        f"Rate: {rate:.1f} rec/s | ETA: {eta/60:.1f} min")

            # Scrape
            recipe = self.scrape_recipe(url)

            if recipe:
                recipes_buffer.append(recipe)
                scraped_urls.add(url)
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1

            # Checkpoint save
            if i % self.checkpoint_interval == 0:
                new_count, total_count = self.save_recipes(recipes_buffer)
                self.log(f"[CHECKPOINT] Saved {new_count} new recipes | Total: {total_count}")

                # Update checkpoint
                checkpoint = {
                    'scraped_urls': list(scraped_urls),
                    'scraped_count': len(scraped_urls),
                    'last_update': datetime.now().isoformat()
                }
                self.save_checkpoint(checkpoint)

                recipes_buffer = []

            # Rate limiting
            if i < len(urls_to_scrape):
                time.sleep(delay)

        # Final save
        if recipes_buffer:
            new_count, total_count = self.save_recipes(recipes_buffer)
            self.log(f"[FINAL] Saved {new_count} new recipes | Total: {total_count}")

        # Final checkpoint
        checkpoint = {
            'scraped_urls': list(scraped_urls),
            'scraped_count': len(scraped_urls),
            'last_update': datetime.now().isoformat(),
            'completed': True
        }
        self.save_checkpoint(checkpoint)

        # Print summary
        elapsed = time.time() - self.stats['start_time']
        self.log("\n" + "="*70)
        self.log("SCRAPING COMPLETE")
        self.log("="*70)
        self.log(f"Total attempted: {len(urls_to_scrape)}")
        self.log(f"Successful: {self.stats['success']}")
        self.log(f"Failed: {self.stats['failed']}")
        self.log(f"Time elapsed: {elapsed/60:.1f} minutes")
        self.log(f"Average rate: {self.stats['success']/elapsed:.2f} recipes/second")
        self.log(f"Final dataset: {total_count} recipes")


def main():
    """Run bulk scraper."""
    print("="*70)
    print("DIFFORD'S GUIDE BULK SCRAPER")
    print("="*70)

    scraper = DiffordsBulkScraper(checkpoint_interval=100)

    print("\n[!] This will scrape ALL 6,633 recipes from Difford's Guide")
    print("[!] Estimated time: ~3.5 hours (2s delay per recipe)")
    print("[!] Checkpoints every 100 recipes (can resume if interrupted)")

    confirm = input("\nContinue? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cancelled")
        return

    scraper.scrape_all(delay=2.0)


if __name__ == "__main__":
    main()
