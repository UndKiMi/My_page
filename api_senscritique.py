#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Flask pour servir les critiques SensCritique
Endpoint: GET /api/critiques
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
import json
from scrape_senscritique import scrape_reviews
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin

# Cache pour les critiques
cached_reviews = None
cache_timestamp = None
CACHE_DURATION = 600  # 10 minutes en secondes


def load_cached_reviews():
    """
    Charge les critiques depuis le cache ou le fichier JSON
    """
    global cached_reviews, cache_timestamp
    
    # Essayer de charger depuis le fichier JSON
    if os.path.exists('senscritique_reviews.json'):
        try:
            with open('senscritique_reviews.json', 'r', encoding='utf-8') as f:
                cached_reviews = json.load(f)
                cache_timestamp = datetime.now().timestamp()
                print(f"✅ Cache chargé depuis le fichier: {cached_reviews['total_reviews']} critiques")
                return True
        except Exception as e:
            print(f"⚠️  Erreur lors du chargement du cache: {e}")
    
    return False


def is_cache_valid():
    """
    Vérifie si le cache est encore valide
    """
    if cached_reviews is None or cache_timestamp is None:
        return False
    
    elapsed = datetime.now().timestamp() - cache_timestamp
    return elapsed < CACHE_DURATION


def update_reviews_background():
    """
    Met à jour les critiques en arrière-plan
    """
    global cached_reviews, cache_timestamp
    
    print("🔄 Mise à jour des critiques en arrière-plan...")
    try:
        reviews_data = scrape_reviews(max_pages=10)
        cached_reviews = reviews_data
        cache_timestamp = datetime.now().timestamp()
        
        # Sauvegarder dans le fichier JSON
        with open('senscritique_reviews.json', 'w', encoding='utf-8') as f:
            json.dump(reviews_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Cache mis à jour: {reviews_data['total_reviews']} critiques")
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")


@app.route('/api/critiques', methods=['GET'])
def get_reviews():
    """
    Endpoint pour récupérer les critiques
    """
    global cached_reviews, cache_timestamp
    
    # Si le cache n'est pas valide, le mettre à jour
    if not is_cache_valid():
        # Si on n'a pas de cache, charger depuis le fichier ou scraper
        if cached_reviews is None:
            if not load_cached_reviews():
                # Pas de cache, scraper maintenant (peut être lent)
                print("⚠️  Pas de cache, scraping en cours...")
                try:
                    reviews_data = scrape_reviews(max_pages=10)
                    cached_reviews = reviews_data
                    cache_timestamp = datetime.now().timestamp()
                except Exception as e:
                    return jsonify({
                        'error': 'Erreur lors du scraping',
                        'message': str(e)
                    }), 500
        else:
            # Cache expiré, mettre à jour en arrière-plan
            thread = threading.Thread(target=update_reviews_background)
            thread.daemon = True
            thread.start()
    
    if cached_reviews is None:
        return jsonify({
            'error': 'Aucune donnée disponible'
        }), 503
    
    return jsonify(cached_reviews)


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint de santé pour vérifier que l'API fonctionne
    """
    return jsonify({
        'status': 'ok',
        'cache_valid': is_cache_valid(),
        'total_reviews': cached_reviews['total_reviews'] if cached_reviews else 0
    })


@app.route('/', methods=['GET'])
def index():
    """
    Page d'accueil de l'API
    """
    return jsonify({
        'message': 'API SensCritique',
        'endpoints': {
            '/api/critiques': 'GET - Récupère toutes les critiques',
            '/api/health': 'GET - Vérifie l\'état de l\'API'
        }
    })


if __name__ == '__main__':
    # Charger le cache au démarrage
    load_cached_reviews()
    
    # Port depuis la variable d'environnement ou 5000 par défaut
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 API SensCritique démarrée sur le port {port}")
    print(f"📡 Endpoint: http://localhost:{port}/api/critiques")
    
    app.run(host='0.0.0.0', port=port, debug=False)

