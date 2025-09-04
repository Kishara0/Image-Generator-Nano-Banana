# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import mimetypes
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to: {file_name}")


def generate():
    # Load environment variables from .env file
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Make sure your .env file is in the same directory as this script and contains:")
        print("GEMINI_API_KEY=your_actual_api_key_here")
        return

    client = genai.Client(api_key=api_key)

    model = "gemini-2.0-flash-exp"  # Updated to a more stable model
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Generate an image of: The majestic
 creature stood
 tall against
 the backdrop of the
 setting sun, its
 fur a brilliant
 crimson"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_modalities=[
            "IMAGE",
            "TEXT",
        ],
    )

    try:
        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                file_name = f"majestic_creature_{file_index}"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                save_binary_file(f"{file_name}{file_extension}", data_buffer)
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    print(chunk.text)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure your API key is valid and you have access to the Gemini API.")


if __name__ == "_main_":
    generate()