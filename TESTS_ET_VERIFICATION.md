# 🧪 Tests et vérification - Guide complet

## Commandes de test

### 1. Test endpoint de base
```bash
curl "http://localhost:3000/senscritique"
```

**Attendu** : JSON avec pagination
```json
{
  "username": "KiMi_",
  "reviews": [...],
  "pagination": {
    "total": 12,
    "limit": 50,
    "offset": 0,
    "hasMore": false,
    "page": 1,
    "totalPages": 1
  }
}
```

### 2. Test pagination
```bash
# Première page (5 critiques)
curl "http://localhost:3000/senscritique?limit=5&offset=0"

# Deuxième page
curl "http://localhost:3000/senscritique?limit=5&offset=5"

# Troisième page
curl "http://localhost:3000/senscritique?limit=5&offset=10"
```

### 3. Test filtrage par type
```bash
# Films uniquement
curl "http://localhost:3000/senscritique?type=film"

# Séries uniquement
curl "http://localhost:3000/senscritique?type=serie"

# Jeux uniquement
curl "http://localhost:3000/senscritique?type=jeu"
```

### 4. Test force refresh
```bash
curl "http://localhost:3000/senscritique?force=true"
```

### 5. Test statistiques monitoring
```bash
curl "http://localhost:3000/senscritique/stats"
```

**Attendu** :
```json
{
  "totalRequests": 5,
  "scrapingRequests": 2,
  "cacheHits": 3,
  "errors": [],
  "lastScrapingTimes": [...],
  "alerts": [],
  "stats": {
    "avgScrapingDuration": 6.45,
    "cacheHitRate": 60.0,
    "errorRate": 0,
    "lastScraping": {...},
    "recentAlerts": []
  }
}
```

### 6. Test vider le cache
```bash
curl "http://localhost:3000/senscritique/clear-cache"
```

**Attendu** :
```json
{
  "success": true,
  "message": "Cache SensCritique vidé"
}
```

---

## Vérifications frontend

### 1. Ouvrir le portfolio
```
http://localhost:3000
```

### 2. Vérifier section SensCritique
- ✅ Images des œuvres affichées (60×90px)
- ✅ Titre, contenu, date, note visibles
- ✅ Hover sur image : effet zoom
- ✅ Hover sur critique : fond légèrement éclairci
- ✅ Bouton "Charger plus (1/X)" visible si > 5 critiques

### 3. Tester bouton "Charger plus"
1. Cliquer sur "Charger plus"
2. Vérifier : texte devient "Chargement..."
3. Vérifier : 5 nouvelles critiques apparaissent
4. Vérifier : bouton se met à jour "Charger plus (2/X)"
5. Vérifier : bouton disparaît à la dernière page

### 4. Console navigateur
Ouvrir F12 → Console :
```
✅ 5 critiques affichées
📊 Données SensCritique reçues: { username: "KiMi_", reviewsCount: 5 }
```

---

## Vérification logs backend

### Logs attendus au démarrage
```
✅ Bot connecté: YourBot#1234
📊 Serveurs: 1
🔍 Recherche de l'utilisateur...
```

### Logs premier scraping
```
🎬 [SensCritique] Démarrage du scraping Puppeteer...
🚀 [Scraper] Lancement de Puppeteer...
📄 [Scraper] Navigation vers: https://www.senscritique.com/KiMi_/critiques
✅ [Scraper] Sélecteur trouvé, page chargée
📊 [Scraper] État initial du DOM: { articles: 6, reviewElements: 12, links: 25 }
🎯 [Scraper] Sélecteur CSS utilisé: "article[data-testid="review-overview"]" (6 éléments trouvés)
✅ [Scraper] 12 critique(s) extraite(s)
📊 [Scraper] Exemples de dates: le 5 nov. 2025, le 5 nov. 2025, le 4 nov. 2025
📊 [Scraper] Premières critiques: The Rain, Ratatouille, Star Citizen
⏱️  [SensCritique] Scraping terminé en 6.57s
✅ [SensCritique] 12 critique(s) récupérée(s)
📊 [Monitoring] Stats: 1 requêtes | 1 scraping | 0 cache
```

### Logs utilisation cache
```
📦 [SensCritique] Cache utilisé - pas de scraping
📊 [Monitoring] Stats: 2 requêtes | 1 scraping | 1 cache
```

### Logs alerte 0 critiques
```
✅ [SensCritique] 0 critique(s) récupérée(s)
🚨 [SensCritique] ALERTE : 0 critiques extraites. Vérifier la structure HTML !
📊 [Monitoring] Alerte enregistrée: 2025-11-12T23:50:00.000Z
```

---

## Vérification fichier monitoring.json

### Lire le fichier
```bash
cat monitoring.json
```

ou sur Windows :
```bash
type monitoring.json
```

### Structure attendue
```json
{
  "totalRequests": 10,
  "scrapingRequests": 3,
  "cacheHits": 7,
  "errors": [],
  "lastScrapingTimes": [
    {
      "timestamp": "2025-11-12T23:45:00.000Z",
      "duration": 6.57,
      "reviewsCount": 12
    },
    {
      "timestamp": "2025-11-12T23:50:00.000Z",
      "duration": 6.23,
      "reviewsCount": 12
    }
  ],
  "alerts": []
}
```

---

## Tests de robustesse

### Test 1 : Scraping multiple rapide
```bash
# Lancer 10 requêtes successives
for i in {1..10}; do
  curl "http://localhost:3000/senscritique" > /dev/null 2>&1 &
done
wait

# Vérifier les stats
curl "http://localhost:3000/senscritique/stats"
```

**Attendu** :
- 1 scraping uniquement (le premier)
- 9 hits de cache
- `cacheHitRate: 90.0%`

### Test 2 : Force refresh
```bash
# Vider le cache
curl "http://localhost:3000/senscritique/clear-cache"

# Forcer nouveau scraping
time curl "http://localhost:3000/senscritique?force=true"
```

**Attendu** :
- Temps de réponse : 6-10 secondes
- Logs de scraping dans la console

### Test 3 : Pagination complète
```bash
# Script pour tester toutes les pages
#!/bin/bash
PAGE=0
while true; do
  OFFSET=$((PAGE * 5))
  RESPONSE=$(curl -s "http://localhost:3000/senscritique?limit=5&offset=$OFFSET")
  HAS_MORE=$(echo $RESPONSE | jq -r '.pagination.hasMore')
  
  echo "Page $((PAGE + 1)): $(echo $RESPONSE | jq -r '.reviews | length') critiques"
  
  if [ "$HAS_MORE" = "false" ]; then
    break
  fi
  
  PAGE=$((PAGE + 1))
done
```

### Test 4 : Erreur réseau simulée
```bash
# Arrêter le serveur
pkill -f "node server.js"

# Tenter un appel
curl "http://localhost:3000/senscritique"
```

**Attendu** : `curl: (7) Failed to connect`

```bash
# Redémarrer
node server.js
```

---

## Checklist de vérification complète

### Backend ✅
- [ ] Serveur démarre sans erreur
- [ ] Endpoint `/senscritique` répond
- [ ] Endpoint `/senscritique/stats` répond
- [ ] Endpoint `/senscritique/clear-cache` répond
- [ ] Pagination fonctionne (`?limit=5&offset=0`)
- [ ] Filtrage fonctionne (`?type=film`)
- [ ] Force refresh fonctionne (`?force=true`)
- [ ] Fichier `monitoring.json` créé automatiquement
- [ ] Logs détaillés dans la console
- [ ] Alerte 0 critiques fonctionnelle

### Frontend ✅
- [ ] Section SensCritique visible
- [ ] Images des œuvres affichées
- [ ] Titre, contenu, date, note visibles
- [ ] Bouton "Charger plus" visible
- [ ] Clic sur "Charger plus" charge nouvelles critiques
- [ ] Message "Aucune critique disponible" si 0 critiques
- [ ] Hover effects fonctionnent
- [ ] Liens vers critiques fonctionnent

### Monitoring ✅
- [ ] Fichier `monitoring.json` se met à jour
- [ ] Stats calculent correctement
- [ ] Alertes enregistrées si 0 critiques
- [ ] Cache hit rate correct
- [ ] Durée moyenne calculée
- [ ] Derniers temps de scraping enregistrés

### Logs ✅
- [ ] Sélecteur CSS loggé
- [ ] Nombre de critiques loggé
- [ ] Temps de scraping loggé
- [ ] Exemples de dates loggés
- [ ] Premiers titres loggés
- [ ] Erreurs loggées avec stack trace

---

## Commandes de déploiement

### Local
```bash
# Installer les dépendances
npm install

# Démarrer
node server.js

# Tester
curl "http://localhost:3000/senscritique"
```

### Railway
```bash
# Commit
git add .
git commit -m "feat: Monitoring + pagination + images + alertes"

# Push (Railway redéploie automatiquement)
git push

# Vérifier les logs Railway
railway logs

# Tester
curl "https://votre-app.up.railway.app/senscritique"
```

### Variables d'environnement Railway
```bash
# Discord (obligatoire)
DISCORD_TOKEN=...
DISCORD_USER_ID=...

# GitHub (optionnel)
GITHUB_USERNAME=UndKiMi

# SensCritique (optionnel)
SENSCRITIQUE_USERNAME=KiMi_

# Webhook Discord (optionnel)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/.../...
```

---

## Troubleshooting

### Problème : 0 critiques extraites

**Vérifier** :
```bash
# 1. Vérifier les logs
curl "http://localhost:3000/senscritique/stats"

# 2. Vérifier le sélecteur utilisé
# Rechercher dans les logs : "🎯 [Scraper] Sélecteur CSS utilisé:"

# 3. Forcer nouveau scraping
curl "http://localhost:3000/senscritique?force=true"
```

**Solution** :
- Inspecter https://www.senscritique.com/KiMi_/critiques
- Identifier le nouveau sélecteur CSS
- Modifier `senscritique-scraper.js` lignes 852-874
- Redéployer

### Problème : Bouton "Charger plus" ne s'affiche pas

**Vérifier** :
```javascript
// Dans la console navigateur (F12)
console.log(CONFIG.totalPages); // Doit être > 1
console.log(CONFIG.currentPage); // Doit être < totalPages
```

**Solution** :
- Vérifier que `reviewsPerPage: 5` dans CONFIG
- Vérifier que le backend retourne `pagination.totalPages`
- Forcer refresh de la page (Ctrl+F5)

### Problème : Images ne s'affichent pas

**Vérifier** :
```javascript
// Dans la console navigateur
const reviews = await fetch('http://localhost:3000/senscritique').then(r => r.json());
console.log(reviews.reviews[0].image); // Doit être une URL ou null
```

**Solution** :
- Si `null` : normal, toutes les critiques n'ont pas d'image
- Si `undefined` : vérifier le scraper (champ `image` manquant)
- Si erreur CORS : vérifier que l'image est accessible

### Problème : Monitoring.json ne se crée pas

**Vérifier** :
```bash
# Permissions d'écriture
ls -la monitoring.json

# Si n'existe pas, créer manuellement
echo '{"totalRequests":0,"scrapingRequests":0,"cacheHits":0,"errors":[],"lastScrapingTimes":[],"alerts":[]}' > monitoring.json

# Redémarrer le serveur
node server.js
```

---

**Version** : 1.0.0  
**Date** : 12 novembre 2025  
**Usage** : Guide de test et vérification post-déploiement

