"""
Pytest configuration and fixtures for MLIP Curriculum Crowdsourcing System tests
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, AsyncMock
from faker import Faker
from typing import Dict, List, Any

# Add src to path for imports
import sys
sys.path.append('src')

fake = Faker()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_firecrawl_response():
    """Mock Firecrawl API response"""
    return {
        "url": "https://example.com",
        "title": "Example MLIP Paper",
        "content": "This is a comprehensive paper about machine learned interatomic potentials...",
        "metadata": {
            "description": "A detailed study on MLIPs",
            "author": "Dr. Example",
            "published_date": "2024-01-01"
        }
    }

@pytest.fixture
def mock_llm_response():
    """Mock LLM classification response"""
    return {
        "resource_type": "paper",
        "difficulty_level": "advanced",
        "confidence": 0.95,
        "topics": ["machine learning", "interatomic potentials", "materials science"]
    }

@pytest.fixture
def sample_resource_data():
    """Sample resource data for testing"""
    return {
        "url": "https://arxiv.org/abs/2401.00001",
        "title": "Machine Learned Interatomic Potentials: A Comprehensive Review",
        "content": "Machine learned interatomic potentials (MLIPs) have revolutionized...",
        "source_site": "arxiv.org",
        "resource_type": "paper",
        "difficulty_level": "advanced"
    }

@pytest.fixture
def sample_seed_sources():
    """Sample seed sources for testing"""
    return [
        {
            "url": "https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=machine+learned+interatomic+potentials",
            "source_type": "arxiv_search",
            "crawl_frequency": "daily",
            "priority": 10,
            "description": "arXiv search for MLIP papers",
            "enabled": True
        },
        {
            "url": "https://github.com/ACEsuit/mace",
            "source_type": "github_repo",
            "crawl_frequency": "weekly",
            "priority": 8,
            "description": "MACE framework repository",
            "enabled": True
        }
    ]

@pytest.fixture
def mock_database_config():
    """Mock database configuration for testing"""
    return {
        "host": "localhost",
        "port": 5433,
        "database": "test_mlip_curriculum",
        "user": "test_user",
        "password": "test_password"
    }

@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    return {
        "SCRAPING_AGENT_USER_KEY": "test_user_key",
        "SCRAPING_AGENT_API_KEY": "test_api_key",
        "SCRAPING_AGENT_MODEL": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        "CLASSIFICATION_AGENT_USER_KEY": "test_classification_user_key",
        "CLASSIFICATION_AGENT_API_KEY": "test_classification_api_key",
        "CLASSIFICATION_AGENT_MODEL": "ServiceNow-AI/Apriel-1.5-15b-Thinker",
        "FIRECRAWL_API_KEY": "test_firecrawl_key",
        "FIRECRAWL_API_URL": "http://localhost:3001",
        "BATCH_SIZE": "5",
        "MAX_CONCURRENT_BATCHES": "1",
        "SCRAPING_DELAY_SECONDS": "0.1"
    }

@pytest.fixture
def mock_scraping_agent():
    """Mock ScrapingAgent for testing"""
    agent = Mock()
    agent.scrape_url = AsyncMock(return_value={
        "url": "https://example.com",
        "title": "Test Resource",
        "content": "Test content",
        "source_site": "example.com"
    })
    agent.get_urls_to_scrape = AsyncMock(return_value=["https://example.com"])
    agent.perform_scraping_batch = AsyncMock(return_value=[{
        "url": "https://example.com",
        "title": "Test Resource",
        "content": "Test content",
        "source_site": "example.com"
    }])
    return agent

@pytest.fixture
def mock_classification_agent():
    """Mock ClassificationAgent for testing"""
    agent = Mock()
    agent.categorize_content = AsyncMock(return_value={
        "resource_type": "paper",
        "difficulty_level": "intermediate"
    })
    agent.process_and_store_resource = AsyncMock(return_value=Mock())
    agent.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return agent

@pytest.fixture
def mock_terminal_hub():
    """Mock TerminalHub for testing"""
    hub = Mock()
    hub.log_info = Mock()
    hub.log_progress = Mock()
    hub.log_success = Mock()
    hub.log_warning = Mock()
    hub.log_error = Mock()
    hub.start_live_display = Mock()
    hub.stop_live_display = Mock()
    return hub

@pytest.fixture
def mock_batch_processor():
    """Mock BatchProcessor for testing"""
    processor = Mock()
    processor.process_batch = AsyncMock(return_value={
        "scraped": 5,
        "classified": 5,
        "duplicates_found": 1,
        "stored": 4
    })
    return processor

@pytest.fixture
def temp_database():
    """Temporary database for testing"""
    # This would create a temporary PostgreSQL instance
    # For now, we'll use a mock
    db = Mock()
    db.connect = AsyncMock()
    db.disconnect = AsyncMock()
    db.create_tables = AsyncMock()
    db.add_resource = AsyncMock()
    db.get_resource_by_url = AsyncMock(return_value=None)
    db.query_similar_embeddings = AsyncMock(return_value=[])
    return db

@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing"""
    return {
        "resource_1": [0.1] * 1536,
        "resource_2": [0.2] * 1536,
        "resource_3": [0.9] * 1536  # Similar to resource_1
    }

@pytest.fixture
def mock_deduplication_manager():
    """Mock DeduplicationManager for testing"""
    manager = Mock()
    manager.check_and_mark_duplicate = AsyncMock(return_value=False)
    manager._generate_content_hash = Mock(return_value="test_hash_123")
    manager._generate_embedding = Mock(return_value=[0.1] * 1536)
    return manager

@pytest.fixture
def test_data_dir():
    """Temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_web_viewer():
    """Mock web viewer for testing"""
    app = Mock()
    app.get = Mock()
    app.post = Mock()
    return app

# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
