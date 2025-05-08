# Local News API

API for searching local news based on geolocation using Anthropic\'s Claude.

## Features

*   Fetches local news articles based on latitude and longitude.
*   Allows specifying search radius, maximum number of results, and time range for news.
*   Uses Anthropic\'s Claude model with web search capabilities to find relevant news.
*   Provides geocoding to determine location details (city, region, country) from coordinates.
*   Returns structured news data including title, content snippet, source, URL, publication date, and citations.

## API Endpoint

### `POST /search-news`

Searches for local news articles.

**Request Body:** (`application/json`)

```json
{
  "latitude": 11.7463,
  "longitude": 79.7644,
  "radius": 20,         // Search radius in kilometers (float, >0, <=100)
  "max_results": 5,   // Optional: Max number of articles (int, >=1, <=20, default: 5)
  "time_range": "7d"  // Optional: Time range (str, "24h", "48h", "7d", default: "24h")
}
```

**Response Body:** (`application/json`)

```json
{
  "articles": [
    {
      "title": "Example News Title",
      "content": "Snippet of the news article content...",
      "source": "example.com",
      "url": "https://example.com/news-article",
      "published_date": "2024-07-30T12:00:00Z", // ISO 8601 datetime string
      "location": { /* Original location_info used for search */ },
      "relevance_score": 0.85,
      "citations": [
        {
          "url": "https://example.com/source-citation",
          "title": "Source Citation Title",
          "cited_text": "Text cited from the source..."
        }
      ]
    }
  ],
  "metadata": {
    "total_results": 1,
    "search_radius": "20.0km",
    "time_range": "7d",
    "location": {
      "type": "approximate",
      "city": "Puduppalayam",
      "region": "Tamil Nadu",
      "country_code": "IN",
      "country": "India",
      "timezone": "UTC",
      "raw_address": "Pudupalayam, Puduppalayam, Cuddalore, Tamil Nadu, 607001, India"
    }
  },
  "search_info": {
    "timestamp": 1690723200.123456,
    "coordinates": {
      "latitude": 11.7463,
      "longitude": 79.7644
    },
    "model_used": "claude-3-5-sonnet-latest"
  }
}
```

### `GET /health`
Provides a simple health check for the API.
**Response Body:** (`application/json`)
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Setup and Installation

1.  **Clone the repository (if applicable):**
    ```bash
    # If you are cloning for the first time
    # git clone <repository-url>
    # cd LocalNews_Anthropic
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *On Windows, use `venv\\Scripts\\activate`*

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root directory and add your Anthropic API key:
    ```env
    ANTHROPIC_API_KEY="your_anthropic_api_key_here"
    ```

## Running the Application

To start the FastAPI application, run the following command from the project root directory:

```bash
uvicorn app.main:app --reload --port 8001
```

The API will be accessible at `http://127.0.0.1:8001`. You can view the auto-generated OpenAPI documentation at `http://127.0.0.1:8001/docs`.

## Project Structure
```
LocalNews_Anthropic/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application, endpoints
│   │   ├── __init__.py
│   │   ├── request.py   # Pydantic models for request bodies
│   │   └── response.py  # Pydantic models for response bodies
│   └── services/
│       ├── __init__.py
│       ├── anthropic.py # Service for interacting with Anthropic API
│       └── geocoding.py # Service for geocoding coordinates
├── venv/                # Virtual environment directory
├── .env                 # Environment variables (ANTHROPIC_API_KEY)
├── requirements.txt     # Python package dependencies
└── README.md            # This file
```

## Example Usage (cURL)

```bash
curl -X POST "http://127.0.0.1:8001/search-news" \
     -H "Content-Type: application/json" \
     -d \'{
           "latitude": 11.7463,
           "longitude": 79.7644,
           "radius": 20,
           "max_results": 2,
           "time_range": "7d"
         }\'
```

This command queries the API for news around the coordinates (11.7463, 79.7644) within a 20km radius, requesting a maximum of 2 articles from the last 7 days.

---
*This README was partially generated with AI assistance.* 