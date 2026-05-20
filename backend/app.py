from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Basic hello-world route
@app.route('/', methods=['GET'])
def hello_world():
    return jsonify({
        "message": "Hello from OmniNews CMS Backend!",
        "status": "success"
    }), 200

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "omninews-cms-backend"
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, port=port)
