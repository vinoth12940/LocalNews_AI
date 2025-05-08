from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from dateutil import parser

class Citation(BaseModel):
    url: str = Field(..., description="URL of the cited source")
    title: str = Field(..., description="Title of the cited source")
    cited_text: str = Field(..., description="Cited text from the source")

class NewsArticle(BaseModel):
    title: str = Field(..., description="Title of the news article")
    content: str = Field(..., description="Content or summary of the news article")
    source: str = Field(..., description="Source of the news article")
    url: str = Field(..., description="URL of the news article")
    published_date: Optional[datetime] = Field(None, description="Publication date of the article")
    location: Dict = Field(..., description="Location information for the article")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score of the article to the search location")
    citations: List[Citation] = Field(default_factory=list, description="Citations from the article")

    @field_validator('published_date', mode='before')
    @classmethod
    def parse_published_date(cls, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        
        if isinstance(value, str):
            try:
                if "days ago" in value.lower():
                    days = int(value.lower().split(" ")[0])
                    return datetime.now(timezone.utc) - timedelta(days=days)
                if "hours ago" in value.lower():
                    hours = int(value.lower().split(" ")[0])
                    return datetime.now(timezone.utc) - timedelta(hours=hours)
                if "minutes ago" in value.lower():
                    minutes = int(value.lower().split(" ")[0])
                    return datetime.now(timezone.utc) - timedelta(minutes=minutes)
                if "yesterday" in value.lower():
                    return datetime.now(timezone.utc) - timedelta(days=1)

                parsed_date = parser.parse(value)
                if parsed_date.tzinfo is None or parsed_date.tzinfo.utcoffset(parsed_date) is None:
                    return parsed_date.replace(tzinfo=timezone.utc)
                return parsed_date
            except (ValueError, TypeError, OverflowError):
                return None
        return None

class SearchMetadata(BaseModel):
    total_results: int = Field(..., description="Total number of results found")
    search_radius: str = Field(..., description="Search radius used")
    time_range: str = Field(..., description="Time range used for search")
    location: Dict = Field(..., description="Location information used for search")

class SearchInfo(BaseModel):
    timestamp: float = Field(..., description="Timestamp of the search")
    coordinates: Dict[str, float] = Field(..., description="Search coordinates")
    model_used: str = Field("claude-3-5-haiku-latest", description="Model used for the search")

class NewsResponse(BaseModel):
    articles: List[NewsArticle] = Field(..., description="List of news articles")
    metadata: SearchMetadata = Field(..., description="Metadata about the search results")
    search_info: SearchInfo = Field(..., description="Information about the search performed") 