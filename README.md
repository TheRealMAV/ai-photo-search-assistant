# AI-Powered Photo Search Assistant

This application processes uploaded images using AI to extract keywords and find similar images. It features a modern web interface, asynchronous processing, and PostgreSQL storage.

## Features

- Image upload and processing
- AI-powered keyword extraction using GPT-4 Vision
- Similar image search using Google Images
- Real-time progress tracking
- PostgreSQL storage with JSONB support
- Docker containerization

## Prerequisites

- Docker and Docker Compose
- Google Cloud API key and Custom Search Engine ID
- OpenAI API key

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/TheRealMAV/ai-photo-search-assistant.git
cd ai-photo-search-assistant
```

2. Create a `.env` file in the project root with the following variables:
```
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=photo_search
DB_HOST=db
DB_PORT=5432
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX=your_google_custom_search_id
```

3. Build and start the containers:
```bash
docker-compose up --build
```

4. Access the application at `http://localhost:8000`

## Project Structure

```
.
├── app/
│   └── main.py
├── static/
│   └── index.html
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check logs: `docker-compose logs db`
- Verify database credentials in `.env`

### Image Processing Errors
- Confirm OpenAI API key is valid
- Check image format support (JPEG, PNG supported)
- Verify Google API credentials

## API Endpoints

- `POST /upload/`: Upload and process new images
- `GET /images/{image_id}`: Retrieve processed image data

## License

This project is licensed under the MIT License - see the LICENSE file for details.