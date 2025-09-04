from flask import Blueprint, request, jsonify, current_app, send_from_directory, url_for
from services.gemini_service import GeminiService
from services.image_service import ImageService
import os

image_bp = Blueprint('images', __name__)

# ---------- Helpers ----------

def _public_path(path: str) -> str:
    """Convert OS path to forward-slash path for client friendliness."""
    return path.replace("\\", "/")

def _download_url(folder: str, filename: str) -> str:
    """Return a stable, relative download URL the frontend can prepend with base."""
    return url_for('images.download_image_v2', folder=folder, filename=filename, _external=False)

def _safe_norm(filename: str) -> str:
    safe = os.path.normpath(filename)
    # block absolute or traversal
    if os.path.isabs(safe) or '..' in safe.split(os.sep):
        raise ValueError("Invalid filename")
    return safe

# ---------- Routes ----------

@image_bp.route('/generate', methods=['POST'])
def generate_image():
    """Generate image from text prompt."""
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt')
        style = data.get('style', 'realistic')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        gemini_service = GeminiService()
        image_path = gemini_service.generate_image_from_text(prompt, style)

        if not image_path:
            return jsonify({'error': 'Failed to generate image'}), 500

        public_path = _public_path(image_path)
        public_name = os.path.basename(image_path)
        download_url = _download_url('generated', public_name)

        return jsonify({
            'success': True,
            'image_path': public_path,
            'download_url': download_url,
            'message': 'Image generated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@image_bp.route('/upload', methods=['POST'])
def upload_image():
    """Upload and save image."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        image_service = ImageService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['GENERATED_FOLDER']
        )

        file_path = image_service.save_uploaded_image(file)
        if not file_path:
            return jsonify({'error': 'Failed to upload image'}), 500

        public_path = _public_path(file_path)
        public_name = os.path.basename(file_path)
        download_url = _download_url('uploads', public_name)

        return jsonify({
            'success': True,
            'image_path': public_path,
            'download_url': download_url,
            'message': 'Image uploaded successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@image_bp.route('/edit', methods=['POST'])
def edit_image():
    """Edit existing image."""
    try:
        data = request.get_json() or {}
        image_path = data.get('image_path')
        edit_prompt = data.get('edit_prompt')

        if not image_path or not edit_prompt:
            return jsonify({'error': 'Image path and edit prompt are required'}), 400

        # support forward/back slashes in incoming path
        normalized = image_path.replace('/', os.sep).replace('\\', os.sep)
        if not os.path.exists(normalized):
            return jsonify({'error': 'Image file not found'}), 404

        gemini_service = GeminiService()
        edited_image_path = gemini_service.edit_image(normalized, edit_prompt)

        if not edited_image_path:
            return jsonify({'error': 'Failed to edit image'}), 500

        public_path = _public_path(edited_image_path)
        public_name = os.path.basename(edited_image_path)
        download_url = _download_url('generated', public_name)

        return jsonify({
            'success': True,
            'image_path': public_path,
            'download_url': download_url,
            'message': 'Image edited successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@image_bp.route('/resize', methods=['POST'])
def resize_image():
    """Resize image for a social media platform."""
    try:
        data = request.get_json() or {}
        image_path = data.get('image_path')
        platform = data.get('platform', 'instagram')

        if not image_path:
            return jsonify({'error': 'Image path is required'}), 400

        normalized = image_path.replace('/', os.sep).replace('\\', os.sep)
        if not os.path.exists(normalized):
            return jsonify({'error': 'Image file not found'}), 404

        image_service = ImageService(
            current_app.config['UPLOAD_FOLDER'],
            current_app.config['GENERATED_FOLDER']
        )

        resized_image_path = image_service.resize_for_social_media(normalized, platform)

        public_path = _public_path(resized_image_path)
        public_name = os.path.basename(resized_image_path)
        download_url = _download_url('generated', public_name)

        return jsonify({
            'success': True,
            'image_path': public_path,
            'download_url': download_url,
            'message': f'Image resized for {platform}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----- Download Endpoints -----

@image_bp.route('/download/<folder>/<path:filename>')
def download_image_v2(folder, filename):
    """Stable download endpoint: /api/images/download/<uploads|generated>/<filename>"""
    try:
        if folder not in ('uploads', 'generated'):
            return jsonify({'error': 'Invalid folder'}), 400

        safe_name = _safe_norm(filename)
        base_dir = (current_app.config['UPLOAD_FOLDER']
                    if folder == 'uploads'
                    else current_app.config['GENERATED_FOLDER'])

        abs_path = os.path.join(base_dir, safe_name)
        if not os.path.exists(abs_path):
            return jsonify({'error': 'File not found'}), 404

        return send_from_directory(base_dir, safe_name)
    except ValueError:
        return jsonify({'error': 'Invalid filename'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@image_bp.route('/download/<path:filename>')
def download_image_legacy(filename):
    """
    Legacy compatibility:
    Accepts 'generated\\file.jpg', 'generated/file.jpg', or just 'file.jpg'.
    Redirects internally to v2 when possible, else searches by basename.
    """
    normalized = filename.replace('\\', '/')
    parts = normalized.split('/')

    # If looks like "<folder>/<file>"
    if len(parts) == 2 and parts[0] in ('uploads', 'generated'):
        return download_image_v2(parts[0], parts[1])

    just_name = os.path.basename(filename)
    for folder, base in (('uploads', current_app.config['UPLOAD_FOLDER']),
                         ('generated', current_app.config['GENERATED_FOLDER'])):
        candidate = os.path.join(base, just_name)
        if os.path.exists(candidate):
            return send_from_directory(base, just_name)

    return jsonify({'error': 'File not found'}), 404
