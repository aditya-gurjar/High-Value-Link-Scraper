import logging
from typing import Dict, List, Any
import time

from firecrawl import FirecrawlApp
from src.config import FIRECRAWL_API_KEY, FORMATS, CRAWL_LIMIT

logger = logging.getLogger(__name__)

class FirecrawlService:
    """Service for interacting with FireCrawl API"""

    def __init__(self, api_key: str = FIRECRAWL_API_KEY):
        """Initialize FireCrawl SDK client"""
        self.app = FirecrawlApp(api_key=api_key)
        logger.info("FireCrawl service initialized")

    def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single URL
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing scraped data
        """
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Configure scraping parameters
            params = {
                'formats': FORMATS,
                'blockAds': True
            }
            
            # Execute scrape
            scrape_result = self.app.scrape_url(url, params=params)
            
            if not scrape_result.get('success', False):
                logger.error(f"Failed to scrape URL: {url}")
                return {}
                
            return scrape_result.get('data', {})
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return {}

    def crawl_website(self, url: str, limit: int = CRAWL_LIMIT) -> List[Dict]:
        """
        Crawl a website starting from the given URL
        
        Args:
            url: The starting URL for crawling
            limit: Maximum number of pages to crawl
            
        Returns:
            List of dictionaries containing data for each crawled page
        """
        try:
            logger.info(f"Starting crawl for website: {url} with limit: {limit}")
            
            # Configure crawl parameters
            params = {
                'limit': limit,
                'scrapeOptions': {
                    'formats': FORMATS
                }
            }
            
            # Start asynchronous crawl job
            crawl_status = self.app.async_crawl_url(url, params=params)
            
            if not crawl_status.get('success', False):
                logger.error(f"Failed to start crawl for URL: {url}")
                return []
            
            # Get crawl ID
            crawl_id = crawl_status.get('id')
            if not crawl_id:
                logger.error("No crawl ID returned")
                return []
                
            # Poll for results
            return self._poll_for_crawl_results(crawl_id)
        except Exception as e:
            logger.error(f"Error crawling website {url}: {str(e)}")
            return []
            
    def _poll_for_crawl_results(self, crawl_id: str, max_attempts: int = 10) -> List[Dict]:
        """
        Poll for crawl results
        
        Args:
            crawl_id: ID of the crawl job
            max_attempts: Maximum number of polling attempts
            
        Returns:
            List of dictionaries containing data for each crawled page
        """
        attempt = 0
        poll_interval = 30  # seconds
        
        while attempt < max_attempts:
            attempt += 1
            
            # Check crawl status - use check_crawl_status method
            try:
                status = self.app.check_crawl_status(crawl_id)
                
                logger.info(f"Crawl status: {status.get('status', 'unknown')}")
                
                if status.get('status') == 'completed':
                    logger.info(f"Crawl {crawl_id} completed")
                    
                    # Get results directly from the status response
                    results = status.get('data', [])
                    logger.info(f"Retrieved {len(results)} pages from crawl")
                    return results
                    
                elif status.get('status') in ['failed', 'cancelled']:
                    logger.error(f"Crawl {crawl_id} {status.get('status')}")
                    return []
                
                logger.info(f"Crawl in progress, attempt {attempt}/{max_attempts}...")
                time.sleep(poll_interval)
                
            except Exception as e:
                logger.error(f"Error checking crawl status: {str(e)}")
                time.sleep(poll_interval)
            
        logger.warning(f"Max polling attempts reached for crawl {crawl_id}")
        return []

    def extract_links(self, page_data: Dict) -> List[Dict]:
        """
        Extract links from page data
        
        Args:
            page_data: Dictionary containing scraped page data
            
        Returns:
            List of dictionaries with link information
        """
        links = []
        
        # Extract raw links from the page
        raw_links = page_data.get('links', [])
        
        # Get page metadata
        metadata = page_data.get('metadata', {})
        source_url = metadata.get('sourceURL', '')
        
        logger.debug(f"Found {len(raw_links)} raw links")

        for link in raw_links:
            # Skip empty links
            if not link:
                continue
                
            # Create link entry
            link_info = {
                'url': link,
                'source_url': source_url,
                'page_title': metadata.get('title', ''),
            }
            
            links.append(link_info)
            
        return links