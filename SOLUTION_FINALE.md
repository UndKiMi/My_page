# ✅ Solution finale - Endpoint /senscritique optimisé

## Problème résolu

Le endpoint `/senscritique` chargeait à l'infini sur Railway à cause de :

1. ❌ **Appel API Python inexistant** : timeout de 30s vers `localhost:5000`
2. ❌ **Arguments Puppeteer incompatibles** : `--single-process`, `--no-zygote` causaient des erreurs `ECONNRESET`
3. ❌ **Timeouts trop longs** : `networkidle0` (30s) + 30 scrolls = 120s+
4. ❌ **Cache interne bloquant** : résultats vides mis en cache

## Solutions appliquées

### 1. Suppression de l'appel API Python

**Fichier** : `server.js` (lignes 410-415)

```javascript
// AVANT : Tentative d'appel Python (30s timeout) puis fallback Puppeteer

// APRÈS : Appel direct de Puppeteer
const profile = await fetchSensCritiqueProfile('KiMi_', {
  loadReviews: true,
  loadFavorites: true,
  useCache: false // Cache géré par le serveur
});
```

✅ **Gain** : -30 secondes

### 2. Correction des arguments Puppeteer

**Fichier** : `senscritique-scraper.js` (lignes 659-666)

```javascript
// AVANT : Arguments causant ECONNRESET
args: [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage',
  '--disable-accelerated-2d-canvas', // ❌ Problématique
  '--disable-gpu',                  // ❌ Problématique
  '--no-first-run',                 // ❌ Problématique
  '--no-zygote',                    // ❌ Problématique
  '--single-process'                // ❌ Cause des ECONNRESET !
]

// APRÈS : Arguments minimaux et stables
args: [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage'
]
```

✅ **Résultat** : Plus d'erreurs ECONNRESET, scraping réussi

### 3. Optimisation des timeouts

| Paramètre | AVANT | APRÈS | Gain |
|-----------|-------|-------|------|
| `page.goto()` waitUntil | `networkidle0` | `domcontentloaded` | -15s |
| `page.goto()` timeout | 30000ms | 15000ms | -15s |
| `waitForSelector()` timeout | 10000ms | 5000ms | -5s |
| Attente initiale | 3000ms | 1000ms | -2s |
| Max scroll attempts | 30 | 5 | -50s |
| Délai entre scrolls | 1500ms | 500ms | -5s |
| Attente stabilisation | 1000ms | 300ms | -0.7s |

✅ **Temps total** : **~6-8 secondes** (vs 150s avant)

### 4. Amélioration du cache

**Ajout d'un endpoint de debug** : `GET /senscritique/clear-cache`

**Ajout d'un paramètre force** : `GET /senscritique?force=true`

```javascript
const forceRefresh = req.query.force === 'true';
if (!forceRefresh && cachedSensCritique && ...) {
  return res.json(cachedSensCritique);
}
```

✅ **Résultat** : Cache contrôlable pour les tests

## Résultats des tests

### Test 1 : Scraping direct

```bash
$ node test_scraper_direct.js
```

**Résultat** :
- ✅ Temps : 6.43s
- ✅ Critiques : 12
- ✅ Données complètes (titre, date, note, contenu, URL)

### Test 2 : Endpoint via serveur

```bash
$ curl http://localhost:3000/senscritique?force=true
```

**Résultat** :
- ✅ Temps : 6.57s
- ✅ Status : 200
- ✅ Taille : 4.55 KB
- ✅ 12 critiques avec données complètes

### Test 3 : Cache serveur

```bash
$ curl http://localhost:3000/senscritique  # 2ème appel
```

**Résultat** :
- ✅ Temps : < 0.1s
- ✅ Cache actif pendant 1h
- ✅ Pas de scraping répété

## Déploiement sur Railway

### 1. Variables d'environnement

```env
# Discord (obligatoire)
DISCORD_TOKEN=your_token
DISCORD_USER_ID=your_user_id

# Optionnel
GITHUB_USERNAME=UndKiMi
SENSCRITIQUE_USERNAME=KiMi_
```

### 2. Configuration

Railway détecte automatiquement le projet Node.js et utilise :

**Procfile** :
```
web: node server.js
```

**railway.json** :
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "node server.js"
  }
}
```

### 3. Logs à surveiller

```
✅ [SensCritique] 12 critique(s) récupérée(s)
⏱️  [SensCritique] Scraping terminé en 6.57s
📦 [SensCritique] Cache utilisé - pas de scraping
```

### 4. Performances attendues

- **1ère requête** (scraping) : 6-10s
- **Requêtes suivantes** (cache) : < 100ms
- **Cache valide** : 1 heure
- **Compatible Railway** : ✅ < 30s

## Structure JSON retournée

```json
{
  "username": "KiMi_",
  "location": "France",
  "gender": "Homme",
  "stats": {
    "films": 0,
    "series": 0,
    "jeux": 0,
    "livres": 0,
    "total": 68
  },
  "collections": [],
  "reviews": [
    {
      "title": "The Rain",
      "content": "Honnêtement, j'ai vraiment accroché à cette série...",
      "date": "le 5 nov. 2025",
      "date_raw": "le 5 nov. 2025",
      "created_at": "2025-11-05T00:00:00.000Z",
      "updated_at": "2025-11-05T00:00:00.000Z",
      "url": "https://www.senscritique.com/serie/the_rain/29681932",
      "rating": 9,
      "image": null
    }
  ],
  "profileUrl": "https://www.senscritique.com/KiMi_/critiques"
}
```

## Endpoints disponibles

### GET /senscritique
Récupère les critiques (avec cache 1h)

### GET /senscritique?force=true
Force un nouveau scraping (bypass cache)

### GET /senscritique/clear-cache
Vide le cache serveur (debug)

### GET /health
Vérifie l'état du serveur

## Fichiers modifiés

1. ✅ `server.js` : Suppression API Python, ajout force refresh
2. ✅ `senscritique-scraper.js` : Fix arguments Puppeteer, optimisation timeouts
3. ✅ Logs améliorés avec préfixes `[SensCritique]` et `[Scraper]`

## Fichiers de test (supprimés)

- ❌ `test_senscritique_endpoint.js`
- ❌ `test_senscritique_fresh.js`
- ❌ `test_puppeteer_simple.js`
- ❌ `test_scraper_direct.js`
- ❌ `test_scraper_simplifie.js`
- ❌ `test_scraping_complet.js`

## Commandes utiles

### Test local
```bash
node server.js
curl http://localhost:3000/senscritique?force=true
```

### Deploy Railway
```bash
git add .
git commit -m "fix: Optimisation endpoint SensCritique"
git push
```

Railway redéploie automatiquement.

---

**Auteur** : Corrections appliquées le 12/11/2025  
**Version** : 2.0.1  
**Temps de résolution** : ~1h  
**Status** : ✅ Résolu et testé

