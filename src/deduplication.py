"""
Deduplication system for MLIP Curriculum Crowdsourcing
Implements three-tier approach: URL checking, content hash, embedding similarity
"""
import hashlib
import re
from typing import List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from .database import db_manager, Resource, ScrapeHistory

class DeduplicationManager:
    """Manages deduplication using multiple strategies"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def clean_content(self, content: str) -> str:
        """Clean content for consistent hashing"""
        # Remove extra whitespace and normalize
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Remove common metadata that might vary
        content = re.sub(r'Last updated:.*', '', content)
        content = re.sub(r'Published:.*', '', content)
        content = re.sub(r'DOI:.*', '', content)
        content = re.sub(r'arXiv:.*', '', content)
        
        return content
    
    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of cleaned content"""
        cleaned_content = self.clean_content(content)
        return hashlib.sha256(cleaned_content.encode('utf-8')).hexdigest()
    
    def check_url_exists(self, session: Session, url: str) -> bool:
        """Check if URL has been scraped before"""
        existing = session.query(ScrapeHistory).filter(ScrapeHistory.url == url).first()
        return existing is not None
    
    def check_content_hash_exists(self, session: Session, content_hash: str) -> Optional[Resource]:
        """Check if content hash already exists"""
        existing = session.query(Resource).filter(Resource.content_hash == content_hash).first()
        return existing
    
    def generate_embedding(self, content: str) -> np.ndarray:
        """Generate embedding for content"""
        # Use title + first 1000 characters for embedding
        embedding_text = content[:1000]
        embedding = self.embedding_model.encode(embedding_text)
        return embedding
    
    def find_similar_embeddings(self, session: Session, embedding: np.ndarray, threshold: float = 0.95) -> List[Resource]:
        """Find resources with similar embeddings"""
        # Convert embedding to list for pgvector
        embedding_list = embedding.tolist()
        
        # Query for similar embeddings using cosine similarity
        similar_resources = session.execute(
            """
            SELECT id, url, title, content_hash, 1 - (embedding <=> :embedding) as similarity
            FROM resources 
            WHERE embedding IS NOT NULL 
            AND 1 - (embedding <=> :embedding) > :threshold
            ORDER BY similarity DESC
            """,
            {
                'embedding': embedding_list,
                'threshold': threshold
            }
        ).fetchall()
        
        # Convert to Resource objects
        resource_ids = [row.id for row in similar_resources]
        resources = session.query(Resource).filter(Resource.id.in_(resource_ids)).all()
        
        return resources
    
    def is_duplicate(self, session: Session, url: str, content: str) -> Tuple[bool, str, Optional[Resource]]:
        """
        Check if content is a duplicate using three-tier approach
        
        Returns:
            (is_duplicate, reason, existing_resource)
        """
        # Tier 1: URL checking
        if self.check_url_exists(session, url):
            return True, "URL already scraped", None
        
        # Tier 2: Content hash checking
        content_hash = self.generate_content_hash(content)
        existing_resource = self.check_content_hash_exists(session, content_hash)
        if existing_resource:
            return True, "Content hash already exists", existing_resource
        
        # Tier 3: Embedding similarity checking
        embedding = self.generate_embedding(content)
        similar_resources = self.find_similar_embeddings(session, embedding, threshold=0.95)
        
        if similar_resources:
            # Find the most similar one
            most_similar = similar_resources[0]
            return True, "Similar content found via embedding", most_similar
        
        return False, "No duplicates found", None
    
    def record_scrape_attempt(self, session: Session, url: str, status: str = 'success', error_message: str = None):
        """Record a scrape attempt in history"""
        existing = session.query(ScrapeHistory).filter(ScrapeHistory.url == url).first()
        
        if existing:
            existing.last_scraped = session.query(ScrapeHistory).filter(ScrapeHistory.url == url).first().last_scraped
            existing.status = status
            existing.error_message = error_message
        else:
            history = ScrapeHistory(
                url=url,
                status=status,
                error_message=error_message
            )
            session.add(history)
    
    def save_resource_with_embedding(self, session: Session, resource_data: dict, content: str) -> Resource:
        """Save resource with generated embedding"""
        # Generate embedding
        embedding = self.generate_embedding(content)
        
        # Create resource
        resource = Resource(**resource_data)
        resource.embedding = embedding.tolist()
        
        session.add(resource)
        session.flush()  # Get the ID
        
        return resource
