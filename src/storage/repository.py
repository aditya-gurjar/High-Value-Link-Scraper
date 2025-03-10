import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.storage.models import Website, Link, get_session

logger = logging.getLogger(__name__)

class LinkRepository:
    """Repository for storing and retrieving link data"""
    
    def __init__(self):
        """Initialize repository with database session"""
        self.session = get_session()
        
    def close(self):
        """Close database session"""
        self.session.close()
        
    def get_or_create_website(self, url: str) -> Website:
        """
        Get or create a website record by domain
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Website record
        """
        domain = self._extract_domain(url)
        
        # Try to find existing website
        website = self.session.query(Website).filter_by(domain=domain).first()
        
        if website:
            # Update last crawled time and increment count
            website.last_crawled = datetime.utcnow()
            website.crawl_count += 1
        else:
            # Create new website
            website = Website(domain=domain)
            self.session.add(website)
            
        self.session.commit()
        return website
        
    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
        
    def add_link(self, link_data: Dict, website: Website) -> Link:
        """
        Add a link to the database
        
        Args:
            link_data: Dictionary containing link data
            website: Website record to associate with link
            
        Returns:
            Created or updated Link record
        """
        url = link_data.get('url')
        
        # Check if link already exists
        link = self.session.query(Link).filter_by(url=url).first()
        
        if link:
            # Update existing link
            link.source_url = link_data.get('source_url', link.source_url)
            link.page_title = link_data.get('page_title', link.page_title)
            link.contact_relevance = link_data.get('contact_relevance', link.contact_relevance)
            link.financial_relevance = link_data.get('financial_relevance', link.financial_relevance)
            link.official_relevance = link_data.get('official_relevance', link.official_relevance)
            link.overall_relevance = link_data.get('overall_relevance', link.overall_relevance)
            link.primary_category = link_data.get('primary_category', link.primary_category)
            link.rationale = link_data.get('rationale', link.rationale)
            link.updated_at = datetime.utcnow()
        else:
            # Create new link
            link = Link(
                url=url,
                source_url=link_data.get('source_url', ''),
                page_title=link_data.get('page_title', ''),
                is_document=link_data.get('is_document', False),
                contact_relevance=link_data.get('contact_relevance', 0.0),
                financial_relevance=link_data.get('financial_relevance', 0.0),
                official_relevance=link_data.get('official_relevance', 0.0),
                overall_relevance=link_data.get('overall_relevance', 0.0),
                primary_category=link_data.get('primary_category', 'other'),
                rationale=link_data.get('rationale', ''),
                website=website
            )
            
            # Add metadata if available
            if link_data.get('metadata'):
                link.link_metadata = link_data.get('metadata')
                
            self.session.add(link)
            
        self.session.commit()
        return link
        
    def add_links(self, links: List[Dict], website: Website) -> List[Link]:
        """
        Add multiple links to the database
        
        Args:
            links: List of link data dictionaries
            website: Website record to associate with links
            
        Returns:
            List of created or updated Link records
        """
        added_links = []
        
        for link_data in links:
            try:
                link = self.add_link(link_data, website)
                added_links.append(link)
            except Exception as e:
                logger.error(f"Error adding link {link_data.get('url')}: {str(e)}")
                
        return added_links
        
    def get_links_by_relevance(self, min_relevance: float = 0.0, limit: int = 100) -> List[Link]:
        """
        Get links ordered by relevance
        
        Args:
            min_relevance: Minimum relevance score
            limit: Maximum number of links to return
            
        Returns:
            List of Link records
        """
        return self.session.query(Link)\
            .filter(Link.overall_relevance >= min_relevance)\
            .order_by(desc(Link.overall_relevance))\
            .limit(limit)\
            .all()
            
    def get_links_by_category(self, category: str, limit: int = 100) -> List[Link]:
        """
        Get links by category
        
        Args:
            category: Link category
            limit: Maximum number of links to return
            
        Returns:
            List of Link records
        """
        return self.session.query(Link)\
            .filter(Link.primary_category == category)\
            .order_by(desc(Link.overall_relevance))\
            .limit(limit)\
            .all()
            
    def get_links_by_website(self, website_id: int, limit: int = 100) -> List[Link]:
        """
        Get links for a specific website
        
        Args:
            website_id: Website ID
            limit: Maximum number of links to return
            
        Returns:
            List of Link records
        """
        return self.session.query(Link)\
            .filter(Link.website_id == website_id)\
            .order_by(desc(Link.overall_relevance))\
            .limit(limit)\
            .all()
            
    def get_document_links(self, limit: int = 100) -> List[Link]:
        """
        Get document links
        
        Args:
            limit: Maximum number of links to return
            
        Returns:
            List of Link records
        """
        return self.session.query(Link)\
            .filter(Link.is_document == True)\
            .order_by(desc(Link.overall_relevance))\
            .limit(limit)\
            .all()
            
    def get_all_websites(self) -> List[Website]:
        """
        Get all websites that have been crawled
        
        Returns:
            List of Website records
        """
        return self.session.query(Website)\
            .order_by(desc(Website.last_crawled))\
            .all()
            
    def search_links(self, query: str, limit: int = 100) -> List[Link]:
        """
        Search links by URL or page title
        
        Args:
            query: Search query
            limit: Maximum number of links to return
            
        Returns:
            List of Link records
        """
        search_term = f"%{query}%"
        return self.session.query(Link)\
            .filter((Link.url.like(search_term)) | (Link.page_title.like(search_term)))\
            .order_by(desc(Link.overall_relevance))\
            .limit(limit)\
            .all()
            
    def get_website_count(self) -> int:
        """
        Get count of websites
        
        Returns:
            Count of websites
        """
        return self.session.query(Website).count()
        
    def get_link_count(self) -> int:
        """
        Get count of links
        
        Returns:
            Count of links
        """
        return self.session.query(Link).count()
        
    def get_document_count(self) -> int:
        """
        Get count of document links
        
        Returns:
            Count of document links
        """
        return self.session.query(Link).filter(Link.is_document == True).count()
        
    def get_category_counts(self) -> Dict[str, int]:
        """
        Get counts of links by category
        
        Returns:
            Dictionary of category counts
        """
        from sqlalchemy import func
        categories = self.session.query(Link.primary_category, func.count(Link.primary_category)).group_by(Link.primary_category).all()
        return {category: count for category, count in categories}