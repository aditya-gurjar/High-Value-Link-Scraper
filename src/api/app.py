from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import logging

from src.api.models import LinkResponse, CrawlRequest, CrawlResponse, LinkFilter
from src.storage.repository import LinkRepository
from src.storage.models import init_db

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="High-Value Link Scraper API",
    description="API for accessing high-value links extracted from websites",
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

# Dependency to get repository
def get_repository():
    repo = LinkRepository()
    try:
        yield repo
    finally:
        repo.close()

@app.get("/links", response_model=List[LinkResponse], tags=["Links"])
async def get_links(
    min_relevance: Optional[float] = Query(0.0, ge=0.0, le=1.0),
    category: Optional[str] = None,
    is_document: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    repo: LinkRepository = Depends(get_repository)
):
    """
    Get links filtered by various criteria
    
    - **min_relevance**: Minimum relevance score (0.0 to 1.0)
    - **category**: Filter by category (contact, financial, official, other)
    - **is_document**: Filter document links
    - **limit**: Maximum number of links to return
    """
    try:
        if is_document:
            links = repo.get_document_links(limit=limit)
        elif category:
            links = repo.get_links_by_category(category=category, limit=limit)
        else:
            links = repo.get_links_by_relevance(min_relevance=min_relevance, limit=limit)
            
        # Additional filtering
        if is_document is not None and not is_document:
            links = [link for link in links if not link.is_document]
            
        return links
    except Exception as e:
        logger.error(f"Error retrieving links: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving links")


@app.get("/links/website/{website_id}", response_model=List[LinkResponse], tags=["Links"])
async def get_links_by_website(
    website_id: int,
    limit: int = Query(100, ge=1, le=1000),
    repo: LinkRepository = Depends(get_repository)
):
    """
    Get links for a specific website
    
    - **website_id**: ID of the website
    - **limit**: Maximum number of links to return
    """
    try:
        links = repo.get_links_by_website(website_id=website_id, limit=limit)
        return links
    except Exception as e:
        logger.error(f"Error retrieving links for website {website_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving links")


@app.post("/crawl", response_model=CrawlResponse, tags=["Crawling"])
async def crawl_website(
    request: CrawlRequest,
    repo: LinkRepository = Depends(get_repository)
):
    """
    Crawl a website and extract high-value links
    
    - **url**: URL to start crawling from
    - **limit**: Maximum number of pages to crawl
    """
    from src.crawler.firecrawl_service import FirecrawlService
    from src.crawler.link_processor import LinkProcessor
    from src.ai.openai_service import OpenAIService
    
    try:
        # Initialize services
        crawler = FirecrawlService()
        processor = LinkProcessor()
        ai_service = OpenAIService()
        
        # Get or create website record
        website = repo.get_or_create_website(request.url)
        
        # Crawl website
        pages = crawler.crawl_website(request.url, limit=request.limit)
        
        if not pages:
            logger.warning(f"No pages crawled for URL: {request.url}")
            return CrawlResponse(
                success=False,
                message="No pages crawled",
                website_id=website.id,
                links_found=0
            )
        
        # Process links from crawled pages
        all_links = []
        for page in pages:
            # Each page has markdown, html, and metadata
            # Extract links from the HTML content or use the metadata
            links = []
            
            # Firecrawl may already extract links for us
            if 'links' in page:
                links = [{'url': link, 'source_url': page.get('metadata', {}).get('sourceURL', ''), 
                          'page_title': page.get('metadata', {}).get('title', '')} 
                         for link in page.get('links', []) if link]
            else:
                # Extract links from page metadata
                extracted_links = [{'url': page.get('metadata', {}).get('sourceURL', ''),
                                  'source_url': request.url,
                                  'page_title': page.get('metadata', {}).get('title', '')}]
                links.extend(extracted_links)
            
            # Process links
            processed_links = processor.process_links(links, request.url)
            all_links.extend(processed_links)
        
        # Analyze links with OpenAI
        enriched_links = ai_service.batch_analyze_links(all_links)
        
        # Store links in database
        stored_links = repo.add_links(enriched_links, website)
        
        return CrawlResponse(
            success=True,
            message=f"Successfully crawled {len(pages)} pages and found {len(stored_links)} links",
            website_id=website.id,
            links_found=len(stored_links)
        )
    except Exception as e:
        logger.error(f"Error crawling website {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crawling website: {str(e)}")


@app.get("/websites", tags=["Websites"])
async def get_websites(
    repo: LinkRepository = Depends(get_repository)
):
    """
    Get all websites that have been crawled
    """
    try:
        websites = repo.get_all_websites()
        return websites
    except Exception as e:
        logger.error(f"Error retrieving websites: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving websites")


@app.get("/links/search", response_model=List[LinkResponse], tags=["Links"])
async def search_links(
    query: str,
    limit: int = Query(100, ge=1, le=1000),
    repo: LinkRepository = Depends(get_repository)
):
    """
    Search links by URL or page title
    
    - **query**: Search query
    - **limit**: Maximum number of links to return
    """
    try:
        links = repo.search_links(query=query, limit=limit)
        return links
    except Exception as e:
        logger.error(f"Error searching links: {str(e)}")
        raise HTTPException(status_code=500, detail="Error searching links")


@app.get("/stats", tags=["Statistics"])
async def get_stats(
    repo: LinkRepository = Depends(get_repository)
):
    """
    Get statistics about crawled websites and links
    """
    try:
        # Get counts
        website_count = repo.get_website_count()
        link_count = repo.get_link_count()
        document_count = repo.get_document_count()
        
        # Get category counts
        category_counts = repo.get_category_counts()
        
        return {
            "website_count": website_count,
            "link_count": link_count,
            "document_count": document_count,
            "category_counts": category_counts
        }
    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving stats")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}