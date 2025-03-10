# High-Value Link Scraper

A web scraper that identifies high-value links on web pages, focusing on extracting relevant contacts and specific files (like "ACFR," "Budget," or related terms). The system uses FireCrawl for web crawling and OpenAI for intelligent link prioritization.

## Project Overview

This tool is designed to scrape websites (particularly government and institutional sites) to discover high-value content such as:
- Financial documents (ACFR, budgets, financial reports)
- Contact information for key personnel (finance directors, etc.)
- Official documents and reports

The system crawls websites, analyzes discovered links using a combination of heuristic analysis and AI-powered classification, and provides an API to access the prioritized links.

## Features

- **Intelligent Web Crawling**: Uses FireCrawl API to efficiently crawl websites
- **Two-Stage Link Prioritization**:
  - Initial assessment based on URL patterns and keywords
  - AI-powered analysis of promising links using OpenAI
- **Government Site Optimization**: Special handling for .gov domains and city websites
- **Document-focused**: Higher prioritization for PDFs and other document formats
- **RESTful API**: Access links with filtering by relevance, category, and more
- **SQLite Storage**: Lightweight data storage for links and metadata

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- FireCrawl API key (for web crawling)
- OpenAI API key (for link prioritization)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd high-value-link-scraper
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   FIRECRAWL_API_KEY=your_firecrawl_api_key
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=sqlite:///./links.db
   ```

### Usage

#### Crawling a Website

To crawl a website and extract high-value links:

```
python main.py crawl https://example.com --limit 50
```

This will:
1. Crawl up to 50 pages on the specified website
2. Process discovered links and assess their potential value
3. Send promising links to OpenAI for detailed analysis
4. Store the results in the database

#### Starting the API Server

To start the API server:

```
python main.py api
```

The API will be available at http://localhost:8000.

## Link Prioritization Approach

The system uses a sophisticated two-stage approach to prioritize links:

### 1. Initial Assessment (Heuristic-based)

All discovered links are first evaluated based on:

- **Document Detection**: Higher scores for PDFs, DOCs, XLSXs and other document formats
- **Keyword Matching**: URLs containing terms like "budget", "financial", "report", etc.
- **Domain Analysis**: Special scoring for .gov domains and deeper paths
- **Path Analysis**: Higher scores for paths like "/finance", "/budget", "/contact"

This produces an initial value score between 0.0 and 1.0.

### 2. AI Analysis (OpenAI-powered)

Links with an initial score above 0.4 are sent to OpenAI for deeper analysis:

- The system prompts the AI to evaluate the link's potential relevance for:
  - Contact information
  - Financial documents
  - Official/government documents

- The AI returns detailed scores for each category and an overall relevance score
- Links are classified into categories based on their highest relevance scores

### 3. Prioritization

Links are then:
- Ranked by their overall relevance score
- Categorized for easy filtering
- Stored with all metadata for retrieval via the API

This two-stage approach balances efficiency with accuracy, using lightweight initial filtering to minimize API calls while ensuring high-value links receive detailed analysis.

## API Usage Guide

The API provides several endpoints for accessing and filtering links:

### Get Links with Filtering

```
GET /links?min_relevance=0.7&category=financial&limit=20
```

**Parameters:**
- `min_relevance`: Minimum relevance score (0.0 to 1.0)
- `category`: Filter by category (contact, financial, official, other)
- `is_document`: Filter document links (true/false)
- `limit`: Maximum number of links to return

### Search Links

```
GET /links/search?query=budget&limit=10
```

**Parameters:**
- `query`: Search term to look for in URLs or page titles
- `limit`: Maximum number of links to return

### Get Links by Website

```
GET /links/website/1?limit=20
```

**Parameters:**
- `website_id`: ID of the website (path parameter)
- `limit`: Maximum number of links to return

### Get Statistics

```
GET /stats
```

Returns counts of websites, links, documents, and category distribution.

### Start a Crawl

```
POST /crawl
```

**Request Body:**
```json
{
  "url": "https://www.a2gov.org",
  "limit": 50
}
```

**Parameters:**
- `url`: URL to start crawling from
- `limit`: Maximum number of pages to crawl

## Scaling Considerations

This implementation can be scaled for production use through several approaches:

### 1. Distributed Crawling

- **Message Queue**: Implement RabbitMQ/Kafka to queue crawl jobs
- **Worker Pools**: Deploy multiple crawler instances to process the queue
- **Pagination Handling**: The current FireCrawl implementation supports pagination for larger crawls

### 2. Database Optimization

- **Database Migration**: For production, replace SQLite with PostgreSQL/MySQL
- **Connection Pooling**: Implement connection pools for better performance
- **Indexing Strategy**: Add indices to frequently queried fields (URL, relevance scores)

### 3. API Performance

- **Caching**: Add Redis caching for frequently accessed endpoints
- **Rate Limiting**: Implement rate limiting for API consumers
- **Load Balancing**: Deploy multiple API instances behind a load balancer

### 4. Cost Management

- **AI Tiering**: The two-stage prioritization approach already minimizes OpenAI API calls
- **Batch Processing**: Links are processed in batches to reduce API overhead
- **Crawl Limits**: The system allows specifying page limits to control crawl costs

### 5. Monitoring and Logging

- **Performance Metrics**: Add Prometheus/Grafana for monitoring
- **Detailed Logging**: Enhanced logging for troubleshooting
- **Alerting**: Set up alerts for errors or performance issues

## Development Process and Decisions

### Technical Choices

- **FireCrawl API**: Chosen for efficient web crawling with minimal setup
- **OpenAI Integration**: Provides high-quality link classification without ML model training
- **FastAPI**: Modern, high-performance API framework with automatic documentation
- **SQLite**: Lightweight database ideal for development and testing
- **Two-Stage Prioritization**: Balances cost, performance, and accuracy

### Optimization for Government Sites

Special attention was given to optimizing for government websites:
- Enhanced scoring for .gov domains
- Expanded keyword list focused on government and financial terms
- Special path handling for common government site structures

### Future Improvements

With additional time, these enhancements could be added:
- Implement full-text search of crawled content
- Add machine learning model training on labeled data
- Develop a web UI for exploring discovered links
- Include entity extraction from documents
- Add support for OCR on scanned PDFs