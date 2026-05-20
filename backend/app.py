from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS for React frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

# Basic hello-world route
@app.route('/', methods=['GET'])
def hello_world():
    return jsonify({
        "message": "Hello from OmniNews CMS Backend!",
        "status": "success",
        "version": "1.0"
    }), 200

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "omninews-cms-backend",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# News API route
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Fetch top breaking news headlines from NewsAPI.
    Optional query parameters:
    - country: Country code (default: 'us')
    - category: News category (e.g., 'business', 'technology', 'sports')
    - limit: Number of articles to return (default: 10, max: 100)
    """
    try:
        # Validate API key
        if not NEWS_API_KEY:
            return jsonify({
                "status": "error",
                "message": "NEWS_API_KEY environment variable is not set",
                "articles": []
            }), 400
        
        # Get query parameters
        country = request.args.get('country', 'us').lower()
        category = request.args.get('category', '')
        limit = request.args.get('limit', 10, type=int)
        
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 10
        
        # Build API request parameters
        params = {
            'country': country,
            'apiKey': NEWS_API_KEY,
            'pageSize': min(limit, 100)
        }
        
        # Add category if provided
        if category:
            params['category'] = category
        
        # Make request to NewsAPI
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if request was successful
        if data.get('status') != 'ok':
            return jsonify({
                "status": "error",
                "message": data.get('message', 'Failed to fetch news from NewsAPI'),
                "articles": []
            }), 502
        
        # Extract and limit articles
        articles = data.get('articles', [])[:limit]
        
        # Process articles to return cleaner data
        processed_articles = []
        for article in articles:
            processed_articles.append({
                'id': len(processed_articles) + 1,
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'imageUrl': article.get('urlToImage', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'author': article.get('author', 'Unknown'),
                'publishedAt': article.get('publishedAt', ''),
                'content': article.get('content', '')
            })
        
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {len(processed_articles)} articles",
            "count": len(processed_articles),
            "country": country,
            "category": category if category else "general",
            "articles": processed_articles
        }), 200
    
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Request to NewsAPI timed out. Please try again.",
            "articles": []
        }), 504
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch news: {str(e)}",
            "articles": []
        }), 502
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}",
            "articles": []
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
