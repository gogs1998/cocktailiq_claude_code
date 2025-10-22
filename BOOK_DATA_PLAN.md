# Cocktail Books Integration Plan

## Why Books Are Better Than TheCocktailDB

### Problems with Current Data (TheCocktailDB)
1. **Quality varies** - Mix of professional and amateur recipes
2. **No expert validation** - No ratings or classifications
3. **Limited context** - Missing flavor notes, techniques
4. **Measurement inconsistencies** - "1 shot" vs "1.5 oz" confusion
5. **Tomato juice bias** - Algorithm finds gaps in savory dimension

### What Books Provide
1. **Expert-curated recipes** - Tested and refined by professionals
2. **Quality ratings** - Classic/modern, difficulty levels
3. **Flavor descriptions** - "bright", "balanced", "spirit-forward"
4. **Proper techniques** - Shaken vs stirred, garnishes
5. **Recipe variations** - How to adjust for taste preferences
6. **Historical context** - Original vs modern versions

---

## How We'll Use Your Books

### Step 1: Data Extraction

**Manual Entry Template:**
```json
{
  "source_book": "Death & Co",
  "page": 142,
  "name": "Penicillin",
  "author": "Sam Ross",
  "classification": "modern classic",
  "rating": "5/5",
  "flavor_profile": "smoky, sweet, sour, spicy",
  "technique": "shaken, double-strained",
  "glass": "rocks",
  "ingredients": [
    {"name": "blended scotch", "amount": 60, "unit": "ml"},
    {"name": "lemon juice", "amount": 22.5, "unit": "ml"},
    {"name": "honey-ginger syrup", "amount": 22.5, "unit": "ml"},
    {"name": "islay scotch", "amount": "float", "unit": "ml"}
  ],
  "garnish": "candied ginger",
  "notes": "Balance of smoke, sweet, and heat",
  "expert_validated": true
}
```

**Or Image/Photo Upload:**
```python
# If you have photos of pages
from PIL import Image
import pytesseract

def extract_from_book_photo(image_path):
    """Extract recipe from book photo using OCR."""
    # OCR + parsing logic
    pass
```

### Step 2: Quality Enhancement

**Add Expert Annotations:**
- ⭐⭐⭐⭐⭐ Classics (e.g., Negroni, Manhattan)
- 🔥 Modern innovations (e.g., Penicillin)
- 🎯 Perfect balance examples
- ⚠️ Advanced techniques required

**Flavor Descriptions:**
- Map book descriptions → molecular dimensions
- "bright and citrusy" → high sour, aromatic
- "spirit-forward" → high base spirit, low sweet
- "well-balanced" → TARGET for calibration

### Step 3: Calibration from Experts

**Learn What "Perfect" Means:**
```python
# Analyze 5-star rated cocktails from books
expert_cocktails = load_book_recipes(rating="5/5")

for cocktail in expert_cocktails:
    analysis = analyzer.analyze_cocktail(cocktail)

    # These are EXPERT-VALIDATED as perfect
    ideal_profiles.append(analysis['balance_scores'])

# Compute "ideal" ranges
ideal_balance_target = np.mean([c['overall_balance'] for c in expert_cocktails])
ideal_sweet_range = (0.4, 0.7)  # From expert data
ideal_sour_range = (0.3, 0.6)
# etc.
```

### Step 4: Fix Recommendation Diversity

**Problem**: Too much tomato juice (9/10 recommendations)

**Solution with Book Data**:
```python
# Add "plausibility" score from book frequency
ingredient_frequency = {
    'lemon juice': 847,  # Appears in 847 book recipes
    'simple syrup': 623,
    'lime juice': 512,
    'bitters': 401,
    'tomato juice': 12,  # Rarely used in cocktails!
}

def calculate_plausibility(ingredient, cocktail_style):
    """Weight by how common ingredient is in similar cocktails."""
    frequency = ingredient_frequency.get(ingredient, 0)
    return np.log(frequency + 1) / np.log(max(ingredient_frequency.values()))
```

### Step 5: Recipe Variations

**Learn Adjustment Patterns:**
```python
# Example: Book shows 3 variations of Daiquiri
variations = [
    {"name": "Classic Daiquiri", "rum": 60, "lime": 22, "sugar": 15},
    {"name": "Hemingway Daiquiri", "rum": 60, "lime": 22, "sugar": 0, "grapefruit": 15, "maraschino": 7.5},
    {"name": "Banana Daiquiri", "rum": 60, "lime": 22, "sugar": 15, "banana liqueur": 15}
]

# Learn: "Want it less sweet? Remove sugar, add grapefruit"
# Learn: "Want fruit flavor? Add matching liqueur"
```

---

## Implementation Steps

### Phase 1: Manual Entry (Immediate)

**Create data entry tool:**
```python
# src/data/book_entry.py
class BookRecipeEntry:
    """Interactive tool to enter recipes from books."""

    def add_recipe(self):
        name = input("Cocktail name: ")
        book = input("Source book: ")
        # ... guided entry

        recipe = self.validate_and_save(data)
        print(f"Added {name} to book_cocktails.json")
```

**Priority books to enter** (your suggestions?):
- Death & Co?
- Cocktail Codex?
- Liquid Intelligence?
- PDT Cocktail Book?
- Others you have?

### Phase 2: OCR/Photo Upload (If Helpful)

If you have many books, we can:
```bash
# Take photos of recipe pages
# Use OCR to extract text
# Parse into structured format
python extract_recipes_from_photos.py --book "Death & Co" --pages photos/*.jpg
```

### Phase 3: Analysis & Calibration

```python
# Compare database vs book cocktails
db_balance_avg = 0.955  # Current average
book_balance_avg = ???  # From your books

# Identify gaps
missing_styles = ["tiki", "molecular", "vintage"]
underrepresented = ["mezcal cocktails", "sherry cocktails"]
```

### Phase 4: Improved Recommendations

```python
class OptimizerV4(OptimizerV3):
    """
    Enhanced with book knowledge:
    - Plausibility scoring
    - Style-aware recommendations
    - Expert balance targets
    """

    def recommend_with_book_knowledge(self, cocktail):
        candidates = self.generate_candidates(cocktail)

        # NEW: Score by book frequency
        for cand in candidates:
            cand['plausibility'] = self.book_frequency[cand['ingredient']]
            cand['style_match'] = self.matches_style(cocktail, cand)

        # Rank by improvement * plausibility
        ranked = sorted(candidates,
                       key=lambda c: c['improvement'] * c['plausibility'],
                       reverse=True)

        return ranked[0]
```

---

## What You Can Do Now

### Option 1: Manual Entry (Start Small)
Pick **10 favorite cocktails** from your books:
- 5 classics you consider "perfectly balanced"
- 5 modern favorites

I'll create an entry form for you.

### Option 2: Bulk Photo Upload
If you have many recipes:
- Take photos of pages
- Send folder of images
- I'll build OCR extraction

### Option 3: Guided Entry Session
We go through books together:
- You read recipe
- I structure the data
- We capture expert notes

### Option 4: Book List First
Tell me which books you have:
- I'll prioritize which recipes to add
- Focus on highest-impact additions

---

## Expected Improvements

### With 50 Book Recipes:
- ✅ Fix tomato juice bias (use book frequency data)
- ✅ Better balance targets (from expert cocktails)
- ✅ Style-aware recommendations
- **Expected**: 100% → 100% (but with better recommendations)

### With 200+ Book Recipes:
- ✅ All above +
- ✅ Recipe variation learning
- ✅ Technique recommendations
- ✅ Garnish suggestions
- **Expected**: More practical, chef-approved suggestions

### With Full Book Integration:
- ✅ All above +
- ✅ Historical context
- ✅ Ingredient substitutions
- ✅ "Make it like [famous bartender]"
- **Expected**: Professional-grade cocktail assistant

---

## Next Step

**Tell me:**
1. Which books do you have?
2. How many recipes (~10, 50, 100+)?
3. Preferred entry method (manual, photos, guided)?
4. Any specific cocktails you want to add first?

Then I'll build the appropriate tool and we'll start enhancing the system with real expert knowledge! 📚🍸
