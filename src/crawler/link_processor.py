import logging
import os
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

from src.config import HIGH_VALUE_KEYWORDS

logger = logging.getLogger(__name__)

class LinkProcessor:
    """Process and filter links from crawled pages"""
    
    def __init__(self):
        # File extensions that might contain valuable information
        self.valuable_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.csv', '.ppt', '.pptx', '.txt'
        }
        
        # Initialize set to track processed URLs
        self.processed_urls = set()
        
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize URL by resolving relative paths and removing fragments
        
        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative paths
            
        Returns:
            Normalized URL
        """
        # Handle relative URLs
        full_url = urljoin(base_url, url)
        
        # Parse URL
        parsed = urlparse(full_url)
        
        # Remove fragments
        normalized = parsed._replace(fragment='').geturl()
        
        return normalized
        
    def is_document_link(self, url: str) -> bool:
        """
        Check if URL points to a document
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to point to a document, False otherwise
        """
        # Check file extension
        _, ext = os.path.splitext(urlparse(url).path)
        return ext.lower() in self.valuable_extensions
        
    def initial_value_assessment(self, url: str) -> float:
        """
        Make an initial assessment of link value based on URL
        
        Args:
            url: URL to assess
            
        Returns:
            Initial value score (0.0 to 1.0)
        """
        # If it's a document, it has higher initial value
        if self.is_document_link(url):
            return 0.9
        
        # Check for valuable keywords in URL
        url_lower = url.lower()
        
        # For government sites, automatically assign higher value to deeper links
        if '.gov' in url_lower:
            # Higher value for deeper paths
            path_depth = url_lower.count('/')
            if path_depth >= 3:  # /path/to/something
                return min(0.6 + (path_depth * 0.05), 0.9)
        
        # Check for valuable keywords in URL
        keyword_count = sum(1 for keyword in HIGH_VALUE_KEYWORDS if keyword in url_lower)
        
        # Calculate initial score based on keyword presence
        if keyword_count > 0:
            return min(0.5 + (keyword_count * 0.1), 0.9)
            
        # For budget-related folders, set higher score
        for valuable_path in ['/budget', '/finance', '/financial', '/report', '/contact', '/staff', '/department']:
            if valuable_path in url_lower:
                return 0.7
                
        # Default score - more lenient now
        return 0.4  # Increased from 0.2 to send more links for AI analysis
        
    def process_links(self, links: List[Dict], base_url: str) -> List[Dict]:
        """
        Process a list of links extracted from a page
        
        Args:
            links: List of link dictionaries
            base_url: Base URL of the page
            
        Returns:
            List of processed link dictionaries
        """
        processed_links = []
        
        for link in links:
            url = link.get('url', '')
            
            # Skip empty URLs
            if not url:
                continue
                
            # Normalize URL
            normalized_url = self.normalize_url(url, base_url)
            
            # Skip already processed URLs
            if normalized_url in self.processed_urls:
                continue
                
            # Mark as processed
            self.processed_urls.add(normalized_url)
            
            # Make initial value assessment
            initial_value = self.initial_value_assessment(normalized_url)
            
            # Create processed link entry
            processed_link = {
                'url': normalized_url,
                'source_url': link.get('source_url', base_url),
                'page_title': link.get('page_title', ''),
                'is_document': self.is_document_link(normalized_url),
                'initial_value': initial_value
            }
            
            processed_links.append(processed_link)
            
        return processed_links