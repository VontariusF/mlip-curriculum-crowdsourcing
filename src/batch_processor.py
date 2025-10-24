"""
Batch Processor for handling deduplication and storage
Manages the batched processing workflow
"""
import asyncio
import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
import numpy as np

from .database import db_manager, Resource, ScrapeHistory
from .deduplication import DeduplicationManager

@dataclass
class ProcessingResult:
    """Result of batch processing"""
    stored_count: int
    duplicates_found: int
    errors: List[str]

class BatchProcessor:
    """Handles batched processing of resources"""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.deduplication_manager = DeduplicationManager()
    
    async def deduplicate_batch(self, resources: List) -> Tuple[List, List]:
        """Deduplicate a batch of resources"""
        validated_resources = []
        duplicates = []
        
        session = db_manager.get_session()
        
        try:
            for resource in resources:
                # Check for duplicates
                is_duplicate, reason, existing_resource = self.deduplication_manager.is_duplicate(
                    session, resource.url, resource.content
                )
                
                if is_duplicate:
                    duplicates.append({
                        'resource': resource,
                        'reason': reason,
                        'existing': existing_resource
                    })
                else:
                    validated_resources.append(resource)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Error in deduplication: {e}")
        finally:
            session.close()
        
        return validated_resources, duplicates
    
    async def store_batch(self, resources: List) -> int:
        """Store a batch of validated resources"""
        stored_count = 0
        session = db_manager.get_session()
        
        try:
            for resource in resources:
                try:
                    # Create resource record
                    resource_data = {
                        'url': resource.url,
                        'title': resource.title,
                        'content_hash': self.deduplication_manager.generate_content_hash(resource.content),
                        'content_markdown': resource.markdown,
                        'resource_type': resource.resource_type,
                        'difficulty_level': resource.difficulty_level,
                        'source_site': resource.source_site,
                        'topics': ','.join(resource.topics) if isinstance(resource.topics, list) else str(resource.topics)
                    }
                    
                    # Save with embedding
                    db_resource = self.deduplication_manager.save_resource_with_embedding(
                        session, resource_data, resource.content
                    )
                    
                    # Record successful scrape
                    self.deduplication_manager.record_scrape_attempt(session, resource.url, 'success')
                    
                    stored_count += 1
                    
                except Exception as e:
                    print(f"Error storing resource {resource.url}: {e}")
                    self.deduplication_manager.record_scrape_attempt(
                        session, resource.url, 'failed', str(e)
                    )
                    continue
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Error in batch storage: {e}")
        finally:
            session.close()
        
        return stored_count
    
    async def process_batch(self, resources: List) -> ProcessingResult:
        """Process a complete batch"""
        errors = []
        
        try:
            # Step 1: Deduplication
            validated_resources, duplicates = await self.deduplicate_batch(resources)
            
            # Step 2: Storage
            stored_count = await self.store_batch(validated_resources)
            
            return ProcessingResult(
                stored_count=stored_count,
                duplicates_found=len(duplicates),
                errors=errors
            )
            
        except Exception as e:
            errors.append(str(e))
            return ProcessingResult(
                stored_count=0,
                duplicates_found=0,
                errors=errors
            )
    
    def get_batch_statistics(self) -> dict:
        """Get batch processing statistics"""
        session = db_manager.get_session()
        
        try:
            total_resources = session.query(Resource).count()
            total_scrapes = session.query(ScrapeHistory).count()
            successful_scrapes = session.query(ScrapeHistory).filter(
                ScrapeHistory.status == 'success'
            ).count()
            
            return {
                'total_resources': total_resources,
                'total_scrapes': total_scrapes,
                'successful_scrapes': successful_scrapes,
                'success_rate': (successful_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0
            }
            
        finally:
            session.close()
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Clean up old data"""
        session = db_manager.get_session()
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Remove old scrape history
            old_history = session.query(ScrapeHistory).filter(
                ScrapeHistory.last_scraped < cutoff_date
            ).delete()
            
            session.commit()
            
            return old_history
            
        except Exception as e:
            session.rollback()
            print(f"Error cleaning up old data: {e}")
            return 0
        finally:
            session.close()
