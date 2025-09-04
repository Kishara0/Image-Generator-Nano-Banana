from flask import Blueprint, request, jsonify
from services.gemini_service import GeminiService
from PIL import Image
import os
import logging

caption_bp = Blueprint('captions', __name__)

@caption_bp.route('/generate', methods=['POST'])
def generate_caption():
    """Generate caption for image"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        platform = data.get('platform', 'general')
        tone = data.get('tone', 'engaging')
        
        if not image_path:
            return jsonify({'error': 'Image path is required'}), 400
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Validate image
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as img_err:
            logging.error(f"Invalid image {image_path}: {str(img_err)}")
            return jsonify({'error': f'Invalid image: {str(img_err)}'}), 400
        
        gemini_service = GeminiService()
        caption = gemini_service.generate_caption(image_path, platform, tone)
        
        return jsonify({
            'success': True,
            'caption': caption,
            'message': 'Caption generated successfully'
        })
        
    except Exception as e:
        logging.error(f"Error generating caption for {image_path}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@caption_bp.route('/regenerate', methods=['POST'])
def regenerate_caption():
    """Regenerate caption with different parameters"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        platform = data.get('platform', 'general')
        tone = data.get('tone', 'engaging')
        custom_prompt = data.get('custom_prompt', '')
        
        if not image_path:
            return jsonify({'error': 'Image path is required'}), 400
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Validate image
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as img_err:
            logging.error(f"Invalid image {image_path}: {str(img_err)}")
            return jsonify({'error': f'Invalid image: {str(img_err)}'}), 400
        
        gemini_service = GeminiService()
        
        # Use custom prompt if provided
        if custom_prompt:
            caption = gemini_service.generate_caption(image_path, platform, custom_prompt)
        else:
            caption = gemini_service.generate_caption(image_path, platform, tone)
        
        return jsonify({
            'success': True,
            'caption': caption,
            'message': 'Caption regenerated successfully'
        })
        
    except Exception as e:
        logging.error(f"Error regenerating caption for {image_path}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500