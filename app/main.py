import base64
import os
import asyncio
import aiohttp
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from databases import Database
from dotenv import load_dotenv
import asyncpg
from PIL import Image
import io
import openai
from google_images_search import GoogleImagesSearch

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
database = Database(DATABASE_URL)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Google Images Search
gis = GoogleImagesSearch(os.getenv('GOOGLE_API_KEY'), os.getenv('GOOGLE_CX'))


# Database initialization
async def init_db():
    try:
        await database.connect()
        # Create tables if they don't exist
        query = """
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            original_filename TEXT,
            keywords JSONB,
            similar_images JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await database.execute(query)
    except Exception as e:
        print(f"Database initialization error: {e}")


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


async def extract_keywords(image_data):
    """Extract keywords from image using OpenAI's GPT-4 Vision"""
    try:
        response = await openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in keywords"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        keywords = response.choices[0].message.content.split(',')
        return [keyword.strip() for keyword in keywords]
    except Exception as e:
        print(f"Keyword extraction error: {e}")
        return []


async def search_similar_images(keywords, max_results=5):
    """Search for similar images using Google Images Search"""
    try:
        search_params = {
            'q': ' '.join(keywords[:3]),  # Use top 3 keywords
            'num': max_results,
            'fileType': 'jpg|png',
            'rights': 'cc_publicdomain|cc_attribute|cc_sharealike'
        }

        gis.search(search_params)
        similar_images = []

        for image in gis.results():
            similar_images.append({
                'url': image.url,
                'thumbnail': image.thumbnail,
                'width': image.width,
                'height': image.height
            })

        return similar_images
    except Exception as e:
        print(f"Image search error: {e}")
        return []


async def download_and_store_image(url):
    """Download image and extract metadata"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                img = Image.open(io.BytesIO(image_data))
                return {
                    'dimensions': f"{img.width}x{img.height}",
                    'format': img.format,
                    'size': len(image_data),
                    'url': url
                }
    return None


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """Handle image upload and processing"""
    try:
        # Read and process the uploaded image
        contents = await file.read()
        image_data = base64.b64encode(contents).decode()

        # Extract keywords
        keywords = await extract_keywords(image_data)

        # Search for similar images
        similar_images = await search_similar_images(keywords)

        # Download and process similar images
        metadata = []
        for image in similar_images:
            image_metadata = await download_and_store_image(image['url'])
            if image_metadata:
                metadata.append(image_metadata)

        # Store in database
        query = """
        INSERT INTO images (original_filename, keywords, similar_images, metadata)
        VALUES (:filename, :keywords, :similar_images, :metadata)
        RETURNING id
        """
        values = {
            'filename': file.filename,
            'keywords': json.dumps(keywords),
            'similar_images': json.dumps(similar_images),
            'metadata': json.dumps(metadata)
        }

        id = await database.execute(query, values)

        return {
            'id': id,
            'keywords': keywords,
            'similar_images': similar_images,
            'metadata': metadata
        }

    except Exception as e:
        return {'error': str(e)}


@app.get("/images/{image_id}")
async def get_image(image_id: int):
    """Retrieve image data from database"""
    query = "SELECT * FROM images WHERE id = :id"
    result = await database.fetch_one(query, {'id': image_id})

    if result:
        return {
            'id': result['id'],
            'keywords': json.loads(result['keywords']),
            'similar_images': json.loads(result['similar_images']),
            'metadata': json.loads(result['metadata']),
            'created_at': result['created_at']
        }
    return {'error': 'Image not found'}


# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")