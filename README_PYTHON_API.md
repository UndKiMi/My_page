# API Python pour SensCritique

Ce système remplace l'ancien scraper Node.js/Puppeteer par un scraper Python utilisant BeautifulSoup4.

## Installation

1. Installer Python 3.8+ si ce n'est pas déjà fait

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

### Option 1: Script standalone

Pour scraper les critiques et les sauvegarder dans un fichier JSON :

```bash
python scrape_senscritique.py
```

Cela créera un fichier `senscritique_reviews.json` avec toutes les critiques.

### Option 2: API Flask

Pour démarrer l'API Flask qui sert les critiques :

```bash
python api_senscritique.py
```

L'API sera accessible sur `http://localhost:5000/api/critiques`

#### Endpoints disponibles :

- `GET /api/critiques` - Récupère toutes les critiques
- `GET /api/health` - Vérifie l'état de l'API
- `GET /` - Page d'accueil avec la documentation

## Configuration

### Variables d'environnement

Pour l'API Flask :
- `PORT` - Port sur lequel l'API écoute (défaut: 5000)

Pour le backend Node.js :
- `PYTHON_API_URL` - URL de l'API Python (défaut: http://localhost:5000/api/critiques)

### Exemple .env

```env
PORT=5000
PYTHON_API_URL=http://localhost:5000/api/critiques
```

## Déploiement sur Railway

1. Créer un nouveau service Railway pour l'API Python
2. Ajouter les variables d'environnement nécessaires
3. Railway détectera automatiquement le fichier `requirements.txt`
4. L'API démarrera automatiquement avec `python api_senscritique.py`

## Structure des données

Le JSON retourné a cette structure :

```json
{
  "username": "KiMi_",
  "updated_at": "2025-11-12T23:00:00",
  "total_reviews": 66,
  "reviews": [
    {
      "id": "331821148",
      "title": "The Rain",
      "rating": "9",
      "content": "Extrait de la critique...",
      "date": "2025-11-05",
      "date_raw": "il y a 7 jours",
      "url": "https://www.senscritique.com/serie/the_rain/critique/331821148",
      "image": "https://..."
    }
  ]
}
```

## Cache

L'API utilise un système de cache :
- Cache en mémoire (10 minutes)
- Cache sur disque (fichier `senscritique_reviews.json`)
- Mise à jour automatique en arrière-plan quand le cache expire

## Notes

- Le scraper gère automatiquement plusieurs pages (max 10 par défaut)
- Les dates relatives ("il y a X jours") sont converties en dates ISO
- Les dates françaises ("le 4 nov. 2025") sont aussi converties en dates ISO
- Les critiques sont triées par date (plus récent en premier)

