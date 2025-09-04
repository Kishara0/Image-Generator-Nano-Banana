from PIL import Image
import os
import uuid

class ImageService:
    def __init__(self, upload_folder, generated_folder):
        self.upload_folder = upload_folder
        self.generated_folder = generated_folder
    
    def save_uploaded_image(self, file):
        """Save uploaded image and return file path"""
        if file and self._allowed_file(file.filename):
            filename = f"upload_{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(self.upload_folder, filename)
            file.save(file_path)
            return file_path
        return None
    
    def resize_for_social_media(self, image_path, platform="instagram"):
        """Resize image for specific social media platform"""
        sizes = {
            "instagram": (1080, 1080),
            "facebook": (1200, 630),
            "twitter": (1200, 675),
            "linkedin": (1200, 627)
        }
        
        size = sizes.get(platform, (1080, 1080))
        
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create new image with exact dimensions and paste centered
            new_img = Image.new('RGB', size, (255, 255, 255))
            paste_x = (size[0] - img.width) // 2
            paste_y = (size[1] - img.height) // 2
            new_img.paste(img, (paste_x, paste_y))
            
            # Save resized image
            filename = f"resized_{uuid.uuid4()}.jpg"
            output_path = os.path.join(self.generated_folder, filename)
            new_img.save(output_path, 'JPEG', quality=90)
            
            return output_path
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions