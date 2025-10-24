"""
Scraping Agent - Llama-3.3-70B-Instruct-Turbo-Free
Specialized in intelligent web scraping and content discovery
"""
import os
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain_together import ChatTogether
from langchain.schema import HumanMessage, SystemMessage
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

@dataclass
class ScrapedResource:
    """Represents a scraped resource"""
    url: str
    title: str
    content: str
    markdown: str
    source_site: str
    relevance_score: float
    metadata: Dict

class ScrapingAgent:
    """Agent 1: Intelligent scraping and content discovery"""
    
    def __init__(self):
        self.model = ChatTogether(
            model=os.getenv('SCRAPING_AGENT_MODEL', 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free'),
            together_api_key=os.getenv('SCRAPING_AGENT_API_KEY'),
            temperature=0.1
        )
        
        self.firecrawl_app = FirecrawlApp(
            api_key=os.getenv('FIRECRAWL_API_KEY'),
            base_url=os.getenv('FIRECRAWL_API_URL', 'http://localhost:3001')
        )
        
        self.seed_sources = self._load_seed_sources()
        self.scraped_urls = set()
    
    async def initialize(self):
        """Initialize the scraping agent"""
        print("🔍 Initializing Scraping Agent (Llama-3.3-70B)...")
        
        # Load seed sources
        await self._load_seed_sources()
        
        print("✅ Scraping Agent initialized")
    
    def _load_seed_sources(self) -> List[Dict]:
        """Load seed sources for scraping"""
        import json
        
        try:
            with open('src/seed_sources.json', 'r') as f:
                data = json.load(f)
            return data['seed_sources']
        except FileNotFoundError:
            # Return default seed sources if file doesn't exist
            return [
                {
                    "url": "https://arxiv.org/list/cs.LG/recent",
                    "source_type": "arxiv",
                    "crawl_frequency": "daily",
                    "priority": 8,
                    "description": "Machine Learning papers from arXiv",
                    "enabled": True
                },
                {
                    "url": "https://github.com/ACEsuit/mace",
                    "source_type": "github",
                    "crawl_frequency": "weekly",
                    "priority": 10,
                    "description": "MACE framework",
                    "enabled": True
                }
            ]
    
    async def scrape_batch(self, batch_size: int = 10) -> List[ScrapedResource]:
        """Scrape a batch of resources"""
        resources = []
        
        for source in self.seed_sources[:batch_size]:
            if not source.get('enabled', True):
                continue
                
            try:
                # Check if we've already scraped this URL
                if source['url'] in self.scraped_urls:
                    continue
                
                # Scrape the source
                resource = await self._scrape_source(source)
                if resource:
                    resources.append(resource)
                    self.scraped_urls.add(source['url'])
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error scraping {source['url']}: {e}")
                continue
        
        return resources
    
    async def _scrape_source(self, source: Dict) -> Optional[ScrapedResource]:
        """Scrape a single source"""
        url = source['url']
        
        try:
            # Use Firecrawl to scrape
            scrape_result = self.firecrawl_app.scrape_url(
                url,
                params={
                    'formats': ['markdown', 'html'],
                    'onlyMainContent': True,
                    'maxAge': 86400
                }
            )
            
            if not scrape_result or not scrape_result.get('success'):
                return None
            
            data = scrape_result['data']
            content = data.get('markdown', '')
            
            # Use LLM to assess relevance
            relevance_score = await self._assess_relevance(content, url)
            
            if relevance_score < 0.5:  # Threshold for MLIP relevance
                return None
            
            # Extract additional links
            additional_links = self._extract_relevant_links(data.get('html', ''), url)
            
            return ScrapedResource(
                url=url,
                title=data.get('metadata', {}).get('title', ''),
                content=content,
                markdown=content,
                source_site=urlparse(url).netloc,
                relevance_score=relevance_score,
                metadata={
                    'source_type': source.get('source_type', 'unknown'),
                    'priority': source.get('priority', 1),
                    'additional_links': additional_links,
                    'scraped_at': asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    async def _assess_relevance(self, content: str, url: str) -> float:
        """Use LLM to assess MLIP relevance of content"""
        system_prompt = """
        You are an expert in Machine-Learned Interatomic Potentials (MLIPs) and computational materials science.
        Your task is to assess the relevance of web content to MLIP education and research.

        Rate the relevance on a scale of 0.0 to 1.0 where:
        - 1.0 = Highly relevant (direct MLIP content, tutorials, papers)
        - 0.8 = Very relevant (related frameworks, computational materials science)
        - 0.6 = Moderately relevant (general ML, materials science)
        - 0.4 = Somewhat relevant (tangential topics)
        - 0.2 = Barely relevant (minimal connection)
        - 0.0 = Not relevant (unrelated content)

        Consider these MLIP-related topics:
        - Interatomic potentials, force fields, molecular dynamics
        - Neural network potentials, graph neural networks
        - MACE, NequIP, SchNet, Allegro, CHGNet frameworks
        - DFT, ab-initio calculations, quantum mechanics
        - Materials properties, crystal structures
        - Training data, datasets, benchmarks

        Respond with only a number between 0.0 and 1.0.
        """
        
        human_prompt = f"""
        Assess the relevance of this content to MLIP education:

        URL: {url}
        Content: {content[:1000]}...

        Relevance score (0.0-1.0):
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.model(messages)
            score_text = response.content.strip()
            
            # Extract numeric score
            try:
                score = float(score_text)
                return max(0.0, min(1.0, score))  # Clamp to [0, 1]
            except ValueError:
                # Fallback scoring based on keywords
                return self._fallback_relevance_score(content)
                
        except Exception as e:
            print(f"Error assessing relevance: {e}")
            return self._fallback_relevance_score(content)
    
    def _fallback_relevance_score(self, content: str) -> float:
        """Fallback relevance scoring based on keywords"""
        mlip_keywords = [
            'interatomic potential', 'force field', 'molecular dynamics',
            'neural network potential', 'graph neural network', 'mace',
            'nequip', 'schnet', 'allegro', 'chgnet', 'dft', 'ab-initio',
            'materials science', 'crystal structure', 'atomistic simulation'
        ]
        
        content_lower = content.lower()
        keyword_count = sum(1 for keyword in mlip_keywords if keyword in content_lower)
        
        # Normalize to 0-1 scale
        return min(1.0, keyword_count / 5.0)
    
    def _extract_relevant_links(self, html: str, base_url: str) -> List[str]:
        """Extract relevant links from HTML content"""
        links = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(base_url, href)
                
                # Filter for relevant links
                if self._is_relevant_link(full_url):
                    links.append(full_url)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            print(f"Error extracting links: {e}")
            return []
    
    def _is_relevant_link(self, url: str) -> bool:
        """Check if a link is relevant to MLIP"""
        relevant_domains = [
            'arxiv.org', 'github.com', 'materialsproject.org',
            'nomad-coe.eu', 'youtube.com', 'scholar.google.com'
        ]
        
        relevant_keywords = [
            'interatomic', 'potential', 'force-field', 'mace', 'nequip',
            'schnet', 'allegro', 'molecular-dynamics', 'dft', 'ab-initio'
        ]
        
        url_lower = url.lower()
        
        # Check domain
        if any(domain in url_lower for domain in relevant_domains):
            return True
        
        # Check keywords
        if any(keyword in url_lower for keyword in relevant_keywords):
            return True
        
        return False
