"""
Database models and setup for MLIP Curriculum Crowdsourcing System
"""
import os
from datetime import datetime
from typing import Optional

import numpy as np
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    create_engine, Index, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid

from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Resource(Base):
    """Stores scraped curriculum content"""
    __tablename__ = 'resources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False, unique=True)
    title = Column(String(512), nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    content_markdown = Column(Text, nullable=False)
    resource_type = Column(String(50), nullable=False)  # paper, lecture, exercise, documentation, tutorial
    difficulty_level = Column(String(20), nullable=False)  # beginner, intermediate, advanced, expert
    source_site = Column(String(255), nullable=False)
    topics = Column(Text)  # JSON string of topics
    scraped_at = Column(DateTime, default=datetime.utcnow)
    embedding = Column(Vector(384))  # Sentence transformer embedding dimension
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_content_hash', 'content_hash'),
        Index('idx_resource_type', 'resource_type'),
        Index('idx_difficulty_level', 'difficulty_level'),
        Index('idx_source_site', 'source_site'),
        Index('idx_scraped_at', 'scraped_at'),
    )

class ScrapeHistory(Base):
    """Tracks scraping history to avoid duplicates"""
    __tablename__ = 'scrape_history'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False, unique=True)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False, default='success')  # success, failed, skipped
    error_message = Column(Text)
    
    __table_args__ = (
        Index('idx_url', 'url'),
        Index('idx_last_scraped', 'last_scraped'),
        Index('idx_status', 'status'),
    )

class SeedSource(Base):
    """Manages seed sources for scraping"""
    __tablename__ = 'seed_sources'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(2048), nullable=False)
    source_type = Column(String(50), nullable=False)  # arxiv, github, youtube, course, tutorial
    crawl_frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    enabled = Column(Boolean, default=True)
    last_crawled = Column(DateTime)
    priority = Column(Integer, default=1)  # 1-10, higher is more important
    description = Column(Text)
    
    __table_args__ = (
        Index('idx_source_type', 'source_type'),
        Index('idx_enabled', 'enabled'),
        Index('idx_priority', 'priority'),
        Index('idx_last_crawled', 'last_crawled'),
    )

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            # Construct from individual components
            host = os.getenv('POSTGRES_HOST', 'localhost')
            port = os.getenv('POSTGRES_PORT', '5432')
            db = os.getenv('POSTGRES_DB', 'mlip_curriculum')
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD', 'postgres')
            self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def init_database(self):
        """Initialize database with pgvector extension"""
        with self.engine.connect() as conn:
            # Enable pgvector extension
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
        
        # Create tables
        self.create_tables()
    
    def insert_embedding(self, session, resource_id: str, embedding: np.ndarray):
        """Insert embedding for a resource"""
        session.query(Resource).filter(Resource.id == resource_id).update({
            'embedding': embedding.tolist()
        })
    
    def find_similar_resources(self, session, embedding: np.ndarray, threshold: float = 0.95, limit: int = 10):
        """Find similar resources using vector similarity"""
        # Using cosine similarity with pgvector
        results = session.execute(
            """
            SELECT id, url, title, 1 - (embedding <=> :embedding) as similarity
            FROM resources 
            WHERE 1 - (embedding <=> :embedding) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
            """,
            {
                'embedding': embedding.tolist(),
                'threshold': threshold,
                'limit': limit
            }
        )
        return results.fetchall()

# Global database manager instance
db_manager = DatabaseManager()
