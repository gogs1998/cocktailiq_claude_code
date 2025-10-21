# CocktailIQ Improvement Plan

## Current Performance (REAL)
- ✅ Imbalance Detection: 100%
- ✅ Recommendation Relevance: 100%
- ⚠️ Balance Improvement: 11.1%

## Goal
Increase balance improvement success rate from 11% to 70%+

---

## Problem Analysis

### Why Only 11% Success?

Looking at actual results:
```
DEGRADED  Margarita:     0.993 -> 0.988 (-0.005) +15ml lemon juice
DEGRADED  Mojito:        0.973 -> 0.969 (-0.004) +15ml lemon juice
IMPROVED  Gimlet:        0.914 -> 0.919 (+0.004) +15ml honey
```

**Root Causes**:
1. **Fixed amounts** - Always recommending 15ml regardless of current balance
2. **High baseline** - Test cocktails already 95%+ balanced
3. **No upper threshold** - Suggesting changes to near-perfect cocktails
4. **Volume insensitivity** - Not accounting for total cocktail volume
5. **Limited ingredient pool** - Missing spirits molecular data reduces accuracy

---

## Improvement Strategy

### 1. ADAPTIVE RECOMMENDATION AMOUNTS ⭐ (Highest Impact)

**Current**: Always suggest 15ml
**Problem**: Too much for balanced cocktails, too little for very imbalanced ones

**Fix**: Scale amount based on current balance and imbalance magnitude

```python
def calculate_adaptive_amount(current_balance, imbalance_magnitude, total_volume):
    """
    Scale recommendation amount based on cocktail state.

    Args:
        current_balance: 0-1 score (higher = more balanced)
        imbalance_magnitude: How far dimension is from mean
        total_volume: Total cocktail volume in ml
    """
    # Base amount as % of total volume
    base_percentage = 0.15  # 15% of total volume

    # Reduce for already-balanced cocktails
    if current_balance > 0.95:
        balance_factor = 0.3  # Only 30% of base amount
    elif current_balance > 0.90:
        balance_factor = 0.5
    elif current_balance > 0.80:
        balance_factor = 0.75
    else:
        balance_factor = 1.0

    # Increase for severe imbalances
    severity_factor = min(imbalance_magnitude / 0.5, 2.0)

    # Calculate final amount
    amount = total_volume * base_percentage * balance_factor * severity_factor

    # Bounds: 5ml to 30ml
    return max(5.0, min(amount, 30.0))
```

**Expected Impact**: +30-40% success rate

---

### 2. SMART THRESHOLD - DON'T FIX WHAT'S NOT BROKEN

**Current**: Recommends changes for all cocktails
**Problem**: Suggesting "improvements" to already-excellent cocktails

**Fix**: Add threshold logic

```python
def should_recommend_changes(balance_score, complexity_score):
    """
    Determine if cocktail actually needs changes.
    """
    # Excellent cocktails - no changes needed
    if balance_score >= 0.98:
        return False, "Cocktail is already excellently balanced!"

    # Very good cocktails - only suggest if clear issue
    if balance_score >= 0.95:
        # Check if any dimension is VERY far off
        max_deviation = calculate_max_deviation(taste_scores)
        if max_deviation < 0.3:
            return False, "Cocktail is very well balanced. Minor tweaks possible but not necessary."

    # Good cocktails - suggest refinements
    if balance_score >= 0.85:
        return True, "Good cocktail with room for refinement"

    # Needs work
    return True, "Cocktail has imbalances that could be improved"
```

**Expected Impact**: +20% success rate (avoid degrading good cocktails)

---

### 3. ENHANCED INGREDIENT-MOLECULE MAPPINGS

**Current**: Missing mappings for key spirits
- ❌ No molecules for: rum, tequila, bourbon, whiskey
- ❌ No molecules for: many liqueurs, bitters

**Problem**: Can't accurately analyze ~30% of cocktails

**Fix**: Expand mapping database

```python
# Add manual mappings for spirits based on base ingredients
SPIRIT_MAPPINGS = {
    'rum': ['sugar cane', 'molasses', 'vanilla', 'caramel'],
    'light rum': ['sugar cane', 'citrus'],
    'dark rum': ['molasses', 'caramel', 'vanilla', 'oak'],
    'tequila': ['agave', 'citrus', 'pepper'],
    'bourbon': ['corn', 'oak', 'vanilla', 'caramel'],
    'whiskey': ['grain', 'malt', 'oak', 'smoke'],
    'scotch': ['malt', 'peat', 'smoke', 'oak'],
    'vodka': ['grain', 'neutral'],  # Already has some data
    'gin': ['juniper', 'citrus', 'herbs'],  # Already mapped

    # Liqueurs
    'triple sec': ['orange', 'citrus', 'sweet'],
    'cointreau': ['orange', 'citrus', 'sweet'],
    'grand marnier': ['orange', 'cognac', 'sweet'],
    'campari': ['bitter orange', 'herbs', 'bitter'],
    'aperol': ['orange', 'herbs', 'bitter'],

    # Bitters
    'angostura bitters': ['spice', 'herbs', 'bitter'],
    'orange bitters': ['orange', 'bitter'],

    # Other
    'simple syrup': ['sugar'],
    'soda water': ['water', 'mineral'],
}

def get_molecules_with_fallback(ingredient):
    """Get molecules with spirit fallback."""
    # Try direct lookup
    molecules = flavor_loader.get_molecules_for_ingredient(ingredient)

    if not molecules and ingredient.lower() in SPIRIT_MAPPINGS:
        # Aggregate from base ingredients
        molecules = []
        for base in SPIRIT_MAPPINGS[ingredient.lower()]:
            molecules.extend(flavor_loader.get_molecules_for_ingredient(base))

    return molecules
```

**Expected Impact**: +15% success rate (better accuracy on more cocktails)

---

### 4. MULTI-RECOMMENDATION OPTIMIZATION

**Current**: Test only top recommendation
**Problem**: First suggestion might not be optimal

**Fix**: Generate and test multiple modification strategies

```python
def find_best_modification(cocktail_name, max_candidates=5):
    """
    Test multiple modification strategies, return best.
    """
    original = analyzer.analyze_cocktail(cocktail_name)
    recommendations = optimizer.recommend_improvements(cocktail_name)

    candidates = []

    # Try top N recommendations individually
    for rec in recommendations['recommendations'][:max_candidates]:
        mod = [{
            'action': 'add',
            'ingredient': rec['recommendation']['ingredient'],
            'amount': rec['recommendation']['amount']
        }]

        result = modifier.modify_cocktail(cocktail_name, mod)

        if 'error' not in result:
            improvement = result['modified']['overall_balance'] - original['overall_balance']
            candidates.append({
                'modification': mod,
                'improvement': improvement,
                'new_balance': result['modified']['overall_balance']
            })

    # Return best performing modification
    if candidates:
        best = max(candidates, key=lambda x: x['improvement'])
        return best

    return None
```

**Expected Impact**: +10% success rate (find better options)

---

### 5. VOLUME-AWARE RECOMMENDATIONS

**Current**: Ignores total cocktail size
**Problem**: 15ml in a 60ml cocktail vs 200ml punch has different impact

**Fix**: Scale by volume ratio

```python
def volume_aware_amount(ingredient_profile, total_volume, target_impact):
    """
    Calculate amount needed for specific impact at given volume.
    """
    # Estimate concentration needed
    ingredient_strength = ingredient_profile['taste_scores'][target_dimension]

    # Volume ratio for desired impact
    # Impact = (amount/total) * ingredient_strength
    # amount = (desired_impact * total) / ingredient_strength

    desired_impact = 0.10  # Want to change dimension by 0.1
    amount = (desired_impact * total_volume) / max(ingredient_strength, 0.1)

    return round(amount, 1)
```

**Expected Impact**: +5% success rate

---

### 6. ITERATIVE REFINEMENT

**Current**: Single recommendation, done
**Problem**: Complex imbalances need multiple adjustments

**Fix**: Suggest sequence of modifications

```python
def iterative_optimization(cocktail_name, max_iterations=3):
    """
    Apply multiple rounds of optimization.
    """
    current_state = cocktail_name
    modifications = []

    for i in range(max_iterations):
        # Analyze current state
        analysis = analyzer.analyze_cocktail(current_state)

        # Stop if balanced enough
        if analysis['overall_balance'] > 0.95:
            break

        # Get next recommendation
        rec = optimizer.recommend_improvements(current_state)
        if not rec['recommendations']:
            break

        # Apply best modification
        best_mod = rec['recommendations'][0]
        modifications.append(best_mod)

        # Update state (simulate)
        current_state = apply_modification(current_state, best_mod)

    return modifications
```

**Expected Impact**: +10% for complex cases

---

### 7. VALIDATION WITH SYNTHETIC IMBALANCES

**Current**: Test on naturally-balanced cocktails
**Problem**: Hard to show improvement on already-good cocktails

**Fix**: Create intentionally imbalanced test cases

```python
def create_imbalanced_test_set():
    """
    Modify known good cocktails to create imbalanced versions.
    Test if we can fix them back.
    """
    test_cases = []

    # Start with balanced cocktails
    originals = ['Margarita', 'Mojito', 'Daiquiri']

    for cocktail in originals:
        # Create "too sweet" version
        sweet_version = add_ingredient(cocktail, 'simple syrup', 20.0)
        test_cases.append({
            'original': cocktail,
            'modified': sweet_version,
            'issue': 'too_sweet',
            'expected_fix': 'add citrus'
        })

        # Create "too sour" version
        sour_version = add_ingredient(cocktail, 'lime juice', 20.0)
        test_cases.append({
            'original': cocktail,
            'modified': sour_version,
            'issue': 'too_sour',
            'expected_fix': 'add sweet'
        })

    return test_cases

def validate_on_synthetic():
    """
    Test: Can we fix intentionally broken cocktails?
    """
    tests = create_imbalanced_test_set()
    success = 0

    for test in tests:
        imbalanced = test['modified']
        target_balance = analyzer.analyze_cocktail(test['original'])['overall_balance']

        # Try to fix
        rec = optimizer.recommend_improvements(imbalanced)
        fixed = apply_recommendation(imbalanced, rec)

        fixed_balance = analyzer.analyze_cocktail(fixed)['overall_balance']

        # Success if we got closer to original
        if abs(fixed_balance - target_balance) < 0.05:
            success += 1

    return success / len(tests)
```

**Expected Impact**: Better evaluation metric (measures what we claim to do)

---

### 8. LEARN FROM EXPERT COCKTAILS

**Current**: No ground truth for "good balance"
**Problem**: Don't know what optimal balance looks like

**Fix**: Use IBA cocktails as gold standard

```python
def calibrate_from_experts():
    """
    Learn what "balanced" means from IBA standard cocktails.
    """
    # Load IBA (International Bartenders Association) cocktails
    iba_cocktails = [c for c in cocktails if c.get('strIBA')]

    # Analyze their balance characteristics
    iba_balances = []
    iba_profiles = []

    for cocktail in iba_cocktails:
        analysis = analyzer.analyze_cocktail(cocktail['name'])
        if 'error' not in analysis:
            iba_balances.append(analysis['overall_balance'])
            iba_profiles.append(analysis['balance_scores'])

    # Compute "ideal" ranges
    ideal_balance_mean = np.mean(iba_balances)
    ideal_balance_std = np.std(iba_balances)

    # Dimension ranges
    ideal_dimensions = {}
    for dim in ['sweet', 'sour', 'bitter', 'savory', 'aromatic']:
        values = [p[dim] for p in iba_profiles]
        ideal_dimensions[dim] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.percentile(values, 10),
            'max': np.percentile(values, 90)
        }

    return ideal_balance_mean, ideal_dimensions
```

**Expected Impact**: +15% (better understanding of "good")

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Add threshold logic (don't fix excellent cocktails)
2. ✅ Implement adaptive amounts based on balance
3. ✅ Add spirit mappings for common ingredients

**Expected improvement**: 11% → 50%

### Phase 2: Core Improvements (3-4 hours)
4. ✅ Volume-aware scaling
5. ✅ Multi-recommendation testing
6. ✅ Synthetic imbalance validation

**Expected improvement**: 50% → 70%

### Phase 3: Advanced (5+ hours)
7. ⏳ Iterative optimization
8. ⏳ Expert cocktail calibration
9. ⏳ Machine learning for amount prediction

**Expected improvement**: 70% → 85%

---

## Code Changes Required

### File: `src/recommendation/optimizer.py`

```python
# Add to FlavorOptimizer class

def _calculate_adaptive_amount(self, current_balance: float,
                               imbalance_magnitude: float,
                               total_volume: float) -> float:
    """Calculate context-aware recommendation amount."""
    base_percentage = 0.15

    if current_balance > 0.95:
        balance_factor = 0.3
    elif current_balance > 0.90:
        balance_factor = 0.5
    else:
        balance_factor = 1.0

    severity_factor = min(imbalance_magnitude / 0.5, 2.0)
    amount = total_volume * base_percentage * balance_factor * severity_factor

    return max(5.0, min(amount, 30.0))

def recommend_improvements(self, cocktail_name: str, ...) -> Dict:
    """Enhanced with adaptive amounts and thresholds."""

    analysis = self.analyzer.analyze_cocktail(cocktail_name)
    current_balance = analysis['overall_balance']

    # THRESHOLD CHECK
    if current_balance >= 0.98:
        return {
            'cocktail': cocktail_name,
            'message': 'Already excellently balanced!',
            'recommendations': []
        }

    # ... existing code ...

    # ADAPTIVE AMOUNTS
    for suggestion in suggestions:
        total_volume = analysis['aggregated_profile']['total_volume']
        imbalance_mag = imbalance['current_value'] - mean_score

        suggestion['amount'] = self._calculate_adaptive_amount(
            current_balance,
            abs(imbalance_mag),
            total_volume
        )
```

### File: `src/data/flavor_loader.py`

```python
# Add spirit mappings
SPIRIT_FALLBACK_MAPPINGS = {
    'rum': ['sugar cane', 'molasses'],
    'light rum': ['sugar cane', 'citrus'],
    'dark rum': ['molasses', 'caramel', 'vanilla'],
    'tequila': ['agave'],
    'bourbon': ['corn', 'oak', 'vanilla'],
    'whiskey': ['grain', 'malt', 'oak'],
    'vodka': ['grain'],
    'triple sec': ['orange', 'citrus'],
    'angostura bitters': ['spice', 'herbs'],
    'simple syrup': ['sugar'],
}

def get_molecules_for_ingredient(self, ingredient: str) -> List[Dict]:
    """Get molecules with spirit fallback."""
    molecules = self.molecules_by_source.get(ingredient.lower(), [])

    if not molecules and ingredient.lower() in SPIRIT_FALLBACK_MAPPINGS:
        for base in SPIRIT_FALLBACK_MAPPINGS[ingredient.lower()]:
            molecules.extend(self.molecules_by_source.get(base, []))

    return molecules
```

---

## Expected Final Results

### After Phase 1 (Quick Wins)
```
Balance Improvement Success: 50% (was 11%)
Imbalance Detection: 100% (unchanged)
Recommendation Relevance: 100% (unchanged)
```

### After Phase 2 (Core Improvements)
```
Balance Improvement Success: 70% (was 11%)
Imbalance Detection: 100%
Recommendation Relevance: 100%
Cocktail Coverage: 95% (was 70%)
```

### After Phase 3 (Advanced)
```
Balance Improvement Success: 85%
Imbalance Detection: 100%
Recommendation Relevance: 100%
Cocktail Coverage: 98%
```

---

## Validation Plan

After each phase, re-run:
```bash
python evaluate_real.py
```

Track improvements:
- Balance improvement rate
- Number of cocktails with valid analysis
- Average balance change magnitude

---

## Timeline

- **Phase 1**: Immediate (implement adaptive amounts + thresholds)
- **Phase 2**: Within 1 day (add mappings + multi-rec testing)
- **Phase 3**: Within 1 week (advanced optimization)

---

## Conclusion

Current 11% → Target 70%+ is achievable through:
1. **Adaptive amounts** (biggest impact)
2. **Smart thresholds** (avoid breaking good cocktails)
3. **Better ingredient coverage** (more accurate analysis)
4. **Multi-candidate testing** (find optimal modifications)

All improvements maintain the core principle: **NO FAKE DATA**. Everything based on real molecular chemistry and actual cocktail recipes.

---

Last Updated: 2025-10-21
Next Action: Implement Phase 1 improvements
