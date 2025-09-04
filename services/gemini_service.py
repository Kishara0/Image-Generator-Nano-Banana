import base64
import mimetypes
import os
import uuid
from google import genai
from google.genai import types


class GeminiService:
    """
    Image generation/editing uses an image-capable model.
    Captioning uses a multimodal text+vision model.
    """
    def __init__(self):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.image_model = "gemini-2.5-flash-image-preview"  # for image gen & edit
        self.caption_model = "gemini-1.5-flash"              # for captioning (text+vision)

    def generate_image_from_text(self, prompt, style="realistic"):
        """Generate image from text prompt."""
        enhanced_prompt = (
            f"Create a high-quality {style} image for social media: {prompt}. "
            "Make it visually appealing, well-composed, and suitable for social media platforms."
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=enhanced_prompt)],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        os.makedirs("generated", exist_ok=True)

        generated_files = []
        file_index = 0

        for chunk in self.client.models.generate_content_stream(
            model=self.image_model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                not chunk.candidates
                or not chunk.candidates[0].content
                or not chunk.candidates[0].content.parts
            ):
                continue

            part = chunk.candidates[0].content.parts[0]
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                file_name = f"generated_{uuid.uuid4()}_{file_index}"
                file_index += 1
                inline_data = part.inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"

                file_path = os.path.join("generated", f"{file_name}{file_extension}")
                self._save_binary_file(file_path, data_buffer)
                generated_files.append(file_path)

        return generated_files[0] if generated_files else None

    def edit_image(self, image_path, edit_prompt):
        """Edit existing image based on prompt."""
        # normalize path
        image_path = image_path.replace("/", os.sep).replace("\\", os.sep)

        with open(image_path, "rb") as f:
            image_data = f.read()

        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=f"Edit this image: {edit_prompt}. Maintain social media quality and appeal."
                    ),
                    types.Part.from_bytes(data=image_data, mime_type=mime_type),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        )

        os.makedirs("generated", exist_ok=True)

        generated_files = []
        file_index = 0

        for chunk in self.client.models.generate_content_stream(
            model=self.image_model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                not chunk.candidates
                or not chunk.candidates[0].content
                or not chunk.candidates[0].content.parts
            ):
                continue

            part = chunk.candidates[0].content.parts[0]
            if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                file_name = f"edited_{uuid.uuid4()}_{file_index}"
                file_index += 1
                inline_data = part.inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type) or ".png"

                file_path = os.path.join("generated", f"{file_name}{file_extension}")
                self._save_binary_file(file_path, data_buffer)
                generated_files.append(file_path)

        return generated_files[0] if generated_files else None

    def generate_caption(self, image_path, platform="general", tone="engaging"):
        """Generate a caption for an image using a text+vision model."""
        image_path = image_path.replace("/", os.sep).replace("\\", os.sep)

        with open(image_path, "rb") as f:
            image_data = f.read()

        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

        prompt = (
            f"Analyze this image and write an {tone} caption optimized for {platform}.\n"
            "- 1–2 short sentences max.\n"
            "- Include 3–5 relevant hashtags at the end.\n"
            "- Encourage engagement without sounding spammy.\n"
            "Only return the caption text."
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                    types.Part.from_bytes(data=image_data, mime_type=mime_type),
                ],
            ),
        ]

        resp = self.client.models.generate_content(
            model=self.caption_model,
            contents=contents,
        )

        # Robustly extract text
        text = getattr(resp, "text", None)
        if not text:
            chunks = []
            for cand in (resp.candidates or []):
                if cand.content and cand.content.parts:
                    for p in cand.content.parts:
                        if hasattr(p, "text") and p.text:
                            chunks.append(p.text)
            text = "".join(chunks).strip()

        return text or "Captured the moment beautifully. ✨ #photography #aesthetics #moments #inspo"

    def _save_binary_file(self, file_path, data):
        with open(file_path, "wb") as f:
            f.write(data)
        print(f"File saved to: {file_path}")
