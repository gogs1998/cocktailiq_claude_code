"""
Interactive Book Recipe Entry Tool
Add cocktails from your books to enhance the system.
"""

import json
from pathlib import Path
from datetime import datetime


class BookRecipeEntry:
    """Tool to add recipes from cocktail books."""

    def __init__(self):
        """Initialize entry tool."""
        self.book_file = Path("data/book_cocktails.json")
        self.load_existing()

    def load_existing(self):
        """Load existing book recipes."""
        if self.book_file.exists():
            with open(self.book_file, 'r', encoding='utf-8') as f:
                self.recipes = json.load(f)
        else:
            self.recipes = []

        print(f"Loaded {len(self.recipes)} existing book recipes")

    def add_recipe_interactive(self):
        """Add a recipe through interactive prompts."""
        print("\n" + "="*60)
        print("ADD RECIPE FROM BOOK")
        print("="*60)

        recipe = {}

        # Basic info
        recipe['name'] = input("\nCocktail name: ").strip()
        recipe['source_book'] = input("Book title: ").strip()
        recipe['page'] = input("Page number (optional): ").strip()
        recipe['author'] = input("Recipe author/creator (optional): ").strip()

        # Classification
        print("\nClassification:")
        print("  1. Classic")
        print("  2. Modern Classic")
        print("  3. Contemporary")
        print("  4. Tiki")
        print("  5. Other")
        classification = input("Select (1-5): ").strip()
        classification_map = {
            '1': 'classic',
            '2': 'modern_classic',
            '3': 'contemporary',
            '4': 'tiki',
            '5': input("  Specify: ").strip()
        }
        recipe['classification'] = classification_map.get(classification, 'unknown')

        # Rating
        rating = input("\nRating (1-5 stars, or press Enter to skip): ").strip()
        recipe['rating'] = int(rating) if rating.isdigit() and 1 <= int(rating) <= 5 else None

        # Flavor profile
        print("\nFlavor profile (keywords like: sweet, sour, bitter, smoky, floral):")
        recipe['flavor_profile'] = input("  Keywords: ").strip()

        # Technique
        print("\nTechnique:")
        print("  1. Shaken")
        print("  2. Stirred")
        print("  3. Built (in glass)")
        print("  4. Blended")
        print("  5. Other")
        technique = input("Select (1-5): ").strip()
        technique_map = {
            '1': 'shaken',
            '2': 'stirred',
            '3': 'built',
            '4': 'blended',
            '5': input("  Specify: ").strip()
        }
        recipe['technique'] = technique_map.get(technique, 'unknown')

        # Glass
        recipe['glass'] = input("\nGlass type (e.g., coupe, rocks, highball): ").strip()

        # Ingredients
        print("\nIngredients (enter one at a time, blank to finish):")
        ingredients = []
        i = 1
        while True:
            print(f"\n  Ingredient {i}:")
            name = input("    Name (or press Enter if done): ").strip()
            if not name:
                break

            amount = input("    Amount (number): ").strip()
            unit = input("    Unit (ml, oz, dash, etc.): ").strip()

            ingredients.append({
                'name': name.lower(),
                'amount': float(amount) if amount.replace('.', '').isdigit() else amount,
                'unit': unit.lower()
            })
            i += 1

        recipe['ingredients'] = ingredients

        # Garnish
        recipe['garnish'] = input("\nGarnish (optional): ").strip()

        # Notes
        print("\nNotes (flavor description, technique tips, etc.):")
        recipe['notes'] = input("  Notes: ").strip()

        # Mark as expert validated
        recipe['expert_validated'] = True
        recipe['date_added'] = datetime.now().isoformat()

        # Review
        print("\n" + "="*60)
        print("RECIPE SUMMARY")
        print("="*60)
        print(json.dumps(recipe, indent=2))

        confirm = input("\nSave this recipe? (y/n): ").strip().lower()

        if confirm == 'y':
            self.recipes.append(recipe)
            self.save()
            print(f"\n✓ Added '{recipe['name']}' from {recipe['source_book']}")
            return True
        else:
            print("\n✗ Recipe not saved")
            return False

    def add_recipe_batch(self, recipe_dict):
        """Add recipe from dictionary (for programmatic entry)."""
        self.recipes.append(recipe_dict)
        self.save()

    def save(self):
        """Save recipes to file."""
        self.book_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.book_file, 'w', encoding='utf-8') as f:
            json.dump(self.recipes, f, indent=2)

        print(f"\nSaved to {self.book_file}")

    def list_recipes(self):
        """List all book recipes."""
        print("\n" + "="*60)
        print(f"BOOK RECIPES ({len(self.recipes)})")
        print("="*60)

        if not self.recipes:
            print("No recipes added yet")
            return

        for i, recipe in enumerate(self.recipes, 1):
            rating = "⭐" * recipe['rating'] if recipe.get('rating') else "No rating"
            print(f"\n{i}. {recipe['name']}")
            print(f"   Book: {recipe['source_book']}")
            print(f"   Rating: {rating}")
            print(f"   Classification: {recipe.get('classification', 'N/A')}")

    def show_statistics(self):
        """Show statistics about book recipes."""
        if not self.recipes:
            print("\nNo recipes added yet")
            return

        print("\n" + "="*60)
        print("BOOK RECIPE STATISTICS")
        print("="*60)

        print(f"\nTotal recipes: {len(self.recipes)}")

        # By book
        books = {}
        for r in self.recipes:
            book = r.get('source_book', 'Unknown')
            books[book] = books.get(book, 0) + 1

        print(f"\nRecipes by book:")
        for book, count in sorted(books.items(), key=lambda x: x[1], reverse=True):
            print(f"  {book}: {count}")

        # By rating
        ratings = {}
        for r in self.recipes:
            rating = r.get('rating')
            if rating:
                ratings[rating] = ratings.get(rating, 0) + 1

        print(f"\nBy rating:")
        for rating in sorted(ratings.keys(), reverse=True):
            stars = "⭐" * rating
            print(f"  {stars}: {ratings[rating]}")

        # By classification
        classifications = {}
        for r in self.recipes:
            cls = r.get('classification', 'Unknown')
            classifications[cls] = classifications.get(cls, 0) + 1

        print(f"\nBy classification:")
        for cls, count in sorted(classifications.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cls}: {count}")


def main():
    """Main interactive menu."""
    entry = BookRecipeEntry()

    while True:
        print("\n" + "="*60)
        print("BOOK RECIPE MANAGER")
        print("="*60)
        print("\n1. Add new recipe")
        print("2. List all recipes")
        print("3. Show statistics")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            entry.add_recipe_interactive()
        elif choice == '2':
            entry.list_recipes()
        elif choice == '3':
            entry.show_statistics()
        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option")


if __name__ == "__main__":
    main()
