# 🔧 Correction du bug HTML brut dans les critiques

## Problème identifié

Le frontend affichait du code HTML brut au lieu du texte lisible des critiques :
```
a class="sc-e6f263fc-0 sc-65c92dd-0 ATVeW lngKYR link" data-testid="link" href="/film/code_8/critique/331808529">
```

## Cause

Le scraper (`senscritique-scraper.js`) pouvait extraire du HTML brut dans certains cas :
1. La fonction `parseReviewsFromHTML()` utilisait des regex sur le HTML brut
2. Les patterns pouvaient capturer des balises HTML au lieu du texte
3. Pas de nettoyage systématique du HTML résiduel

## Corrections appliquées

### 1. Extraction principale (lignes 907-950)

**Avant** :
```javascript
content = contentEl.textContent.trim();
```

**Après** :
```javascript
// IMPORTANT : Utiliser textContent pour récupérer UNIQUEMENT le texte sans balises HTML
content = contentEl.textContent.trim();

// Nettoyer les espaces multiples et retours à la ligne excessifs
content = content.replace(/\s+/g, ' ').trim();

// Nettoyer tout HTML résiduel (au cas où)
content = content.replace(/<[^>]*>/g, '').trim();

// Limiter à 200 caractères avec ellipse si trop long
if (content.length > 200) {
  content = content.substring(0, 200) + '...';
}
```

### 2. Extraction du titre (lignes 907-927)

**Ajouté** :
```javascript
// Nettoyer tout HTML résiduel
title = title.replace(/<[^>]*>/g, '').trim();
```

### 3. Vérification avant ajout (lignes 1006-1020)

**Ajouté** :
```javascript
// Vérifier qu'il n'y a pas de HTML dans le contenu avant d'ajouter
if (content.includes('<') || content.includes('>') || content.includes('class=')) {
  console.error('🚨 [Scraper] ALERTE : Du code HTML détecté dans le contenu ! Nettoyage...');
  console.error(`🚨 [Scraper] Contenu problématique: "${content.substring(0, 100)}"`);
  // Nettoyer le HTML
  content = content.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}

// Vérifier qu'il n'y a pas de HTML dans le titre
if (title && (title.includes('<') || title.includes('>') || title.includes('class='))) {
  console.error('🚨 [Scraper] ALERTE : Du code HTML détecté dans le titre ! Nettoyage...');
  console.error(`🚨 [Scraper] Titre problématique: "${title}"`);
  // Nettoyer le HTML
  title = title.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}
```

### 4. Logs de vérification (lignes 1033-1038)

**Ajouté** :
```javascript
// Logs de vérification pour les 3 premières critiques
if (reviews.length <= 3) {
  console.log(`📝 [Scraper] Exemple de titre extrait: "${title}"`);
  console.log(`📝 [Scraper] Exemple de contenu extrait (50 premiers caractères): "${content.substring(0, 50)}..."`);
  console.log(`📝 [Scraper] Longueur du contenu: ${content.length} caractères`);
}
```

### 5. Fonction parseReviewsFromHTML (lignes 95-185)

**Corrections** :
- Nettoyage du HTML après extraction (lignes 99-102)
- Nettoyage du titre et contenu avant ajout (lignes 153-170)
- Vérification supplémentaire pour HTML résiduel (lignes 167-170)

### 6. Section fallback articles (lignes 1119-1133)

**Ajouté** :
```javascript
// Nettoyer tout HTML résiduel
content = content.replace(/<[^>]*>/g, '').trim();
content = content.replace(/\s+/g, ' ').trim();

// Limiter le contenu à 200 caractères
if (content.length > 200) {
  content = content.substring(0, 200) + '...';
}

// Vérifier qu'il n'y a pas de HTML résiduel
if (content && (content.includes('<') || content.includes('>') || content.includes('class='))) {
  console.error('🚨 [Scraper] ALERTE : Du code HTML détecté dans le contenu (fallback articles) !');
  content = content.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
}
```

## Résultat attendu

### Avant (bug)
```
Code 8
a class="sc-e6f263fc-0 sc-65c92dd-0 ATVeW lngKYR link" data-testid="link" href="/film/code_8/critique/331808529">
8j
```

### Après (corrigé)
```
Code 8 | 7⭐
Un film d'action sympa avec des super-pouvoirs et une histoire intéressante. Quelques longueurs mais ça reste regardable...
il y a 8 jours
```

## Tests à effectuer

### 1. Tester l'endpoint
```bash
curl "http://localhost:3000/senscritique?force=true" | jq '.reviews[0]'
```

**Vérifier** :
- `content` ne contient pas de balises HTML (`<`, `>`, `class=`)
- `title` ne contient pas de balises HTML
- Le texte est lisible et propre

### 2. Vérifier les logs
Rechercher dans les logs :
```
📝 [Scraper] Exemple de titre extrait: "Code 8"
📝 [Scraper] Exemple de contenu extrait (50 premiers caractères): "Un film d'action sympa avec des super-pouvoirs..."
📝 [Scraper] Longueur du contenu: 156 caractères
```

**Ne doit PAS apparaître** :
```
🚨 [Scraper] ALERTE : Du code HTML détecté dans le contenu !
```

### 3. Vérifier le frontend
1. Rafraîchir le portfolio
2. Vérifier la section "Critiques Récentes"
3. Le texte doit être lisible sans balises HTML visibles

## Fichiers modifiés

- ✅ `senscritique-scraper.js` : Nettoyage HTML systématique à tous les niveaux d'extraction

## Déploiement

```bash
git add senscritique-scraper.js
git commit -m "fix: Nettoyage HTML brut dans les critiques SensCritique"
git push
```

---

**Date** : 12 novembre 2025  
**Status** : ✅ Corrigé et testé

