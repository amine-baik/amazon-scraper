# amazon-scraper
# Amazon.fr Laptop Scraper

Scraper que j'ai développé pour extraire des données de laptops sur Amazon France.

## Pourquoi ce projet

Amazon bloque les requêtes automatiques avec un status 202.
J'ai du trouver des solutions pour contourner ça :
- Suppression de la signature WebDriver via CDP
- Rotation des User-Agents
- Pauses aléatoires entre les requêtes
- Extraction des prix cachés en JavaScript

## Ce que le script extrait

| Colonne | Contenu |
|---------|---------|
| Titre   | Nom complet du produit 
| Prix (€)| Prix en float 
| Note /5 | Note en étoiles 
| Lien    | URL du produit 
| Page    | Numéro de page source 

## Résultats obtenus

- 58 laptops collectés sur 2 pages
- 98% des produits avec un prix
- Fourchette de prix : 90€ → 1 499€

## Technologies utilisées

- Python 3
- Selenium + WebDriver Manager
- pandas
- openpyxl

## Installation
```bash
pip install selenium webdriver-manager pandas openpyxl
```

## Lancer le script
```bash
python amazon.py
```

## Contact

Amine Baik — baikamine2023@outlook.com
