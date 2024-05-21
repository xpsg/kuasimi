import os
import time
import threading
import subprocess
from rich.console import Console
import google.generativeai as genai
import argparse
import sys
from PIL import Image
import io
import tempfile
import asyncio

# --- Global Variables ---
api_response_text = ""
console = Console()

# Set your Gemini API key from the environment variable.
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# --- Default Prompt ---
DEFAULT_PROMPT = """
Kuasimi is an advanced visual assistant designed to analyze and understand the content of input images, which are likely to be screenshots. Its primary goal is to provide users with concise, contextual answers based on the information detected within the image.
When a user submits an image, Kuasimi employs sophisticated computer vision and image recognition techniques to examine the image thoroughly. It identifies and extracts key elements, such as text, objects, symbols, and any other relevant visual components that contribute to the overall context of the image.
Kuasimi processes the extracted information to determine the most relevant and meaningful aspects in relation to the user's intended query. This involves analyzing the relationships between the identified elements and understanding the context in which they appear within the image.
Based on its understanding of the image's content and context, Kuasimi formulates a concise response that directly addresses the user's needs. The response is tailored to provide the most pertinent information while maintaining clarity and brevity. Kuasimi's replies focus on delivering essential insights without unnecessary elaboration, ensuring that users can quickly obtain the information they seek.
The generated response is presented in a clear and easily understandable format, taking into consideration the user's presumed level of knowledge and the complexity of the image's content. Kuasimi strives to provide accurate and helpful information, enabling users to gain valuable insights from the input image efficiently.
Throughout its interactions, Kuasimi prioritizes delivering concise and relevant answers, making it an ideal tool for users who require quick and accurate information based on visual input.
"""

# --- Model ---
MODEL_NAME="gemini-1.5-flash-latest"
#MODEL_NAME="gemini-1.5-pro-latest"

# --- Gemini API Functions ---
async def call_gemini_api(image_data, prompt=DEFAULT_PROMPT):
    """Calls the Gemini Flash API asynchronously, streaming the response."""
    global api_response_text

    model = genai.GenerativeModel(
        model_name=MODEL_NAME
    )

    img = Image.open(io.BytesIO(image_data))
    api_response_text = ""

    try:
        async for chunk in await model.generate_content_async([prompt, img], stream=True, safety_settings={
            'HATE': 'BLOCK_NONE',
            'HARASSMENT': 'BLOCK_NONE',
            'SEXUAL' : 'BLOCK_NONE',
            'DANGEROUS' : 'BLOCK_NONE'
        }):
            api_response_text += chunk.text
            update_notification(api_response_text)
    except Exception as e:
        api_response_text = f"Error: {e}"
        update_notification(api_response_text)

def update_notification(text):
    """Updates the dunstify notification with the given text."""
    global thumbnail_path

    subprocess.run(
        ["dunstify", "-r", "222222", "-a", "Kua Simi?", "-i", thumbnail_path, "-t", "10000", "Kua Simi?",  text],
        check=True
    )

# --- Image Handling and Thumbnail Creation ---
def create_thumbnail(image_path):
    """Creates a thumbnail from the provided image and saves it."""
    with Image.open(image_path) as img:
        img.thumbnail((128, 128))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as thumb_file:
            img.save(thumb_file.name, format="PNG")
            return thumb_file.name

# --- Main Application Logic ---
def main():
    global thumbnail_path

    parser = argparse.ArgumentParser(description="Kua Simi?")
    parser.add_argument(
        "-f", "--file", help="Path to the image file", required=True
    )
    parser.add_argument(
        "-p",
        "--prompt",
        help="Prompt string for the API call (overrides the default)",
        default=DEFAULT_PROMPT
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: Image file not found: {args.file}")
        sys.exit(1)

    thumbnail_path = create_thumbnail(args.file)

    with open(args.file, "rb") as f:
        image_data = f.read()

    # --- Start API call in a separate thread ---
    threading.Thread(target=lambda: asyncio.run(call_gemini_api(image_data, args.prompt))).start()

if __name__ == "__main__":
    main()
