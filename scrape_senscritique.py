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


def extract_date(date_text: str) -> tuple[Optional[str], str]:
    """
    Extrait et convertit une date en ISO.
    Retourne (date_iso, date_raw)
    """
    if not date_text:
        return None, None
    
    date_raw = date_text.strip()
    
    # Essayer d'abord la date relative
    date_iso = parse_relative_date(date_raw)
    if date_iso:
        return date_iso, date_raw
    
    # Essayer ensuite la date française
    date_iso = parse_french_date(date_raw)
    if date_iso:
        return date_iso, date_raw
    
    # Si aucune conversion n'a fonctionné, retourner None
    return None, date_raw


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


def scrape_reviews(max_pages: int = 10) -> Dict:
    """
    Scrape les critiques depuis SensCritique
    """
    all_reviews = []
    page = 1
    
    print(f"🔍 Début du scraping pour {USERNAME}...")
    
    while page <= max_pages:
        # Construire l'URL avec pagination
        if page == 1:
            url = BASE_URL
        else:
            url = f"{BASE_URL}?page={page}"
        
        print(f"📄 Page {page}/{max_pages}: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les articles de critiques
            # Plusieurs sélecteurs possibles selon la structure HTML
            review_articles = soup.find_all('article', {'data-testid': 'review-overview'})
            
            if not review_articles:
                # Essayer d'autres sélecteurs
                review_articles = soup.find_all('article')
                # Filtrer pour ne garder que ceux qui contiennent des critiques
                review_articles = [a for a in review_articles if a.find('a', href=re.compile(r'/critique/'))]
            
            if not review_articles:
                print(f"⚠️  Aucune critique trouvée sur la page {page}")
                break
            
            print(f"✅ {len(review_articles)} critiques trouvées sur la page {page}")
            
            page_reviews = []
            
            for article in review_articles:
                try:
                    review = {}
                    
                    # Extraire le titre
                    title_link = article.find('a', {'data-testid': 'productReviewTitle'})
                    if not title_link:
                        title_link = article.find('h2', {'data-testid': 'reviewTitle'})
                        if title_link:
                            title_link = title_link.find('a')
                    
                    if not title_link:
                        # Chercher dans tout l'article
                        title_link = article.find('a', href=re.compile(r'/(film|serie|jeu|livre)/'))
                    
                    if title_link:
                        title = title_link.get_text(strip=True)
                        # Nettoyer le titre (enlever "Critique de" et "par KiMi_")
                        title = re.sub(r'^Critique de\s+', '', title, flags=re.IGNORECASE)
                        title = re.sub(r'\s+par\s+KiMi_', '', title, flags=re.IGNORECASE)
                        review['title'] = title.strip()
                        
                        # Extraire l'URL
                        href = title_link.get('href', '')
                        if href:
                            if href.startswith('/'):
                                review['url'] = f"https://www.senscritique.com{href}"
                            else:
                                review['url'] = href
                            
                            # Extraire l'ID
                            review['id'] = extract_review_id(review['url'])
                    else:
                        continue  # Pas de titre, on skip cette critique
                    
                    # Extraire la note
                    rating_elem = article.find('div', {'data-testid': 'Rating'})
                    if not rating_elem:
                        rating_elem = article.find(string=re.compile(r'^\d+$'))
                    
                    if rating_elem:
                        if hasattr(rating_elem, 'get_text'):
                            rating_text = rating_elem.get_text(strip=True)
                        else:
                            rating_text = str(rating_elem).strip()
                        
                        rating_match = re.search(r'(\d+)', rating_text)
                        if rating_match:
                            review['rating'] = rating_match.group(1)
                    
                    # Extraire le contenu
                    content_elem = article.find('p', {'data-testid': 'linkify'})
                    if not content_elem:
                        content_elem = article.find('p')
                    
                    if content_elem:
                        content = content_elem.get_text(strip=True)
                        # Limiter à 200 caractères
                        if len(content) > 200:
                            content = content[:200] + '...'
                        review['content'] = content
                    else:
                        review['content'] = 'Pas de commentaire'
                    
                    # Extraire la date
                    date_elem = article.find('time')
                    date_text = None
                    
                    if date_elem:
                        # Essayer l'attribut datetime
                        date_text = date_elem.get('datetime')
                        if not date_text:
                            date_text = date_elem.get_text(strip=True)
                    else:
                        # Chercher dans le texte de l'article
                        date_patterns = [
                            r'il\s+y\s+a\s+\d+\s+(?:jour|jours|semaine|semaines|mois|an|ans)',
                            r'le\s+\d{1,2}\s+\w+\.?\s+\d{4}',
                            r'hier',
                            r"aujourd'hui"
                        ]
                        
                        article_text = article.get_text()
                        for pattern in date_patterns:
                            match = re.search(pattern, article_text, re.IGNORECASE)
                            if match:
                                date_text = match.group(0)
                                break
                    
                    if date_text:
                        date_iso, date_raw = extract_date(date_text)
                        review['date'] = date_iso
                        review['date_raw'] = date_raw
                    else:
                        review['date'] = None
                        review['date_raw'] = None
                    
                    # Extraire l'image
                    img_elem = article.find('img')
                    if img_elem:
                        img_src = img_elem.get('src', '')
                        if img_src and 'senscritique.com' in img_src:
                            review['image'] = img_src
                    
                    # Ajouter la critique seulement si elle a un titre
                    if review.get('title'):
                        page_reviews.append(review)
                
                except Exception as e:
                    print(f"⚠️  Erreur lors de l'extraction d'une critique: {e}")
                    continue
            
            if not page_reviews:
                print(f"⚠️  Aucune critique valide extraite de la page {page}")
                break
            
            all_reviews.extend(page_reviews)
            print(f"✅ {len(page_reviews)} critiques extraites de la page {page}")
            
            # Attendre un peu avant la prochaine requête
            time.sleep(1)
            page += 1
        
        except requests.RequestException as e:
            print(f"❌ Erreur lors de la requête page {page}: {e}")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue page {page}: {e}")
            break
    
    # Trier par date (plus récent en premier)
    def sort_key(review):
        date_str = review.get('date')
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except:
                return datetime.min
        return datetime.min
    
    all_reviews.sort(key=sort_key, reverse=True)
    
    # Construire le résultat final
    result = {
        "username": USERNAME,
        "updated_at": datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        "total_reviews": len(all_reviews),
        "reviews": all_reviews
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
    # Scraper les critiques (max 10 pages)
    reviews_data = scrape_reviews(max_pages=10)
    
    # Sauvegarder dans un fichier JSON
    save_to_json(reviews_data)
    
    # Afficher un résumé
    print(f"\n📊 Résumé:")
    print(f"   - Total: {reviews_data['total_reviews']} critiques")
    print(f"   - Dernière mise à jour: {reviews_data['updated_at']}")
    if reviews_data['reviews']:
        print(f"   - Plus récente: {reviews_data['reviews'][0]['title']} ({reviews_data['reviews'][0]['date']})")

