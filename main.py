import argparse
import logging
import os
import uvicorn
from pathlib import Path

from src.config import API_HOST, API_PORT
from src.storage.models import init_db
from src.crawler.firecrawl_service import FirecrawlService
from src.crawler.link_processor import LinkProcessor
from src.ai.openai_service import OpenAIService
from src.storage.repository import LinkRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure necessary directories exist"""
    Path('logs').mkdir(exist_ok=True)


def crawl_website(url: str, limit: int = 10):
    """
    Crawl a website and store high-value links
    
    Args:
        url: URL to crawl
        limit: Maximum number of pages to crawl
    """
    logger.info(f"Starting crawl for {url} with limit {limit}")
    
    # Initialize services
    crawler = FirecrawlService()
    processor = LinkProcessor()
    ai_service = OpenAIService()
    repo = LinkRepository()
    
    try:
        # Get or create website record
        website = repo.get_or_create_website(url)
        
        # Crawl website
        pages = crawler.crawl_website(url, limit=limit)
        
        if not pages:
            logger.warning(f"No pages crawled for URL: {url}")
            return
        
        logger.info(f"Crawled {len(pages)} pages")
        
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
                                   'source_url': url,
                                   'page_title': page.get('metadata', {}).get('title', '')}]
                links.extend(extracted_links)
            
            # Process links
            processed_links = processor.process_links(links, url)
            all_links.extend(processed_links)
            
        logger.info(f"Extracted {len(all_links)} links")
        
        # Analyze links with OpenAI
        enriched_links = ai_service.batch_analyze_links(all_links)
        
        # Store links in database
        stored_links = repo.add_links(enriched_links, website)
        
        logger.info(f"Stored {len(stored_links)} links in database")
        
        # Show top 5 high-value links
        top_links = repo.get_links_by_relevance(min_relevance=0.7, limit=5)
        
        if top_links:
            logger.info("Top high-value links:")
            for link in top_links:
                logger.info(f"  - {link.url} (Relevance: {link.overall_relevance}, Category: {link.primary_category})")
        else:
            logger.info("No high-value links found")
    
    except Exception as e:
        logger.error(f"Error during crawl: {str(e)}")
    finally:
        repo.close()


def start_api():
    """Start the FastAPI server"""
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    uvicorn.run(
        "src.api.app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )


if __name__ == "__main__":
    # Ensure directories exist
    ensure_directories()
    
    # Initialize database
    init_db()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="High-Value Link Scraper")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start API server")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website")
    crawl_parser.add_argument("url", help="URL to crawl")
    crawl_parser.add_argument("--limit", type=int, default=10, help="Maximum number of pages to crawl")
    
    args = parser.parse_args()
    
    if args.command == "api":
        start_api()
    elif args.command == "crawl":
        crawl_website(args.url, args.limit)
    else:
        parser.print_help()