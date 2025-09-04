from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes.image_routes import image_bp
from routes.caption_routes import caption_bp
import logging

# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
app.config['UPLOAD_FOLDER'] = os.path.normpath(os.environ.get('UPLOAD_FOLDER', 'uploads'))
app.config['GENERATED_FOLDER'] = os.path.normpath(os.environ.get('GENERATED_FOLDER', 'generated'))

CORS(app)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(image_bp, url_prefix='/api/images')
app.register_blueprint(caption_bp, url_prefix='/api/captions')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Social Media Generator API is running'})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)