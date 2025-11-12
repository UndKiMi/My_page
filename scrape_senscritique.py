#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour scraper les critiques SensCritique
Récupère les critiques depuis https://www.senscritique.com/KiMi_/critiques
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

# Configuration
USERNAME = "KiMi_"
BASE_URL = f"https://www.senscritique.com/{USERNAME}/critiques"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Mapping des mois français
MONTHS_FR = {
    'janv': 1, 'janvier': 1,
    'févr': 2, 'février': 2, 'fevr': 2, 'fevrier': 2,
    'mars': 3,
    'avr': 4, 'avril': 4,
    'mai': 5,
    'juin': 6,
    'juil': 7, 'juillet': 7,
    'août': 8, 'aout': 8,
    'sept': 9, 'septembre': 9,
    'oct': 10, 'octobre': 10,
    'nov': 11, 'novembre': 11,
    'déc': 12, 'décembre': 12, 'dec': 12, 'decembre': 12
}


def parse_relative_date(date_text: str) -> Optional[str]:
    """
    Convertit une date relative ("il y a X jours") en date ISO (YYYY-MM-DD)
    """
    if not date_text:
        return None
    
    date_text = date_text.strip().lower()
    today = datetime.now()
    
    # Pattern: "il y a X jour(s)"
    jour_match = re.search(r'il\s+y\s+a\s+(\d+)\s+jour', date_text)
    if jour_match:
        days_ago = int(jour_match.group(1))
        date_obj = today - timedelta(days=days_ago)
        return date_obj.strftime('%Y-%m-%d')
    
    # Pattern: "il y a X semaine(s)"
    semaine_match = re.search(r'il\s+y\s+a\s+(\d+)\s+semaine', date_text)
    if semaine_match:
        weeks_ago = int(semaine_match.group(1))
        date_obj = today - timedelta(weeks=weeks_ago)
        return date_obj.strftime('%Y-%m-%d')
    
    # Pattern: "il y a X mois"
    mois_match = re.search(r'il\s+y\s+a\s+(\d+)\s+mois', date_text)
    if mois_match:
        months_ago = int(mois_match.group(1))
        # Approximation: 30 jours par mois
        date_obj = today - timedelta(days=months_ago * 30)
        return date_obj.strftime('%Y-%m-%d')
    
    # Pattern: "il y a X an(s)"
    an_match = re.search(r'il\s+y\s+a\s+(\d+)\s+an', date_text)
    if an_match:
        years_ago = int(an_match.group(1))
        date_obj = today - timedelta(days=years_ago * 365)
        return date_obj.strftime('%Y-%m-%d')
    
    # Patterns spéciaux
    if 'hier' in date_text:
        date_obj = today - timedelta(days=1)
        return date_obj.strftime('%Y-%m-%d')
    
    if "aujourd'hui" in date_text or "auj" in date_text:
        return today.strftime('%Y-%m-%d')
    
    return None


def parse_french_date(date_text: str) -> Optional[str]:
    """
    Convertit une date française ("le 4 nov. 2025") en date ISO (YYYY-MM-DD)
    """
    if not date_text:
        return None
    
    date_text = date_text.strip().lower()
    
    # Pattern: "le DD MMM. YYYY" ou "le DD MMM YYYY"
    pattern = r'le\s+(\d{1,2})\s+(\w+)\.?\s+(\d{4})'
    match = re.search(pattern, date_text)
    
    if match:
        day = int(match.group(1))
        month_str = match.group(2).rstrip('.')
        year = int(match.group(3))
        
        # Trouver le numéro du mois
        month = None
        for key, value in MONTHS_FR.items():
            if month_str.startswith(key):
                month = value
                break
        
        if month:
            try:
                date_obj = datetime(year, month, day)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                return None
    
    return None


def extract_date(element) -> Dict[str, Optional[str]]:
    """
    Extrait TOUTES les formes de dates avec PRIORITÉ à l'ISO
    
    Priorité 1: Attribut datetime="2025-11-12T..." (le plus fiable)
    Priorité 2: Date française "le 4 nov. 2025"
    Priorité 3: Date relative "il y a X jours"
    
    Args:
        element: BeautifulSoup element ou string
    
    Returns:
        dict: {'date_iso': '2025-11-12T...', 'date_text': 'il y a 5 jours'}
    """
    date_iso = None
    date_text = None
    
    # Si c'est un élément BeautifulSoup
    if hasattr(element, 'find'):
        # PRIORITÉ 1 : Chercher les balises <time datetime="...">
        time_tag = element.find('time', datetime=True)
        if time_tag and time_tag.get('datetime'):
            date_iso = time_tag['datetime']
            # Nettoyer l'ISO (enlever timezone si présent)
            if 'T' in date_iso:
                date_iso = date_iso.split('.')[0].split('+')[0].split('Z')[0]  # Enlever millisecondes et timezone
            date_text = time_tag.get_text(strip=True) or None
        
        # Si pas d'ISO, chercher dans le texte de l'élément
        if not date_iso:
            all_text = element.get_text()
            
            # PRIORITÉ 2 : Chercher date française "le 4 nov. 2025"
            french_date_match = re.search(
                r'(?:le\s+)?(\d{1,2})\s+(janv?\.?|févr?\.?|mars|avr\.?|mai|juin|juil?\.?|août|sept?\.?|oct\.?|nov\.?|déc\.?)\s+(\d{4})',
                all_text,
                re.IGNORECASE
            )
            if french_date_match:
                day = int(french_date_match.group(1))
                month_str = french_date_match.group(2).lower().rstrip('.')
                year = int(french_date_match.group(3))
                month = MONTHS_FR.get(month_str, 1)
                try:
                    date_iso = datetime(year, month, day).isoformat()
                    date_text = french_date_match.group(0)
                except ValueError:
                    pass
            
            # PRIORITÉ 3 : Chercher date relative "il y a X jours/semaines/mois/ans"
            if not date_text:
                # Pattern amélioré pour capturer "jour" ET "jours"
                relative_match = re.search(
                    r'il\s+y\s+a\s+(\d+)\s+(jour|jours|semaine|semaines|mois|an|ans)',
                    all_text,
                    re.IGNORECASE
                )
                if relative_match:
                    number = int(relative_match.group(1))
                    unit = relative_match.group(2).lower()
                    
                    # Normaliser : toujours mettre au pluriel si > 1
                    if number > 1 and not unit.endswith('s'):
                        unit += 's'
                    
                    date_text = f"il y a {number} {unit}"
                    
                    # Calculer l'ISO depuis la date relative
                    now = datetime.now()
                    if 'jour' in unit:
                        date_iso = (now - timedelta(days=number)).isoformat()
                    elif 'semaine' in unit:
                        date_iso = (now - timedelta(weeks=number)).isoformat()
                    elif 'mois' in unit:
                        # Approximation : 1 mois = 30 jours
                        date_iso = (now - timedelta(days=number * 30)).isoformat()
                    elif 'an' in unit:
                        date_iso = (now - timedelta(days=number * 365)).isoformat()
    else:
        # Si c'est une string, utiliser l'ancienne méthode
        date_text = str(element).strip() if element else None
        if date_text:
            # Essayer d'abord la date relative
            date_iso = parse_relative_date(date_text)
            if not date_iso:
                # Essayer ensuite la date française
                date_iso = parse_french_date(date_text)
    
    return {
        'date_iso': date_iso,
        'date_text': date_text
    }


def extract_review_id(url: str) -> Optional[str]:
    """
    Extrait l'ID de la critique depuis l'URL
    Exemple: https://www.senscritique.com/serie/the_rain/critique/331821148 -> 331821148
    """
    if not url:
        return None
    
    match = re.search(r'/critique/(\d+)', url)
    if match:
        return match.group(1)
    return None


def scrape_reviews(max_pages: int = 100, delay: float = 0.5) -> Dict:
    """
    Scrape les critiques depuis SensCritique
    """
    all_reviews = []
    page = 1
    
    print(f"🔍 Scraping des critiques de {USERNAME}...")
    print(f"📄 Pages max: {max_pages} | Délai: {delay}s")
    
    session = requests.Session()
    
    while page <= max_pages:
        # Construire l'URL avec pagination
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}?page={page}"
        
        print(f"📄 Page {page}/{max_pages}...", end=' ')
        
        try:
            response = session.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Multi-sélecteurs CSS (ordre de priorité)
            review_articles = (
                soup.select('article[data-testid="review-overview"]') or
                soup.select('[data-testid*="review"]') or
                soup.select('article.elme-review') or
                soup.select('article')
            )
            
            if not review_articles:
                print(f"✅ Fin (aucune critique sur cette page)")
                break
            
            page_reviews = 0
            for element in review_articles:
                # Extraire le titre avec multi-sélecteurs
                title_el = (
                    element.select_one('a[data-testid="productReviewTitle"]') or
                    element.select_one('h2[data-testid="reviewTitle"]') or
                    element.select_one('h2') or
                    element.select_one('h3')
                )
                
                if not title_el:
                    continue
                
                title = title_el.get_text(strip=True)
                # Nettoyer le titre
                title = re.sub(r'^Critique de\s+', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s+par\s+\w+$', '', title, flags=re.IGNORECASE)
                
                # Extraire le contenu
                content_el = (
                    element.select_one('p[data-testid="linkify"]') or
                    element.select_one('p.elme-review-text') or
                    element.select_one('p')
                )
                content = content_el.get_text(strip=True) if content_el else "Pas de commentaire"
                
                # Extraire les dates avec la fonction optimisée
                dates = extract_date(element)
                
                # Extraire la note
                rating = None
                rating_el = (
                    element.select_one('[data-testid="Rating"]') or
                    element.select_one('[class*="rating"]')
                )
                if rating_el:
                    rating_match = re.search(r'(\d+)', rating_el.get_text())
                    if rating_match:
                        rating = int(rating_match.group(1))
                
                # Extraire le lien
                link_el = (
                    element.select_one('a[href*="/film/"]') or
                    element.select_one('a[href*="/serie/"]') or
                    element.select_one('a[href*="/jeu/"]')
                )
                url = f"https://www.senscritique.com{link_el['href']}" if link_el and link_el.get('href') else None
                
                # Ajouter la critique si valide
                if title and len(title) > 2:
                    review = {
                        'title': title,
                        'content': content[:200] + ('...' if len(content) > 200 else ''),
                        'date': dates['date_text'],
                        'date_raw': dates['date_text'],
                        'created_at': dates['date_iso'],
                        'updated_at': dates['date_iso'],
                        'rating': rating,
                        'url': url
                    }
                    
                    # Éviter les doublons
                    if not any(r['title'] == title for r in all_reviews):
                        all_reviews.append(review)
                        page_reviews += 1
                    
            
            print(f"✅ {page_reviews} critiques")
            
            if page_reviews == 0:
                print("✅ Fin du scraping (page vide)")
                break
            
            # Attendre un peu avant la prochaine requête (rate limiting)
            time.sleep(delay)
            page += 1
        
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la requête page {page}: {e}")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue page {page}: {e}")
            break
    
    # Trier par date ISO (plus récentes en premier)
    all_reviews.sort(
        key=lambda r: r.get('created_at') or r.get('date') or '1970-01-01',
        reverse=True
    )
    
    # Construire le résultat final
    result = {
        "username": USERNAME,
        "updated_at": datetime.now().isoformat(),
        "total_reviews": len(all_reviews),
        "reviews": all_reviews,
        "scraped_at": datetime.now().isoformat()
    }
    
    print(f"\n✅ Scraping terminé: {len(all_reviews)} critiques récupérées")
    
    return result


def save_to_json(data: Dict, filename: str = 'senscritique_reviews.json'):
    """
    Sauvegarde les données dans un fichier JSON
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Données sauvegardées dans {filename}")


if __name__ == '__main__':
    # Scraper jusqu'à 50 pages (augmentable selon besoin)
    reviews_data = scrape_reviews(max_pages=50, delay=0.5)
    
    # Sauvegarder dans un fichier JSON
    save_to_json(reviews_data)
    
    # Afficher un résumé
    print(f"\n📊 Résumé:")
    print(f"   - Total: {reviews_data['total_reviews']} critiques")
    print(f"   - Dernière mise à jour: {reviews_data['updated_at']}")
    if reviews_data['reviews']:
        print(f"   - Plus récente: {reviews_data['reviews'][0]['title']} ({reviews_data['reviews'][0]['date']})")

