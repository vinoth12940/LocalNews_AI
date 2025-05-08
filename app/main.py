from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .models.request import LocationRequest
from .models.response import NewsResponse, NewsArticle, SearchMetadata, SearchInfo, Citation
from .services.geocoding import GeocodingService
from .services.anthropic import AnthropicService
from typing import List
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local News API",
    description="API for searching local news based on geolocation using Anthropic's Claude",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
geocoding_service = GeocodingService()
anthropic_service = AnthropicService()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

@app.post("/search-news", response_model=NewsResponse)
async def search_local_news(request: LocationRequest):
    try:
        logger.info(f"Received search request for coordinates: {request.latitude}, {request.longitude}")
        
        # Get location information
        location_info = geocoding_service.get_location_info(
            request.latitude,
            request.longitude
        )
        logger.info(f"Location info retrieved: {location_info}")

        # Search for news
        news_results = anthropic_service.search_local_news(
            location_info=location_info,
            radius=request.radius,
            max_results=request.max_results,
            time_range=request.time_range
        )
        logger.info(f"Found {len(news_results)} news results")

        # Convert results to NewsArticle objects
        articles = []
        for result in news_results:
            try:
                citations = []
                for citation in result.get('citations', []):
                    citations.append(
                        Citation(
                            url=citation.get('url', ''),
                            title=citation.get('title', ''),
                            cited_text=citation.get('cited_text', '')
                        )
                    )
                
                article = NewsArticle(
                    title=result.get("title", "Untitled"),
                    content=result.get("content", ""),
                    source=result.get("source", ""),
                    url=result.get("url", ""),
                    published_date=result.get("published_date"),
                    location=result.get("location", location_info),
                    relevance_score=result.get("relevance_score", 0.5),
                    citations=citations
                )
                articles.append(article)
            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue

        # Prepare response
        response = NewsResponse(
            articles=articles,
            metadata=SearchMetadata(
                total_results=len(articles),
                search_radius=f"{request.radius}km",
                time_range=request.time_range,
                location=location_info
            ),
            search_info=SearchInfo(
                timestamp=time.time(),
                coordinates={
                    "latitude": request.latitude,
                    "longitude": request.longitude
                },
                model_used=anthropic_service.model
            )
        )

        logger.info("Successfully prepared response")
        return response

    except Exception as e:
        logger.error(f"Error in search_local_news: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for news: {str(e)}"
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"} 