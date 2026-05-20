from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import json
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
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

# Initialize Groq client (OpenAI-compatible)
def get_groq_client():
    return OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

# Liquid Content Generation Function
def generate_liquid_content(article_text):
    """
    Transform raw article text into structured "Liquid Content" using Groq AI.
    Returns a dictionary with executive_summary, timeline, and social_caption.
    """
    if not GROQ_API_KEY:
        return {
            "error": "GROQ_API_KEY not configured",
            "executive_summary": [],
            "timeline": [],
            "social_caption": ""
        }
    
    if not article_text or len(article_text.strip()) < 20:
        return {
            "error": "Article text too short or empty",
            "executive_summary": [],
            "timeline": [],
            "social_caption": ""
        }
    
    try:
        client = get_groq_client()
        
        system_prompt = """You are an expert news content transformer. Analyze the provided article and return ONLY a valid JSON object with these exact keys:
- executive_summary: Array of 3 bullet points summarizing the key points
- timeline: Array of 2-3 key events mentioned chronologically
- social_caption: A single sentence social media hook (engaging and punchy)

Return ONLY the JSON object, no markdown formatting, no code blocks, no additional text."""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Transform this article into liquid content:\n\n{article_text}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        liquid_content = json.loads(response_text)
        
        return liquid_content
    
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parsing failed: {str(e)}",
            "executive_summary": [],
            "timeline": [],
            "social_caption": "",
            "raw_response": response_text if 'response_text' in locals() else None
        }
    
    except Exception as e:
        return {
            "error": f"Failed to generate liquid content: {str(e)}",
            "executive_summary": [],
            "timeline": [],
            "social_caption": ""
        }


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

# News API route with Liquid Content enrichment
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Fetch top breaking news headlines from NewsAPI and enrich with AI-generated Liquid Content.
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
        for idx, article in enumerate(articles):
            article_data = {
                'id': len(processed_articles) + 1,
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'imageUrl': article.get('urlToImage', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'author': article.get('author', 'Unknown'),
                'publishedAt': article.get('publishedAt', ''),
                'content': article.get('content', '')
            }
            
            # Enrich top 3 articles with Liquid Content using Groq AI
            if idx < 3:
                article_text = f"{article_data['title']}\n\n{article_data['description']}\n\n{article_data['content']}"
                liquid_content = generate_liquid_content(article_text)
                article_data['liquid_content'] = liquid_content
            
            processed_articles.append(article_data)
        
        return jsonify({
            "status": "success",
            "message": f"Successfully fetched {len(processed_articles)} articles",
            "count": len(processed_articles),
            "country": country,
            "category": category if category else "general",
            "articles": processed_articles,
            "enriched_count": min(3, len(processed_articles))
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
