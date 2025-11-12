# Corrections Backend SensCritique - Résolution du chargement infini

## Problème identifié

Le endpoint `/senscritique` sur Railway chargeait à l'infini car :
1. **Appel API Python bloquant** : tentative de connexion à `localhost:5000` (timeout de 30s)
2. **Timeouts Puppeteer trop longs** : `networkidle0` (30s) + 30 tentatives de scroll
3. **Temps total** : 30s (Python) + 120s (Puppeteer) = **150 secondes** → Railway coupe la connexion

## Solutions appliquées

### 1. Désactivation de l'API Python (`server.js`)

**AVANT** :
```javascript
// Tentait d'appeler localhost:5000/api/critiques (30s timeout)
// Puis fallback sur Puppeteer (120s)
```

**APRÈS** :
```javascript
// Appel DIRECT de Puppeteer sans tentative API Python
const profile = await fetchSensCritiqueProfile('KiMi_');
```

✅ **Gain de temps** : -30 secondes

### 2. Optimisation des timeouts Puppeteer (`senscritique-scraper.js`)

| Paramètre | AVANT | APRÈS | Gain |
|-----------|-------|-------|------|
| `page.goto()` waitUntil | `networkidle0` | `domcontentloaded` | -15s |
| `page.goto()` timeout | 30000ms | 15000ms | -15s |
| `waitForSelector()` timeout | 10000ms | 5000ms | -5s |
| Attente initiale | 3000ms | 1000ms | -2s |
| Max scroll attempts | 30 | 5 | -50s |
| Délai entre scrolls | 1500ms | 500ms | -5s |
| Attente stabilisation | 1000ms | 300ms | -0.7s |

✅ **Temps total estimé** : **< 25 secondes** (dans les limites Railway)

### 3. Logs améliorés

**Ajout de logs structurés** :
```
🎬 [SensCritique] Démarrage du scraping Puppeteer...
🚀 [Scraper] Lancement de Puppeteer...
📄 [Scraper] Navigation vers: https://...
✅ [Scraper] Sélecteur trouvé, page chargée
📊 [Scraper] État initial du DOM: {...}
📊 [Scraper] Scroll 1/5: 12 critiques
✅ [Scraper] Scroll terminé: 25 critiques après 3 tentatives
📄 [Scraper] HTML récupéré: 456.78 KB
✅ [Scraper] Puppeteer fermé
⏱️  [SensCritique] Scraping terminé en 18.45s
✅ [SensCritique] 25 critique(s) récupérée(s)
```

### 4. Cache conservé (1 heure)

Le cache backend reste actif :
- **Durée** : 1 heure (`SC_CACHE_DURATION = 3600000`)
- **Évite** : scraping répété pour chaque visite frontend
- **Performance** : réponse instantanée si cache valide

## Configuration Railway

### Variables d'environnement à définir

```env
# Discord (obligatoire)
DISCORD_TOKEN=votre_token
DISCORD_USER_ID=votre_user_id

# GitHub (facultatif)
GITHUB_USERNAME=UndKiMi

# SensCritique (facultatif)
SENSCRITIQUE_USERNAME=KiMi_
```

### Commande de démarrage

Railway utilise automatiquement :
```
node server.js
```

Voir `Procfile` :
```
web: node server.js
```

## Test en local

### Démarrage
```bash
node server.js
```

### Test du endpoint
```bash
# Avec curl
curl http://localhost:3000/senscritique

# Avec navigateur
http://localhost:3000/senscritique
```

### Temps de réponse attendus

- **1ère requête (pas de cache)** : 15-25s
- **Requêtes suivantes (cache actif)** : < 100ms
- **Après 1h (cache expiré)** : 15-25s

## Résultats attendus

✅ Réponse JSON avec structure :
```json
{
  "username": "KiMi_",
  "location": "France",
  "gender": "Homme",
  "stats": {
    "total": 68
  },
  "reviews": [
    {
      "title": "Titre du film/série",
      "content": "Extrait du commentaire...",
      "date": "il y a 5 jours",
      "date_raw": "il y a 5 jours",
      "rating": 8,
      "url": "https://www.senscritique.com/..."
    }
  ]
}
```

## Vérification sur Railway

### 1. Logs à surveiller
```
📦 [SensCritique] Cache utilisé - pas de scraping  ← Bon signe (cache actif)
🎬 [SensCritique] Démarrage du scraping...          ← Cache expiré
✅ [SensCritique] 25 critique(s) récupérée(s)       ← Succès
⏱️  [SensCritique] Scraping terminé en 18.45s      ← Dans les limites
```

### 2. Erreurs à surveiller
```
❌ [Scraper] Erreur Puppeteer: Protocol error       ← Puppeteer crash
❌ [SensCritique] Erreur scraping: timeout          ← Timeout Railway
```

### Solutions si erreurs persistent

1. **Si Puppeteer crash** : Réduire encore `maxScrollAttempts` à 3
2. **Si timeout Railway** : Réduire `page.goto()` timeout à 10s
3. **Si 0 critiques** : Vérifier structure HTML SensCritique (sélecteurs CSS)

## Frontend (aucune modification nécessaire)

Le frontend continue d'appeler :
```javascript
const response = await fetch(`${CONFIG.backendUrl}/senscritique`);
```

Aucun changement côté client requis.

---

**Auteur** : Corrections appliquées le 12/11/2025
**Version backend** : 2.0.0
**Frameworks** : Node.js + Express + Puppeteer + JSDOM

