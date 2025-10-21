# CocktailIQ: Molecular Cocktail Design System

## Overview
CocktailIQ is the world's first molecular-level cocktail design and optimization system. It uses computational chemistry and flavor science to analyze, modify, and create cocktails based on their molecular composition.

## Key Features
- **Molecular Flavor Analysis**: Decompose cocktails into constituent flavor molecules
- **Flavor Balance Scoring**: Quantitative assessment of sweet/sour/bitter/aromatic balance
- **Intelligent Recommendations**: Get molecular-based suggestions to improve cocktail balance
- **Novel Cocktail Generation**: Create new cocktails using chemical compatibility algorithms
- **Interactive Modification**: Alter existing cocktails and predict flavor impact in real-time

## Scientific Foundation
This system combines:
- TheCocktailDB: 630+ cocktail recipes with detailed ingredient information
- FlavorDB: Comprehensive molecular flavor compound database
- Computational chemistry principles (molecular similarity, functional group analysis)
- Machine learning for pattern recognition and optimization

## Project Structure
```
cocktailiq/
├── src/                    # Source code
│   ├── data/              # Data processing modules
│   ├── analysis/          # Molecular analysis engines
│   ├── recommendation/    # Recommendation system
│   └── generation/        # Novel cocktail generator
├── data/                  # Data files
│   ├── raw/              # Original data sources
│   ├── interim/          # Intermediate processing
│   └── processed/        # Clean, analysis-ready data
├── docs/                  # Documentation
│   ├── paper/            # Scientific paper
│   └── figures/          # Visualizations
├── tests/                 # Test suite
├── notebooks/             # Jupyter notebooks for exploration
└── results/               # Generated cocktails and analyses
```

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from src.analysis import CocktailAnalyzer
from src.recommendation import FlavorOptimizer

# Analyze a cocktail
analyzer = CocktailAnalyzer()
score = analyzer.score_cocktail("Negroni")

# Get improvement recommendations
optimizer = FlavorOptimizer()
suggestions = optimizer.recommend_improvements("Negroni")
```

## Research Paper
This project is accompanied by a scientific paper documenting the methodology, algorithms, and validation results. See `docs/paper/` for details.

## Contributing
This is a research project. Contributions welcome for:
- Algorithm improvements
- Additional data sources
- Validation experiments
- Documentation

## License
MIT License

## Citation
If you use this work, please cite:
```
[Paper citation to be added upon publication]
```

## Contact
For questions or collaboration: [Your contact info]
