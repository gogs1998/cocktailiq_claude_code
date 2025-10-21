# Claude Development Notes

## Project Principles

**CRITICAL RULE: NO FAKE DATA, NO SUBSTITUTIONS, NO LIES**
- Only use real data from the actual datasets
- Only report actual computed results
- No placeholder values or example data
- No simulated or estimated results
- If data is missing, acknowledge it - don't fabricate
- All statistics, scores, and analyses must be computed from real data
- All molecular mappings must come from actual FlavorDB data
- All cocktail recipes must come from actual TheCocktailDB data

## Development Guidelines

1. **Data Integrity**
   - Parse actual JSON files in raw/ directory
   - Compute real statistics from parsed data
   - Document data quality issues honestly
   - Report actual coverage and missing data

2. **Scientific Rigor**
   - All algorithms must be implemented and tested
   - Results in paper must match actual computed values
   - No theoretical examples - only real implementations
   - Validate all claims with code and data

3. **Documentation**
   - Paper must reflect actual methodology implemented
   - Update paper sections as features are completed
   - Mark incomplete sections clearly
   - Provide real example outputs, not hypotheticals

4. **Version Control**
   - Commit regularly with meaningful messages
   - Push to GitHub frequently
   - Document all major milestones
   - Tag releases appropriately

## Current Status

[This section will be updated as development progresses]

### Completed
- Project structure created
- Scientific paper framework established
- Requirements defined

### In Progress
- Data processing pipeline

### Pending
- All core functionality
- Real data analysis
- Validation and results
