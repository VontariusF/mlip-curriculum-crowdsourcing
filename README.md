# MLIP Curriculum Crowdsourcing System (Two-Agent Architecture)

An open-source system that continuously scrapes and curates a comprehensive curriculum of papers, lectures, and exercises for Machine-Learned Interatomic Potentials (MLIPs). The system uses **two specialized AI agents** working in a batched processing pipeline to automatically discover, deduplicate, and categorize educational content.

## 🏗️ Two-Agent Architecture

### Agent 1: Scraping Agent (Llama-3.3-70B-Instruct-Turbo-Free)
- **Focus**: Intelligent web scraping and content discovery
- **Capabilities**: 
  - Relevance filtering using MLIP expertise
  - Content extraction and structuring
  - Link discovery and validation
  - Batch processing (10 resources per cycle)

### Agent 2: Classification Agent (ServiceNow-AI/Apriel-1.5-15b-Thinker)
- **Focus**: Document classification and semantic analysis
- **Capabilities**:
  - Deep content analysis and categorization
  - Resource type and difficulty level assignment
  - Topic extraction and metadata enrichment
  - Quality scoring and embedding generation

## 🔄 Batched Processing Pipeline

The system processes resources in controlled batches to ensure quality and prevent overwhelming:

1. **Scrape Phase**: Agent 1 scrapes batch of X resources (default: 10)
2. **Classify Phase**: Agent 2 processes all scraped items
3. **Deduplicate Phase**: System checks for duplicates and flags/removes them
4. **Store Phase**: Validated resources saved to database
5. **Report Phase**: Update terminal hub with batch results
6. **Repeat**: Move to next batch

## 📊 Real-time Terminal Hub

The system features a **Rich-based dashboard** showing:

- **Live Progress Panel**: Current batch, items processed, success rate
- **Agent Status Panel**: What each agent is currently doing
- **Statistics Panel**: Total resources, by type, by difficulty
- **Recent Activity Log**: Scrolling log of scraping/classification events
- **Duplication Report**: Flagged duplicates and removal actions
- **Error Tracking**: Failed scrapes and classification errors
- **Performance Metrics**: Processing speed, API usage, database stats

## 🔒 Security Notice

**IMPORTANT**: This repository does not contain any real API keys or secrets. All sensitive information has been removed from the Git history.

- The `.env` file is gitignored and never committed
- The `.env.example` file contains only placeholder values
- You must create your own `.env` file with your actual API credentials
- Never commit files containing real API keys or secrets

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Firecrawl running locally
- Together AI API access for both agents

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mlip-curriculum-crowdsourcing
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL with pgvector:
```bash
docker-compose up -d postgres
```

5. Initialize the system:
```bash
python main.py init
```

## 🎮 Usage Commands

### Initialize the System
```bash
python main.py init
```
Creates database tables and initializes seed sources.

### Run Single Batch (Testing)
```bash
python main.py single-batch
```
Processes one batch of resources for testing.

### Run Continuous Processing
```bash
python main.py continuous
```
Starts the continuous batched processing with real-time terminal hub.

### Start Web Viewer
```bash
python main.py web
```
Launches the web interface at `http://localhost:8000`.

## ⚙️ Configuration

### Environment Variables

```env
# Agent 1: Scraping Agent (Llama-3.3-70B)
SCRAPING_AGENT_USER_KEY=your_together_user_key
SCRAPING_AGENT_API_KEY=your_together_api_key
SCRAPING_AGENT_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free

# Agent 2: Classification Agent (Apriel-1.5-15b-Thinker)
CLASSIFICATION_AGENT_USER_KEY=your_apriel_user_key
CLASSIFICATION_AGENT_API_KEY=your_apriel_api_key
CLASSIFICATION_AGENT_MODEL=ServiceNow-AI/Apriel-1.5-15b-Thinker

# Batch Processing
BATCH_SIZE=10
MAX_CONCURRENT_BATCHES=2
SCRAPING_DELAY_SECONDS=2

# Terminal Hub
TERMINAL_HUB_REFRESH_RATE=1.0
TERMINAL_HUB_LOG_LINES=50
```

## 📚 Seed Sources

The system comes with a curated list of MLIP-focused sources:

- **arXiv**: Machine learning and computational physics papers
- **GitHub**: Popular MLIP frameworks (MACE, NequIP, SchNet, Allegro, etc.)
- **Documentation**: Framework docs and tutorials
- **Academic Sources**: University course materials
- **Community Resources**: Tutorials and educational content

## 🗂️ Content Organization

### Resource Types
- **Papers**: Academic papers and research articles
- **Lectures**: Video lectures and course materials
- **Exercises**: Hands-on exercises and coding tutorials
- **Documentation**: API docs and technical guides
- **Tutorials**: Step-by-step guides and walkthroughs

### Difficulty Levels
- **Beginner**: Introduction to concepts, basic understanding required
- **Intermediate**: Some background knowledge needed, practical applications
- **Advanced**: Deep technical knowledge required, research-level content
- **Expert**: Cutting-edge research, requires extensive domain expertise

## 🔧 System Architecture

### Core Components

- **Database**: PostgreSQL + pgvector for storage and semantic similarity
- **Scraping Pipeline**: Firecrawl + LangChain integration
- **Deduplication**: Three-tier approach (URL, hash, embeddings)
- **Terminal Hub**: Rich-based real-time monitoring
- **Web Viewer**: FastAPI-based browsing interface

### Key Features

✅ **Two-Agent Specialization**: Each agent focuses on its expertise  
✅ **Batched Processing**: Controlled, quality-focused processing  
✅ **Real-time Monitoring**: Live terminal dashboard  
✅ **Robust Deduplication**: Multi-method duplicate prevention  
✅ **Community Expandable**: Easy to add new seed sources  
✅ **Local-First Testing**: Works with local Firecrawl before scaling  

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add new seed sources or improve the system
4. Submit a pull request

### Adding New Seed Sources

Edit `src/seed_sources.json` to add new sources:

```json
{
  "url": "https://example.com",
  "source_type": "tutorial",
  "crawl_frequency": "weekly",
  "priority": 8,
  "description": "Description of the source",
  "enabled": true
}
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Firecrawl](https://firecrawl.dev/) for web scraping
- Uses [LangChain](https://langchain.com/) for document processing
- Powered by [Together AI](https://together.ai/) for both agents
- Vector similarity with [pgvector](https://github.com/pgvector/pgvector)
- Terminal UI with [Rich](https://rich.readthedocs.io/)

## 📞 Support

For questions, issues, or contributions, please open an issue on GitHub or contact the maintainers.
