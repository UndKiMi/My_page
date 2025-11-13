# Script de test des endpoints SensCritique sur Railway
# Usage: .\test-endpoints.ps1

$baseUrl = "https://mypage-production-4e09.up.railway.app"

Write-Host "🧪 Tests des endpoints SensCritique" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Scraping complet forcé
Write-Host "📊 Test 1: Scraping complet forcé (force=true)" -ForegroundColor Yellow
Write-Host "URL: $baseUrl/senscritique?force=true" -ForegroundColor Gray
$startTime = Get-Date
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique?force=true" -Method Get -TimeoutSec 120
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "✅ Temps de réponse: $([math]::Round($duration, 2))s" -ForegroundColor Green
    Write-Host "✅ Username: $($response.username)" -ForegroundColor Green
    Write-Host "✅ Nombre de critiques: $($response.reviews.Count)" -ForegroundColor Green
    Write-Host "✅ Pagination total: $($response.pagination.total)" -ForegroundColor Green
    Write-Host "✅ Pagination hasMore: $($response.pagination.hasMore)" -ForegroundColor Green
    
    if ($response.reviews.Count -gt 0) {
        $firstReview = $response.reviews[0]
        Write-Host "✅ Première critique:" -ForegroundColor Green
        Write-Host "   - Titre: $($firstReview.title)" -ForegroundColor Gray
        $contentPreview = if ($firstReview.content.Length -gt 50) { 
            $firstReview.content.Substring(0, 50) + "..." 
        } else { 
            $firstReview.content 
        }
        Write-Host "   - Contenu: $contentPreview" -ForegroundColor Gray
        
        # Vérifier l'absence de HTML brut
        if ($firstReview.content -match '<[^>]+>|class=|href=|data-testid=') {
            Write-Host "❌ ERREUR: HTML brut détecté dans le contenu!" -ForegroundColor Red
        } else {
            Write-Host "✅ Aucun HTML brut détecté" -ForegroundColor Green
        }
    }
    
    # Vérifier le nombre de critiques
    if ($response.reviews.Count -lt 50) {
        Write-Host "⚠️  ATTENTION: Moins de 50 critiques récupérées (attendu: 60-68)" -ForegroundColor Yellow
    } elseif ($response.reviews.Count -ge 60) {
        Write-Host "✅ Nombre de critiques OK (60-68 attendu)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Cache (réponse instantanée)
Write-Host "📦 Test 2: Cache (réponse instantanée)" -ForegroundColor Yellow
Write-Host "URL: $baseUrl/senscritique" -ForegroundColor Gray
$startTime = Get-Date
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique" -Method Get -TimeoutSec 10
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host "✅ Temps de réponse: $([math]::Round($duration, 2))s" -ForegroundColor Green
    if ($duration -lt 2) {
        Write-Host "✅ Cache fonctionne correctement (réponse < 2s)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Cache peut-être expiré ou non activé" -ForegroundColor Yellow
    }
    Write-Host "✅ Nombre de critiques: $($response.reviews.Count)" -ForegroundColor Green
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Pagination
Write-Host "📄 Test 3: Pagination (limit=5, offset=0)" -ForegroundColor Yellow
Write-Host "URL: $baseUrl/senscritique?limit=5&offset=0" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique?limit=5&offset=0" -Method Get -TimeoutSec 10
    
    Write-Host "✅ Nombre de critiques retournées: $($response.reviews.Count)" -ForegroundColor Green
    Write-Host "✅ Pagination limit: $($response.pagination.limit)" -ForegroundColor Green
    Write-Host "✅ Pagination offset: $($response.pagination.offset)" -ForegroundColor Green
    Write-Host "✅ Pagination page: $($response.pagination.page)" -ForegroundColor Green
    Write-Host "✅ Pagination hasMore: $($response.pagination.hasMore)" -ForegroundColor Green
    Write-Host "✅ Pagination totalPages: $($response.pagination.totalPages)" -ForegroundColor Green
    
    if ($response.reviews.Count -eq 5 -and $response.pagination.hasMore -eq $true) {
        Write-Host "✅ Pagination fonctionne correctement" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Pagination peut avoir un problème" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Filtrage par type
Write-Host "🎬 Test 4: Filtrage par type (type=serie)" -ForegroundColor Yellow
Write-Host "URL: $baseUrl/senscritique?type=serie" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique?type=serie" -Method Get -TimeoutSec 10
    
    Write-Host "✅ Nombre de séries: $($response.reviews.Count)" -ForegroundColor Green
    
    # Vérifier que toutes les critiques sont des séries
    $allSeries = $true
    foreach ($review in $response.reviews) {
        if ($review.url -and $review.url -notmatch '/serie/') {
            $allSeries = $false
            Write-Host "❌ Critique non-série trouvée: $($review.title)" -ForegroundColor Red
            break
        }
    }
    
    if ($allSeries) {
        Write-Host "✅ Toutes les critiques sont des séries" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Stats de monitoring
Write-Host "📊 Test 5: Stats de monitoring" -ForegroundColor Yellow
Write-Host "URL: $baseUrl/senscritique/stats" -ForegroundColor Gray
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique/stats" -Method Get -TimeoutSec 10
    
    Write-Host "✅ Total requests: $($response.totalRequests)" -ForegroundColor Green
    Write-Host "✅ Scraping requests: $($response.scrapingRequests)" -ForegroundColor Green
    Write-Host "✅ Cache hits: $($response.cacheHits)" -ForegroundColor Green
    Write-Host "✅ Errors: $($response.errors.Count)" -ForegroundColor Green
    Write-Host "✅ Last scraping times: $($response.lastScrapingTimes.Count)" -ForegroundColor Green
    
    if ($response.lastScrapingTimes.Count -gt 0) {
        $lastScraping = $response.lastScrapingTimes[-1]
        Write-Host "   - Dernier scraping: $($lastScraping.timestamp) (durée: $($lastScraping.duration)s)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: Vérification des doublons
Write-Host "🔍 Test 6: Vérification des doublons" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/senscritique?force=true" -Method Get -TimeoutSec 120
    
    $titles = $response.reviews | ForEach-Object { $_.title }
    $uniqueTitles = $titles | Select-Object -Unique
    $duplicates = $titles.Count - $uniqueTitles.Count
    
    if ($duplicates -eq 0) {
        Write-Host "✅ Aucun doublon détecté" -ForegroundColor Green
    } else {
        Write-Host "❌ ERREUR: $duplicates doublon(s) détecté(s)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "✅ Tests terminés!" -ForegroundColor Cyan

