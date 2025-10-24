"""
Basic system test using real environment variables
Tests that all modules can be imported and basic functionality works
"""
import pytest
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.append('src')

@pytest.mark.unit
class TestSystemWithRealEnv:
    """Test system components with real environment variables"""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded"""
        # Check that key environment variables are loaded
        assert os.getenv('SCRAPING_AGENT_API_KEY') is not None, "SCRAPING_AGENT_API_KEY not found"
        assert os.getenv('CLASSIFICATION_AGENT_API_KEY') is not None, "CLASSIFICATION_AGENT_API_KEY not found"
        assert os.getenv('FIRECRAWL_API_KEY') is not None, "FIRECRAWL_API_KEY not found"
        assert os.getenv('FIRECRAWL_API_URL') is not None, "FIRECRAWL_API_URL not found"
        
        # Check database configuration
        assert os.getenv('POSTGRES_HOST') is not None, "POSTGRES_HOST not found"
        assert os.getenv('POSTGRES_PORT') is not None, "POSTGRES_PORT not found"
        assert os.getenv('POSTGRES_DB') is not None, "POSTGRES_DB not found"
        assert os.getenv('POSTGRES_USER') is not None, "POSTGRES_USER not found"
        assert os.getenv('POSTGRES_PASSWORD') is not None, "POSTGRES_PASSWORD not found"
    
    def test_import_scraping_agent(self):
        """Test that ScrapingAgent can be imported and initialized"""
        from src.scraping_agent import ScrapingAgent
        agent = ScrapingAgent()
        assert agent is not None
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'firecrawl_app')
        assert hasattr(agent, 'seed_sources')
    
    def test_import_classification_agent(self):
        """Test that ClassificationAgent can be imported and initialized"""
        from src.classification_agent import ClassificationAgent
        agent = ClassificationAgent()
        assert agent is not None
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'embedding_model')
    
    def test_import_database_manager(self):
        """Test that DatabaseManager can be imported and initialized"""
        from src.database import DatabaseManager
        manager = DatabaseManager()
        assert manager is not None
        assert hasattr(manager, 'database_url')
    
    def test_import_terminal_hub(self):
        """Test that TerminalHub can be imported and initialized"""
        from src.terminal_hub import TerminalHub
        hub = TerminalHub()
        assert hub is not None
    
    def test_import_batch_processor(self):
        """Test that BatchProcessor can be imported and initialized"""
        from src.batch_processor import BatchProcessor
        processor = BatchProcessor(batch_size=10)
        assert processor is not None
        assert processor.batch_size == 10
    
    def test_import_deduplication_manager(self):
        """Test that DeduplicationManager can be imported and initialized"""
        from src.deduplication import DeduplicationManager
        manager = DeduplicationManager()
        assert manager is not None
    
    def test_import_web_viewer(self):
        """Test that web viewer can be imported"""
        from src.web_viewer import app
        assert app is not None

@pytest.mark.unit
class TestBasicFunctionality:
    """Test basic functionality of components"""
    
    def test_scraping_agent_methods(self):
        """Test that ScrapingAgent has expected methods"""
        from src.scraping_agent import ScrapingAgent
        agent = ScrapingAgent()
        
        # Check for expected methods (based on actual implementation)
        assert hasattr(agent, 'scrape_batch')
        assert hasattr(agent, '_scrape_source')
        assert hasattr(agent, '_load_seed_sources')
        assert hasattr(agent, 'initialize')
    
    def test_classification_agent_methods(self):
        """Test that ClassificationAgent has expected methods"""
        from src.classification_agent import ClassificationAgent
        agent = ClassificationAgent()
        
        # Check for expected methods (based on actual implementation)
        assert hasattr(agent, 'classify_batch')
        assert hasattr(agent, '_classify_resource')
        assert hasattr(agent, '_generate_embedding')
        assert hasattr(agent, 'initialize')
    
    def test_database_manager_methods(self):
        """Test that DatabaseManager has expected methods"""
        from src.database import DatabaseManager
        manager = DatabaseManager()
        
        # Check for expected methods (based on actual implementation)
        assert hasattr(manager, 'create_tables')
        assert hasattr(manager, 'get_session')
        assert hasattr(manager, 'init_database')
    
    def test_deduplication_manager_methods(self):
        """Test that DeduplicationManager has expected methods"""
        from src.deduplication import DeduplicationManager
        manager = DeduplicationManager()
        
        # Check for expected methods
        assert hasattr(manager, 'check_duplicate') or hasattr(manager, 'is_duplicate')
        assert hasattr(manager, 'generate_content_hash') or hasattr(manager, 'hash_content')
    
    def test_batch_processor_methods(self):
        """Test that BatchProcessor has expected methods"""
        from src.batch_processor import BatchProcessor
        processor = BatchProcessor(batch_size=5)
        
        # Check for expected methods (based on actual implementation)
        assert hasattr(processor, 'deduplicate_batch')
        assert hasattr(processor, 'store_batch')
        assert hasattr(processor, 'process_batch')

@pytest.mark.unit
class TestDataStructures:
    """Test data structures and models"""
    
    def test_scraped_resource_dataclass(self):
        """Test ScrapedResource dataclass structure"""
        from src.scraping_agent import ScrapedResource
        
        # Test creating a ScrapedResource instance
        resource = ScrapedResource(
            url="https://example.com",
            title="Test Resource",
            content="Test content",
            markdown="# Test Resource\n\nTest content",
            source_site="example.com",
            relevance_score=0.9,
            metadata={"test": "data"}
        )
        
        assert resource.url == "https://example.com"
        assert resource.title == "Test Resource"
        assert resource.content == "Test content"
        assert resource.source_site == "example.com"
        assert resource.relevance_score == 0.9
    
    def test_classified_resource_dataclass(self):
        """Test ClassifiedResource dataclass structure"""
        from src.classification_agent import ClassifiedResource
        import numpy as np
        
        # Test creating a ClassifiedResource instance
        resource = ClassifiedResource(
            url="https://example.com",
            title="Test Resource",
            content="Test content",
            markdown="# Test Resource\n\nTest content",
            source_site="example.com",
            resource_type="paper",
            difficulty_level="intermediate",
            topics=["machine learning", "AI"],
            quality_score=0.85,
            embedding=np.array([0.1, 0.2, 0.3]),
            metadata={"test": "data"}
        )
        
        assert resource.url == "https://example.com"
        assert resource.resource_type == "paper"
        assert resource.difficulty_level == "intermediate"
        assert len(resource.topics) == 2
        assert resource.quality_score == 0.85

@pytest.mark.unit
class TestConfiguration:
    """Test configuration and setup"""
    
    def test_seed_sources_loaded(self):
        """Test that seed sources are properly loaded"""
        import json
        
        # Check that seed sources file exists and is valid
        with open('src/seed_sources.json', 'r') as f:
            seed_data = json.load(f)
        
        assert isinstance(seed_data, dict)
        assert 'seed_sources' in seed_data
        assert isinstance(seed_data['seed_sources'], list)
        assert len(seed_data['seed_sources']) > 0
        
        # Check structure of seed sources
        for source in seed_data['seed_sources']:
            assert 'url' in source
            assert 'source_type' in source
            assert 'crawl_frequency' in source
    
    def test_database_url_construction(self):
        """Test database URL construction"""
        from src.database import DatabaseManager
        manager = DatabaseManager()
        
        # Check that database URL is properly constructed
        assert manager.database_url is not None
        assert 'postgresql://' in manager.database_url
        assert os.getenv('POSTGRES_HOST') in manager.database_url
        assert os.getenv('POSTGRES_DB') in manager.database_url
    
    def test_batch_processor_configuration(self):
        """Test BatchProcessor configuration"""
        from src.batch_processor import BatchProcessor
        
        # Test different batch sizes
        processor1 = BatchProcessor(batch_size=5)
        assert processor1.batch_size == 5
        
        processor2 = BatchProcessor(batch_size=20)
        assert processor2.batch_size == 20

@pytest.mark.integration
class TestComponentIntegration:
    """Test integration between components"""
    
    def test_agent_initialization(self):
        """Test that agents can be initialized together"""
        from src.scraping_agent import ScrapingAgent
        from src.classification_agent import ClassificationAgent
        
        scraping_agent = ScrapingAgent()
        classification_agent = ClassificationAgent()
        
        assert scraping_agent is not None
        assert classification_agent is not None
    
    def test_database_models_import(self):
        """Test that all database models can be imported"""
        from src.database import Resource, ScrapeHistory, SeedSource
        
        assert Resource is not None
        assert ScrapeHistory is not None
        assert SeedSource is not None
    
    def test_main_module_import(self):
        """Test that main module can be imported"""
        # The main module is main.py in the root directory, not src/main.py
        import main
        assert main is not None
