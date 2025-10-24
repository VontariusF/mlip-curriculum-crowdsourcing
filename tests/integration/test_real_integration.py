"""
Integration test - Tests actual functionality with real environment
"""
import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append('src')

@pytest.mark.integration
class TestSystemIntegration:
    """Test actual system functionality with real environment"""
    
    def test_scraping_agent_can_load_seed_sources(self):
        """Test that ScrapingAgent can load seed sources"""
        from src.scraping_agent import ScrapingAgent
        agent = ScrapingAgent()
        
        # Test that seed sources are loaded
        assert len(agent.seed_sources) > 0
        assert isinstance(agent.seed_sources, list)
        
        # Test structure of first seed source
        first_source = agent.seed_sources[0]
        assert 'url' in first_source
        assert 'source_type' in first_source
        assert 'crawl_frequency' in first_source
    
    def test_classification_agent_can_generate_embeddings(self):
        """Test that ClassificationAgent can generate embeddings"""
        from src.classification_agent import ClassificationAgent
        agent = ClassificationAgent()
        
        # Test that embedding model is loaded
        assert agent.embedding_model is not None
        
        # Test generating an embedding
        test_text = "This is a test MLIP paper about machine learning potentials."
        embedding = agent.embedding_model.encode(test_text)
        
        assert embedding is not None
        assert len(embedding) > 0
        assert isinstance(embedding, list) or hasattr(embedding, '__len__')
    
    def test_database_manager_can_construct_url(self):
        """Test that DatabaseManager can construct database URL"""
        from src.database import DatabaseManager
        manager = DatabaseManager()
        
        # Test database URL construction
        assert manager.database_url is not None
        assert 'postgresql://' in manager.database_url
        assert os.getenv('POSTGRES_HOST') in manager.database_url
        assert os.getenv('POSTGRES_DB') in manager.database_url
    
    def test_batch_processor_can_be_configured(self):
        """Test that BatchProcessor can be configured with different batch sizes"""
        from src.batch_processor import BatchProcessor
        
        # Test different batch sizes
        processor1 = BatchProcessor(batch_size=5)
        assert processor1.batch_size == 5
        
        processor2 = BatchProcessor(batch_size=20)
        assert processor2.batch_size == 20
        
        processor3 = BatchProcessor(batch_size=1)
        assert processor3.batch_size == 1
    
    def test_deduplication_manager_can_generate_hashes(self):
        """Test that DeduplicationManager can generate content hashes"""
        from src.deduplication import DeduplicationManager
        manager = DeduplicationManager()
        
        # Test content hash generation
        test_content = "This is test content for hashing."
        hash1 = manager.generate_content_hash(test_content)
        hash2 = manager.generate_content_hash(test_content)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string
        
        # Different content should produce different hash
        different_content = "This is different content."
        hash3 = manager.generate_content_hash(different_content)
        assert hash1 != hash3
    
    def test_terminal_hub_can_be_created(self):
        """Test that TerminalHub can be created and has expected attributes"""
        from src.terminal_hub import TerminalHub
        hub = TerminalHub()
        
        # Test that hub has expected attributes
        assert hub is not None
        # TerminalHub should have logging and display methods
        assert hasattr(hub, 'log_activity') or hasattr(hub, 'log_error') or hasattr(hub, 'live_display')
    
    def test_web_viewer_can_be_imported(self):
        """Test that web viewer can be imported and has expected structure"""
        from src.web_viewer import app
        
        # Test that FastAPI app exists
        assert app is not None
        assert hasattr(app, 'get')  # FastAPI apps have get method for routes
    
    def test_all_components_can_work_together(self):
        """Test that all components can be instantiated together"""
        from src.scraping_agent import ScrapingAgent
        from src.classification_agent import ClassificationAgent
        from src.database import DatabaseManager
        from src.batch_processor import BatchProcessor
        from src.deduplication import DeduplicationManager
        from src.terminal_hub import TerminalHub
        
        # Test that all components can be created
        scraping_agent = ScrapingAgent()
        classification_agent = ClassificationAgent()
        db_manager = DatabaseManager()
        batch_processor = BatchProcessor(batch_size=10)
        dedup_manager = DeduplicationManager()
        terminal_hub = TerminalHub()
        
        # All components should exist
        assert scraping_agent is not None
        assert classification_agent is not None
        assert db_manager is not None
        assert batch_processor is not None
        assert dedup_manager is not None
        assert terminal_hub is not None
        
        # Test that they can access each other's data
        assert len(scraping_agent.seed_sources) > 0
        assert classification_agent.embedding_model is not None
        assert db_manager.database_url is not None
        assert batch_processor.batch_size == 10

@pytest.mark.integration
class TestDataFlow:
    """Test data flow between components"""
    
    def test_scraped_resource_structure(self):
        """Test that ScrapedResource can be created with proper structure"""
        from src.scraping_agent import ScrapedResource
        
        resource = ScrapedResource(
            url="https://example.com/test",
            title="Test MLIP Paper",
            content="This is test content about MLIPs.",
            markdown="# Test MLIP Paper\n\nThis is test content about MLIPs.",
            source_site="example.com",
            relevance_score=0.9,
            metadata={"test": True}
        )
        
        assert resource.url == "https://example.com/test"
        assert resource.title == "Test MLIP Paper"
        assert resource.content == "This is test content about MLIPs."
        assert resource.source_site == "example.com"
        assert resource.relevance_score == 0.9
        assert resource.metadata["test"] == True
    
    def test_classified_resource_structure(self):
        """Test that ClassifiedResource can be created with proper structure"""
        from src.classification_agent import ClassifiedResource
        import numpy as np
        
        resource = ClassifiedResource(
            url="https://example.com/test",
            title="Test MLIP Paper",
            content="This is test content about MLIPs.",
            markdown="# Test MLIP Paper\n\nThis is test content about MLIPs.",
            source_site="example.com",
            resource_type="paper",
            difficulty_level="intermediate",
            topics=["machine learning", "interatomic potentials"],
            quality_score=0.85,
            embedding=np.array([0.1, 0.2, 0.3]),
            metadata={"test": True}
        )
        
        assert resource.url == "https://example.com/test"
        assert resource.resource_type == "paper"
        assert resource.difficulty_level == "intermediate"
        assert len(resource.topics) == 2
        assert resource.quality_score == 0.85
        assert len(resource.embedding) == 3
        assert resource.metadata["test"] == True
