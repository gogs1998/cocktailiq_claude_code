# Difford's Guide Scraping Guide

## Overview

Difford's Guide (diffordsguide.com) is one of the world's premier online cocktail databases with 3,000+ expert-curated recipes. This scraper allows you to extract recipes directly from Difford's Guide to enhance CocktailIQ with professional cocktail knowledge.

---

## Why Difford's Guide?

### Advantages

1. **Expert-Curated** - All recipes professionally tested and rated
2. **Comprehensive** - 3,000+ recipes with detailed specifications
3. **Quality Ratings** - Each recipe has ratings and difficulty levels
4. **Consistent Format** - Standardized ingredient measurements
5. **Complete Information** - Technique, glass, garnish, history
6. **Always Updated** - New recipes added regularly

### What We Extract

- Recipe name
- Ingredients with precise measurements
- Preparation technique (shaken, stirred, built, blended)
- Glass type
- Rating (if available)
- Description/notes
- Source URL for reference

---

## Installation

### Install Required Libraries

```bash
pip install requests beautifulsoup4 lxml
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

---

## Usage

### Quick Start: Scrape Top Cocktails

```bash
python scrape_diffords.py
```

**Choose option 1:**
- Enter number of recipes (e.g., 50)
- Scraper will automatically fetch top cocktails
- Saved to `data/book_cocktails.json`

**Example:**
```
Options:
  1. Scrape top cocktails (recommended)
  2. Search and scrape specific cocktails
  3. Scrape specific URLs

Select option (1-3): 1

How many recipes to scrape? (default: 50): 50

[!] This will scrape 50 recipes from Difford's Guide
[!] Estimated time: ~1.7 minutes (2s delay per recipe)
Continue? (y/n): y

[+] Searching Difford's Guide for cocktails...
[+] Found 50 recipe URLs

[1/50]
[+] Scraping: https://www.diffordsguide.com/cocktails/recipe/1234/margarita
[+] Scraped: Margarita (4 ingredients)
[+] Waiting 2s before next request...

...

[+] Successfully scraped 50/50 recipes
[+] Saved 50 new recipes to data/book_cocktails.json
[+] Total recipes: 50
```

---

### Search Specific Cocktails

```bash
python scrape_diffords.py
```

**Choose option 2:**
- Enter search query (e.g., "whiskey sour")
- Specify max results (e.g., 20)
- Scraper finds matching recipes

**Example:**
```
Select option (1-3): 2

Search query: negroni variations
Max results (default: 20): 10

[+] Found 10 recipes
Scrape all? (y/n): y

[+] Scraping 10 recipes...
```

---

### Scrape Specific URLs

```bash
python scrape_diffords.py
```

**Choose option 3:**
- Paste recipe URLs (one per line)
- Press Enter on blank line to finish

**Example:**
```
Select option (1-3): 3

Enter recipe URLs (one per line, blank to finish):
https://www.diffordsguide.com/cocktails/recipe/1234/margarita
https://www.diffordsguide.com/cocktails/recipe/5678/manhattan
[blank line]

[+] Scraping 2 recipes...
```

---

## Rate Limiting

### Built-In Protection

The scraper automatically:
- Waits 2 seconds between requests (configurable)
- Uses respectful User-Agent header
- Handles errors gracefully

### Recommended Limits

- **Small batch**: 10-20 recipes (instant)
- **Medium batch**: 50-100 recipes (~3-6 minutes)
- **Large batch**: 200-500 recipes (~15-30 minutes)

**Do NOT:**
- Scrape more than 500 recipes in one session
- Reduce delay below 2 seconds
- Run multiple scrapers simultaneously

---

## Output Format

### Saved to: `data/book_cocktails.json`

```json
{
  "name": "Margarita",
  "source_book": "Difford's Guide",
  "source_url": "https://www.diffordsguide.com/cocktails/recipe/1234/margarita",
  "ingredients": [
    {
      "name": "tequila blanco",
      "amount": 60.0,
      "unit": "ml",
      "original": "2 oz Tequila Blanco"
    },
    {
      "name": "lime juice",
      "amount": 30.0,
      "unit": "ml",
      "original": "1 oz Lime juice"
    },
    {
      "name": "cointreau",
      "amount": 22.5,
      "unit": "ml",
      "original": "0.75 oz Cointreau"
    }
  ],
  "technique": "shaken",
  "glass": "coupe",
  "notes": "The classic Margarita, perfectly balanced citrus and tequila...",
  "rating": 4.8,
  "expert_validated": true
}
```

---

## Integration with V4 Optimizer

### Automatic Integration

Once scraped, recipes automatically integrate with V4:

```bash
# 1. Scrape Difford's Guide
python scrape_diffords.py
# Saves to data/book_cocktails.json

# 2. Analyze recipes (builds frequency database)
python analyze_book_recipes.py
# Generates:
#   - ingredient_frequency.json
#   - ingredient_plausibility.json
#   - perfect_cocktails.json

# 3. Use V4 optimizer
python src/recommendation/optimizer_v4.py
# Uses Difford's data for plausibility scoring
```

### Expected Impact

**With 50 Difford's recipes:**
- Ingredient frequency data: ✅
- Common ingredients identified: ✅
- Rare ingredients penalized: ✅

**With 200+ Difford's recipes:**
- Comprehensive frequency database: ✅
- Style-specific patterns: ✅
- Regional variations: ✅
- Professional-grade recommendations: ✅

---

## Legal & Ethical Considerations

### Fair Use

This scraper is designed for:
- **Research purposes** (academic/scientific)
- **Personal use** (analyzing your own cocktail preferences)
- **Educational use** (learning about cocktail composition)

### Respectful Scraping

We follow best practices:
- ✅ Rate limiting (2s delay between requests)
- ✅ Respectful User-Agent identification
- ✅ No aggressive crawling
- ✅ Attribution (source_url included in data)
- ✅ No commercial use

### Attribution

All scraped recipes include:
- `"source_book": "Difford's Guide"`
- `"source_url": "[original URL]"`

When using CocktailIQ results based on Difford's data, acknowledge:
> "Cocktail recipes sourced from Difford's Guide (diffordsguide.com)"

---

## Troubleshooting

### "Connection Error"

**Problem:** Cannot reach Difford's Guide

**Solutions:**
- Check internet connection
- Try again later (site may be down)
- Use VPN if site is blocked in your region

### "No recipes found"

**Problem:** Search returned no results

**Solutions:**
- Try broader search query
- Use option 1 (top cocktails) instead
- Check if Difford's Guide is accessible

### "Parsing Error"

**Problem:** Recipe format not recognized

**Cause:** Difford's Guide may have updated their HTML structure

**Solutions:**
- Report the error (include URL)
- Try different recipes
- May need to update scraper selectors

### "Rate Limited / Blocked"

**Problem:** Too many requests too fast

**Solutions:**
- Wait 10-15 minutes before retrying
- Increase delay: Edit `scrape_diffords.py`, change `delay=2.0` to `delay=3.0`
- Scrape smaller batches

---

## Advanced Usage

### Programmatic Use

```python
from scrape_diffords import DiffordsGuideScraper

scraper = DiffordsGuideScraper()

# Scrape top 100 cocktails
recipes = scraper.scrape_top_cocktails(limit=100)

# Save to file
scraper.save_recipes(recipes)

# Or process directly
for recipe in recipes:
    print(f"{recipe['name']}: {len(recipe['ingredients'])} ingredients")
```

### Custom Delay

```python
# Slower scraping for safety
recipes = scraper.scrape_multiple(urls, delay=5.0)
```

### Search Specific Style

```python
# Search for specific cocktail types
urls = scraper.search_cocktails(query="tiki", limit=30)
recipes = scraper.scrape_multiple(urls)
```

---

## Comparison: Difford's vs Ebooks

### Difford's Guide Advantages

- ✅ **Fast** - Scrape 50 recipes in 2 minutes
- ✅ **Consistent** - Standardized format
- ✅ **Ratings** - Each recipe has quality score
- ✅ **Updated** - Always current
- ✅ **Complete** - All details included

### Ebook Advantages

- ✅ **Contextual** - Author commentary and history
- ✅ **Variations** - Multiple versions of same cocktail
- ✅ **Techniques** - Detailed preparation instructions
- ✅ **Permanent** - You own the books

### Recommendation

**Use both:**
1. Scrape Difford's Guide for breadth (500+ recipes)
2. Extract from ebooks for depth (author insights)
3. V4 learns from combined knowledge

---

## Example Workflow

### Building Expert Database

```bash
# Step 1: Scrape Difford's Guide (fast, comprehensive)
$ python scrape_diffords.py
> Option 1: Scrape top cocktails
> Limit: 200
[+] Saved 200 recipes

# Step 2: Extract from ebooks (detailed, contextual)
$ python book_extractor_unified.py
> Option 1: PDF file
> Book: Death & Co
[+] Saved 108 recipes
[+] Total recipes: 308

# Step 3: Analyze combined data
$ python analyze_book_recipes.py

INGREDIENT FREQUENCY ANALYSIS
Total unique ingredients: 187

Top 30:
  lemon juice: 156 recipes (50.6%)
  simple syrup: 134 recipes (43.5%)
  lime juice: 98 recipes (31.8%)
  ...
  tomato juice: 3 recipes (0.9%)  ← RARE!

EXPERT-CURATED PERFECT COCKTAILS
Found 67 perfectly balanced cocktails (>=0.98)

[+] Saved frequency database
[+] Saved plausibility scores
[+] Saved perfect cocktails

# Step 4: Use V4 with expert knowledge
$ python src/recommendation/optimizer_v4.py

V4 vs V3 COMPARISON
...
Recommendations changed: 8/10

Gimlet:
  V3: tomato juice (plausibility: 0.05)
  V4: simple syrup (plausibility: 0.92)  ← BETTER!
```

---

## Results

### Expected Database Size

**After scraping 200 Difford's recipes:**
- Total recipes: 200+ (Difford's) + existing ebooks
- Unique ingredients: 150-200
- Perfect cocktails (>=0.98): 40-60
- Comprehensive frequency data: ✅

### Expected V4 Improvements

| Metric | Before | After Difford's | Change |
|--------|--------|-----------------|--------|
| Recipes in database | 0-50 | 200+ | +4-200x |
| Ingredient coverage | Limited | Comprehensive | ✅ |
| Frequency accuracy | Low | High | ✅ |
| Plausibility scores | Sparse | Complete | ✅ |
| Recommendation diversity | 20% | 100% | +5x |

---

## Status & Next Steps

### Status
- ✅ Scraper implemented
- ✅ Rate limiting built-in
- ✅ Integration with V4
- ✅ Documentation complete

### Next Steps

1. **You:** Run the scraper
   ```bash
   python scrape_diffords.py
   ```

2. **Scrape:** 50-200 recipes (recommended)

3. **Analyze:** Build frequency database
   ```bash
   python analyze_book_recipes.py
   ```

4. **Test:** V4 with Difford's knowledge
   ```bash
   python src/recommendation/optimizer_v4.py
   ```

5. **Validate:** Check recommendation improvements

---

## Summary

Difford's Guide scraper provides **fast, expert-curated cocktail data** to enhance CocktailIQ's recommendation quality.

**Key benefits:**
- 🚀 Fast (200 recipes in ~7 minutes)
- 🎯 Professional quality
- 📊 Ratings and classifications
- 🔄 Easy to update
- 🤝 Integrates automatically with V4

Combined with ebook extraction, you'll have a comprehensive expert cocktail database powering world-class recommendations!
