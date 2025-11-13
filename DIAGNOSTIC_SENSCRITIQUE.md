# Diagnostic SensCritique - 0 critiques récupérées

## Problème identifié

L'endpoint `/senscritique` retourne :
```json
{
  "username": "KiMi_",
  "stats": { "total": 68 },
  "reviews": [],
  "collections": [],
  "pagination": { "total": 0, "hasMore": false }
}
```

## Cause racine

**La popup de cookies SensCritique bloque le scraping Puppeteer !**

### Preuve
Inspection de la page https://www.senscritique.com/KiMi_/critiques :
- ✅ 6 articles trouvés avec `data-testid="review-overview"`
- ✅ Structure HTML correcte (heading h2, paragraph p)
- ✅ Sélecteurs CSS fonctionnels
- ❌ Popup cookies affichée par-dessus le contenu

### Screenshot
![Popup cookies visible](capture d'écran montre la popup "Avec votre consentement...")

## Solution appliquée

Ajout d'un code dans `senscritique-scraper.js` pour :
1. Détecter la popup cookies après le chargement de la page
2. Chercher le bouton "Accepter & Fermer" ou "Continuer sans accepter"
3. Cliquer automatiquement sur le bouton
4. Attendre 1.5s que la popup disparaisse

### Code ajouté (lignes 743-780)
```javascript
// IMPORTANT : Accepter automatiquement les cookies pour débloquer le contenu
console.log('🍪 [Scraper] Recherche de la popup cookies...');
try {
  const cookieButtonAccepted = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const cookieButton = buttons.find(b => {
      const text = b.textContent.toLowerCase();
      return text.includes('accepter') || text.includes('continuer') || text.includes('fermer');
    });
    
    if (cookieButton) {
      cookieButton.click();
      return true;
    }
    return false;
  });
  
  if (cookieButtonAccepted) {
    console.log('✅ [Scraper] Cookies acceptés automatiquement');
    await new Promise(resolve => setTimeout(resolve, 1500));
  }
} catch (e) {
  console.log('⚠️  [Scraper] Erreur acceptation cookies:', e.message);
}
```

## Structure HTML vérifiée

```html
<article data-testid="review-overview" class="sc-9c2f7502-0 eEUaEZ">
  <div class="sc-9c2f7502-1 bmXsXd">
    <a href="/jeuvideo/legendes_pokemon_z_a/79385903">
      <img alt="Légendes Pokémon : Z-A" src="...">
    </a>
    <div class="sc-9c2f7502-2">
      <div>Note: 1</div>
    </div>
  </div>
  <div>
    <h2>Critique de Légendes Pokémon : Z-A par KiMi_</h2>
    <p>Vraiment une honte de vendre un jeu pareil en big 2025</p>
    <a href="/jeuvideo/legendes_pokemon_z_a/critique/332166991">Lire la critique</a>
    <div>
      <p>Par KiMi_</p>
      <p>il y a 36 minutes</p>
    </div>
  </div>
</article>
```

## Sélecteurs CSS confirmés

- ✅ `article[data-testid="review-overview"]` - Fonctionnel
- ✅ `h2` pour le titre
- ✅ `p` pour le contenu
- ✅ `a[href*="/critique/"]` pour le lien
- ✅ Date dans `<p>` avec "il y a X" ou "le DD MMM. YYYY"

## Prochaines étapes

1. **Commit et push** les modifications :
   ```bash
   git add senscritique-scraper.js
   git commit -m "fix: Acceptation automatique cookies SensCritique pour débloquer scraping"
   git push
   ```

2. **Attendre 2-3 minutes** que Railway redéploie

3. **Tester l'endpoint** :
   ```
   https://mypage-production-4e09.up.railway.app/senscritique?force=true
   ```

4. **Vérifier les logs Railway** :
   - Doit afficher "✅ [Scraper] Cookies acceptés automatiquement"
   - Doit afficher "📊 [Scraper] Éléments trouvés: { withTestId: 6, ... }"
   - Doit afficher "✅ [Scraper] 60-68 critique(s) récupérée(s)"

## Résultat attendu

```json
{
  "username": "KiMi_",
  "stats": { "total": 68 },
  "reviews": [
    {
      "title": "Légendes Pokémon : Z-A",
      "content": "Vraiment une honte de vendre un jeu pareil en big 2025",
      "date": "il y a 36 minutes",
      "rating": 1,
      "url": "https://www.senscritique.com/jeuvideo/legendes_pokemon_z_a/critique/332166991"
    },
    // ... 67 autres critiques
  ],
  "pagination": {
    "total": 68,
    "hasMore": true
  }
}
```

## En cas d'échec

Si le scraping retourne toujours 0 critiques après le déploiement :

1. **Vérifier les logs Railway** pour voir si les cookies sont acceptés
2. **Augmenter le délai d'attente** après l'acceptation des cookies (ligne 774)
3. **Effectuer un rollback** si nécessaire :
   ```powershell
   .\rollback.ps1
   ```

## Notes techniques

- Puppeteer version : 24.29.1
- User-Agent : Chrome/120.0.0.0
- Timeout page.goto : 15s
- Timeout waitForSelector : 5s
- Max scroll attempts : 50
- Scroll delay : 1000ms

