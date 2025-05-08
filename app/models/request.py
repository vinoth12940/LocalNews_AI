from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude of the location")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude of the location")
    radius: float = Field(..., gt=0, le=100, description="Search radius in kilometers")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of news results to return")
    time_range: Optional[str] = Field("24h", description="Time range for news (e.g., '24h', '48h', '7d')")

    @validator('time_range')
    def validate_time_range(cls, v):
        valid_ranges = ['24h', '48h', '7d']
        if v not in valid_ranges:
            raise ValueError(f'time_range must be one of {valid_ranges}')
        return v 