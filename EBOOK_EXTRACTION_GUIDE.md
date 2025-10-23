# Recipe Extraction Guide

## Quick Start

Multiple ways to add expert cocktail recipes to CocktailIQ:
1. **Difford's Guide scraping** (Recommended - Fast & Easy)
2. **Ebook extraction** (PDFs, EPUB files)
3. **Manual copy-paste** (Any source)

---

## Option 1: Scrape Difford's Guide (Recommended)

**Fastest way to build a comprehensive database!**

Difford's Guide has 3,000+ professional recipes with ratings.

```bash
python scrape_diffords.py
```

**Select option 1:**
- Scrape top cocktails (e.g., 200 recipes)
- Takes ~7 minutes with built-in rate limiting
- Automatically saves to `data/book_cocktails.json`

**See:** `DIFFORDS_SCRAPING_GUIDE.md` for complete instructions

---

## Option 2: Extract from Ebooks

### Step 1: Extract Recipes from Your Ebooks

### Method A: Automated Extraction (PDF/EPUB)

```bash
python book_extractor_unified.py
```

**Choose option 1 (PDF) or 2 (EPUB):**
- Enter file path to your ebook
- Enter book title
- Tool will automatically extract recipes

**Supported formats:**
- PDF: Uses PyPDF2 (install: `pip install PyPDF2`)
- EPUB: Uses ebooklib (install: `pip install ebooklib beautifulsoup4`)

### Method B: Manual Copy-Paste

```bash
python book_extractor_unified.py
```

**Choose option 3 (Manual paste):**
1. Open your ebook in any reader
2. Copy recipe text (Ctrl+A, Ctrl+C)
3. Paste into the tool
4. Type `DONE` when finished

**Format examples:**

```
MARGARITA
2 oz tequila
1 oz lime juice
0.75 oz triple sec
Shake and strain into coupe

OLD FASHIONED
2 oz bourbon
1 barspoon simple syrup
2 dashes bitters
Stir, serve in rocks glass
```

---

## Step 2: Analyze All Recipes

After extracting recipes (from Difford's, ebooks, or manual paste), analyze them to build ingredient frequency database:

```bash
python analyze_book_recipes.py
```

**This will:**
1. Build ingredient frequency database
2. Identify perfectly balanced cocktails (>=0.98)
3. Compare book recipes vs database recipes
4. Compute plausibility scores for ingredients
5. Generate analysis report

**Output files created:**
- `data/processed/ingredient_frequency.json` - How often each ingredient appears
- `data/processed/perfect_cocktails.json` - Expert-curated perfect cocktails
- `data/processed/ingredient_plausibility.json` - Plausibility scores (0-1)

---

## Step 3: Use Book Knowledge in V4 Optimizer

Once you have book recipe data, the V4 optimizer will use it to:

### Fix Tomato Juice Bias
**Problem:** V3 recommends tomato juice in 9/10 cases (adds missing "savory")

**Solution:** Use plausibility scores
- Tomato juice: Appears in <1% of book recipes → Low plausibility (0.05)
- Lemon juice: Appears in 40% of book recipes → High plausibility (0.95)
- V4 ranks: `improvement * plausibility`

### Learn from Perfect Cocktails
**Problem:** Current balance targets are database-derived

**Solution:** Calibrate from expert books
- Analyze 5-star rated cocktails from books
- Compute ideal balance ranges
- Use as targets for recommendations

### Style-Aware Recommendations
**Problem:** Generic recommendations don't respect cocktail style

**Solution:** Learn patterns from books
- Tiki cocktails: More complex, tropical flavors
- Classic cocktails: Spirit-forward, simple
- Modern classics: Balanced, inventive

---

## Expected Improvements

### With 50 Book Recipes:
- ✅ Fix tomato juice bias
- ✅ Better balance targets
- ✅ Common ingredients prioritized
- **Expected:** More practical recommendations

### With 200+ Book Recipes:
- ✅ All above +
- ✅ Style-aware recommendations
- ✅ Recipe variation learning
- ✅ Technique suggestions
- **Expected:** Professional-grade suggestions

---

## Example Workflow

### Scenario: You have "Death & Co" as PDF

```bash
# Step 1: Extract recipes
$ python book_extractor_unified.py
> Select method (1-3): 1
> Enter PDF file path: C:\Books\Death_and_Co.pdf
> Enter book title: Death & Co

Processing 320 pages...
Extracted 108 recipes from Death & Co

FOUND 108 RECIPES
1. Penicillin
   Ingredients: 4
     - 60.0ml blended scotch
     - 22.5ml lemon juice
     - 22.5ml honey-ginger syrup

Review before saving? (y/n): n

[+] Saved 108 new recipes to data/book_cocktails.json
[+] Total recipes: 108

# Step 2: Analyze
$ python analyze_book_recipes.py

INGREDIENT FREQUENCY ANALYSIS
Total unique ingredients: 87

Top 30 most common ingredients:
Ingredient                          Count   Frequency
------------------------------------------------------------
lemon juice                            52        48.1%
simple syrup                           41        38.0%
lime juice                             35        32.4%
bitters                                28        25.9%
bourbon                                24        22.2%
...
tomato juice                            1         0.9%  ← LOW FREQUENCY!

EXPERT-CURATED PERFECT COCKTAILS
Found 23 perfectly balanced cocktails (>=0.98)

Cocktail                       Book                      Balance
----------------------------------------------------------------------
Manhattan                      Death & Co                    0.993
Penicillin                     Death & Co                    0.991
Old Fashioned                  Death & Co                    0.989
...

Ideal targets from expert cocktails:
  Average balance: 0.985
  Average complexity: 0.912

PLAUSIBILITY SCORES
High plausibility (common in books):
  lemon juice                    0.952 (appears in 52 recipes)
  simple syrup                   0.921 (appears in 41 recipes)
  lime juice                     0.893 (appears in 35 recipes)

Low plausibility (rare in books):
  tomato juice                   0.052 (appears in 1 recipe)   ← PENALIZE!
  celery                         0.063 (appears in 1 recipe)
  oyster sauce                   0.052 (appears in 1 recipe)

[+] Saved to data/processed/ingredient_frequency.json
[+] Saved to data/processed/perfect_cocktails.json
[+] Saved to data/processed/ingredient_plausibility.json

Key insights for V4 optimizer:
  [+] Use ingredient_frequency.json to weight recommendations
  [+] Use perfect_cocktails.json to calibrate balance targets
  [+] Use ingredient_plausibility.json to penalize rare ingredients

Expected improvements:
  [+] Fix tomato juice bias (low plausibility score)
  [+] Prioritize common cocktail ingredients
  [+] Better balance targets from expert cocktails

# Step 3: Build V4 (next task)
$ python src/recommendation/optimizer_v4.py
```

---

## Troubleshooting

### "PyPDF2 not installed"
```bash
pip install PyPDF2
```

### "ebooklib not installed"
```bash
pip install ebooklib beautifulsoup4
```

### "No recipes found"
- Check recipe format (must have measurements like "2 oz")
- Use manual paste method for complex formats
- Review extracted recipes interactively (select 'y' when asked)

### "File not found"
- Use absolute path: `C:\Books\mybook.pdf`
- Remove quotes if copy-pasted: `"C:\Books\file.pdf"` → `C:\Books\file.pdf`

---

## Adding More Books

You can add recipes from multiple books:

```bash
# Add first book
$ python book_extractor_unified.py
> Book: Death & Co
[+] Saved 108 recipes

# Add second book (merges automatically)
$ python book_extractor_unified.py
> Book: PDT Cocktail Book
[+] Saved 87 new recipes
[+] Total recipes: 195  ← Cumulative

# Add third book
$ python book_extractor_unified.py
> Book: Liquid Intelligence
[+] Saved 62 new recipes
[+] Total recipes: 257
```

Duplicates are automatically skipped (by recipe name).

---

## Data Files

### Input
- Your ebook files (PDF, EPUB, MOBI, etc.)

### Output
- `data/book_cocktails.json` - All extracted recipes
- `data/processed/ingredient_frequency.json` - Ingredient counts
- `data/processed/perfect_cocktails.json` - Perfect cocktails (>=0.98)
- `data/processed/ingredient_plausibility.json` - Plausibility scores

### Used By
- V4 optimizer (next step)
- Recommendation engine
- Balance calibration

---

## Next Steps

1. Extract recipes from your ebooks (use this guide)
2. Run analysis: `python analyze_book_recipes.py`
3. Build V4 optimizer with book knowledge (next task)
4. Test V4 improvements
5. Update paper with results

---

## Status

- ✅ Ebook extraction tools ready
- ✅ Analysis tools ready
- ⏳ Waiting for you to extract recipes from your ebooks
- ⏳ V4 optimizer (will be built after book data is available)

**Your next action:** Run `python book_extractor_unified.py` to start extracting recipes!
