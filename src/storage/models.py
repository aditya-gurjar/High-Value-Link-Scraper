import json
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from src.config import DATABASE_URL

# Create SQLAlchemy base
Base = declarative_base()

# Create engine
engine = create_engine(DATABASE_URL)

class Website(Base):
    """Model representing a crawled website"""
    __tablename__ = 'websites'
    
    id = Column(Integer, primary_key=True)
    domain = Column(String(255), unique=True, nullable=False)
    last_crawled = Column(DateTime, default=datetime.utcnow)
    crawl_count = Column(Integer, default=1)
    
    # Relationships
    links = relationship("Link", back_populates="website", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Website domain={self.domain}>"


class Link(Base):
    """Model representing a link found during crawling"""
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(1024), unique=True, nullable=False)
    source_url = Column(String(1024))
    page_title = Column(String(512))
    is_document = Column(Boolean, default=False)
    
    # Relevance scores
    contact_relevance = Column(Float, default=0.0)
    financial_relevance = Column(Float, default=0.0)
    official_relevance = Column(Float, default=0.0)
    overall_relevance = Column(Float, default=0.0)
    
    # Classification
    primary_category = Column(String(50))
    rationale = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Raw data
    metadata_json = Column(Text)
    
    # Relationships
    website_id = Column(Integer, ForeignKey('websites.id'))
    website = relationship("Website", back_populates="links")
    
    def __repr__(self):
        return f"<Link url={self.url}, relevance={self.overall_relevance}>"
    
    @property
    def link_metadata(self):
        """Get metadata as dictionary"""
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @link_metadata.setter
    def link_metadata(self, value):
        """Set metadata as JSON string"""
        if value is not None:
            self.metadata_json = json.dumps(value)
        else:
            self.metadata_json = None


# Ensure database directory exists
def ensure_db_directory():
    """Ensure the directory for SQLite database exists"""
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
        if db_path.startswith('./'):
            db_path = db_path[2:]
        
        # Get directory of the database file
        db_dir = os.path.dirname(db_path)
        
        # Create directory if it doesn't exist and is not empty
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)


# Database initialization function
def init_db():
    """Initialize database and tables"""
    # Ensure database directory exists
    ensure_db_directory()
    
    # Create tables
    Base.metadata.create_all(engine)
    return engine


# Session factory
def get_session():
    """Create a new database session"""
    Session = sessionmaker(bind=engine)
    return Session()