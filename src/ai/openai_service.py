import logging
import json
from typing import Dict, List

import openai
from openai import OpenAI

from src.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for interacting with OpenAI API to analyze link relevance"""
    
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"OpenAI service initialized with model: {model}")
        
    def analyze_link_relevance(self, link_data: Dict) -> Dict:
        """
        Analyze a link's relevance for finding contacts and financial documents
        
        Args:
            link_data: Dictionary containing link information
            
        Returns:
            Dictionary with relevance scores and categories
        """
        try:
            # Extract relevant information for analysis
            url = link_data.get('url', '')
            page_title = link_data.get('page_title', '')
            is_document = link_data.get('is_document', False)
            
            # Craft prompt for OpenAI
            system_prompt = """
            You are an AI assistant that analyzes website links to identify high-value content related to:
            1. Contact information (especially for finance directors, government officials)
            2. Financial documents (ACFR, Annual Comprehensive Financial Reports, budgets, financial statements)
            3. Government reports and official documents
            
            Analyze the provided URL and page title to determine relevance.
            """
            
            user_prompt = f"""
            Please analyze this link and provide a JSON response with these fields:
            
            Link information:
            - URL: {url}
            - Page title: {page_title}
            - Is document: {is_document}
            
            Rate on a scale of 0.0 to 1.0:
            1. contact_relevance: How likely this contains contact information
            2. financial_relevance: How likely this contains financial documents/information
            3. official_relevance: How likely this contains government/official documents
            
            Add these fields:
            - overall_relevance: Overall score (maximum of the three scores)
            - primary_category: One of ["contact", "financial", "official", "other"]
            - rationale: Brief explanation of your reasoning (max 100 characters)
            
            Return ONLY valid JSON, nothing else.
            """
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            relevance_data = json.loads(response_text)
            
            return relevance_data
        except Exception as e:
            logger.error(f"Error analyzing link relevance: {str(e)}")
            # Return default values
            return {
                "contact_relevance": 0.0,
                "financial_relevance": 0.0,
                "official_relevance": 0.0,
                "overall_relevance": 0.0,
                "primary_category": "other",
                "rationale": "Error during analysis"
            }
            
    def batch_analyze_links(self, links: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Analyze a batch of links for relevance
        
        Args:
            links: List of link dictionaries
            batch_size: Number of links to analyze in a single batch
            
        Returns:
            List of links with added relevance data
        """
        enriched_links = []
        
        # Process links in batches
        for i in range(0, len(links), batch_size):
            batch = links[i:i+batch_size]
            
            # Only analyze links with sufficient initial value
            # to save on API costs - using a lower threshold now
            for link in batch:
                initial_value = link.get('initial_value', 0.0)
                
                # If initial value is high enough, use AI for detailed analysis
                # Lower threshold from 0.5 to 0.4 to analyze more links
                if initial_value >= 0.4:
                    try:
                        relevance_data = self.analyze_link_relevance(link)
                        link.update(relevance_data)
                    except Exception as e:
                        logger.error(f"Error analyzing link {link.get('url')}: {str(e)}")
                        # Provide default values on error, but maintain the initial value
                        link.update({
                            "contact_relevance": 0.0,
                            "financial_relevance": 0.0,
                            "official_relevance": 0.0,
                            "overall_relevance": initial_value,  # Use initial value instead of 0
                            "primary_category": "other",
                            "rationale": f"Error during analysis: {str(e)}"
                        })
                else:
                    # For low initial value links, skip AI analysis
                    link.update({
                        "contact_relevance": 0.0,
                        "financial_relevance": 0.0,
                        "official_relevance": 0.0,
                        "overall_relevance": initial_value,
                        "primary_category": "other",
                        "rationale": "Low initial value assessment"
                    })
                
                enriched_links.append(link)
                
        # Sort links by overall relevance
        enriched_links.sort(key=lambda x: x.get('overall_relevance', 0.0), reverse=True)
        
        return enriched_links