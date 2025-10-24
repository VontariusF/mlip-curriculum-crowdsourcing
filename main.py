"""
Two-Agent MLIP Curriculum Crowdsourcing System
Agent 1: Scraping Agent (Llama-3.3-70B)
Agent 2: Classification Agent (Apriel-1.5-15b-Thinker)
"""
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

from src.database import db_manager
from src.scraping_agent import ScrapingAgent
from src.classification_agent import ClassificationAgent
from src.terminal_hub import TerminalHub
from src.batch_processor import BatchProcessor

load_dotenv()

@dataclass
class SystemConfig:
    """System configuration"""
    batch_size: int = int(os.getenv('BATCH_SIZE', '10'))
    max_concurrent_batches: int = int(os.getenv('MAX_CONCURRENT_BATCHES', '2'))
    scraping_delay: float = float(os.getenv('SCRAPING_DELAY_SECONDS', '2'))
    terminal_refresh_rate: float = float(os.getenv('TERMINAL_HUB_REFRESH_RATE', '1.0'))

class MLIPCurriculumSystem:
    """Main system orchestrating the two-agent workflow"""
    
    def __init__(self):
        self.config = SystemConfig()
        self.scraping_agent = ScrapingAgent()
        self.classification_agent = ClassificationAgent()
        self.terminal_hub = TerminalHub()
        self.batch_processor = BatchProcessor(self.config.batch_size)
        
        # System state
        self.is_running = False
        self.current_batch = 0
        self.total_resources_processed = 0
        self.total_duplicates_found = 0
        
    async def initialize(self):
        """Initialize the system"""
        print("🚀 Initializing MLIP Curriculum Crowdsourcing System...")
        
        # Initialize database
        await self._init_database()
        
        # Initialize agents
        await self.scraping_agent.initialize()
        await self.classification_agent.initialize()
        
        # Start terminal hub
        await self.terminal_hub.start()
        
        print("✅ System initialized successfully!")
    
    async def _init_database(self):
        """Initialize database with tables and seed data"""
        db_manager.init_database()
        
        # Initialize seed sources if not already done
        from src.scraper import MLIPScraper
        scraper = MLIPScraper()
        scraper.initialize_seed_sources()
    
    async def run_continuous_cycle(self):
        """Run the continuous batched processing cycle"""
        self.is_running = True
        
        try:
            while self.is_running:
                await self._process_next_batch()
                await asyncio.sleep(self.config.scraping_delay)
                
        except KeyboardInterrupt:
            print("\n🛑 System stopped by user")
        except Exception as e:
            print(f"❌ System error: {e}")
        finally:
            self.is_running = False
            await self.terminal_hub.stop()
    
    async def _process_next_batch(self):
        """Process the next batch of resources"""
        self.current_batch += 1
        
        # Update terminal hub
        await self.terminal_hub.update_batch_info(
            batch_number=self.current_batch,
            status="Starting batch processing"
        )
        
        try:
            # Phase 1: Scraping
            await self.terminal_hub.update_agent_status(
                agent="scraping",
                status="Discovering and scraping content",
                progress=0
            )
            
            scraped_resources = await self.scraping_agent.scrape_batch(
                batch_size=self.config.batch_size
            )
            
            await self.terminal_hub.update_agent_status(
                agent="scraping",
                status="Scraping completed",
                progress=100,
                results=len(scraped_resources)
            )
            
            if not scraped_resources:
                await self.terminal_hub.log_activity(
                    f"Batch {self.current_batch}: No resources scraped, skipping"
                )
                return
            
            # Phase 2: Classification
            await self.terminal_hub.update_agent_status(
                agent="classification",
                status="Analyzing and categorizing content",
                progress=0
            )
            
            classified_resources = await self.classification_agent.classify_batch(
                scraped_resources
            )
            
            await self.terminal_hub.update_agent_status(
                agent="classification",
                status="Classification completed",
                progress=100,
                results=len(classified_resources)
            )
            
            # Phase 3: Deduplication
            await self.terminal_hub.update_batch_info(
                status="Checking for duplicates"
            )
            
            validated_resources, duplicates = await self.batch_processor.deduplicate_batch(
                classified_resources
            )
            
            self.total_duplicates_found += len(duplicates)
            
            # Phase 4: Storage
            await self.terminal_hub.update_batch_info(
                status="Storing validated resources"
            )
            
            stored_count = await self.batch_processor.store_batch(validated_resources)
            self.total_resources_processed += stored_count
            
            # Phase 5: Reporting
            await self._report_batch_results(
                scraped=len(scraped_resources),
                classified=len(classified_resources),
                duplicates=len(duplicates),
                stored=stored_count
            )
            
        except Exception as e:
            await self.terminal_hub.log_error(f"Batch {self.current_batch} failed: {e}")
            await self.terminal_hub.update_batch_info(
                status=f"Error: {str(e)[:50]}..."
            )
    
    async def _report_batch_results(self, scraped: int, classified: int, 
                                  duplicates: int, stored: int):
        """Report batch results to terminal hub"""
        await self.terminal_hub.log_activity(
            f"Batch {self.current_batch} completed: "
            f"{scraped} scraped, {classified} classified, "
            f"{duplicates} duplicates, {stored} stored"
        )
        
        await self.terminal_hub.update_statistics(
            total_resources=self.total_resources_processed,
            total_duplicates=self.total_duplicates_found,
            current_batch=self.current_batch
        )
        
        await self.terminal_hub.update_batch_info(
            status="Batch completed successfully"
        )
    
    async def run_single_batch(self):
        """Run a single batch for testing"""
        await self.initialize()
        await self._process_next_batch()
        await self.terminal_hub.stop()
    
    def stop(self):
        """Stop the system"""
        self.is_running = False

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MLIP Curriculum Crowdsourcing System")
    parser.add_argument("command", choices=[
        "init", "single-batch", "continuous", "web"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    system = MLIPCurriculumSystem()
    
    if args.command == "init":
        await system.initialize()
        print("System initialized. Use 'single-batch' or 'continuous' to start processing.")
    
    elif args.command == "single-batch":
        await system.run_single_batch()
    
    elif args.command == "continuous":
        await system.run_continuous_cycle()
    
    elif args.command == "web":
        from src.web_viewer import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
