from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class LinkFilter(BaseModel):
    """Model for filtering links"""
    min_relevance: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Minimum relevance score")
    category: Optional[str] = Field(None, description="Link category")
    is_document: Optional[bool] = Field(None, description="Filter document links")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of links to return")


class LinkResponse(BaseModel):
    """Model for link response"""
    id: int
    url: str
    source_url: Optional[str] = None
    page_title: Optional[str] = None
    is_document: bool
    contact_relevance: float
    financial_relevance: float
    official_relevance: float
    overall_relevance: float
    primary_category: str
    rationale: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class CrawlRequest(BaseModel):
    """Model for crawl request"""
    url: HttpUrl
    limit: int = Field(50, ge=1, le=500, description="Maximum number of pages to crawl")


class CrawlResponse(BaseModel):
    """Model for crawl response"""
    success: bool
    message: str
    website_id: int
    links_found: int