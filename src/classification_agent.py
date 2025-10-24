"""
Classification Agent - ServiceNow-AI/Apriel-1.5-15b-Thinker
Specialized in document classification and semantic analysis
"""
import os
import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
from langchain_together import ChatTogether
from langchain.schema import HumanMessage, SystemMessage
from sentence_transformers import SentenceTransformer
import numpy as np

@dataclass
class ClassifiedResource:
    """Represents a classified resource"""
    url: str
    title: str
    content: str
    markdown: str
    source_site: str
    resource_type: str
    difficulty_level: str
    topics: List[str]
    quality_score: float
    embedding: np.ndarray
    metadata: Dict

class ClassificationAgent:
    """Agent 2: Deep document analysis and categorization"""
    
    def __init__(self):
        self.model = ChatTogether(
            model=os.getenv('CLASSIFICATION_AGENT_MODEL', 'ServiceNow-AI/Apriel-1.5-15b-Thinker'),
            together_api_key=os.getenv('CLASSIFICATION_AGENT_API_KEY'),
            temperature=0.1
        )
        
        self.embedding_model = SentenceTransformer(
            os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
        )
    
    async def initialize(self):
        """Initialize the classification agent"""
        print("🧠 Initializing Classification Agent (Apriel-1.5-15b-Thinker)...")
        
        # Load embedding model
        print("Loading embedding model...")
        await asyncio.get_event_loop().run_in_executor(
            None, self.embedding_model.encode, "test"
        )
        
        print("✅ Classification Agent initialized")
    
    async def classify_batch(self, resources: List) -> List[ClassifiedResource]:
        """Classify a batch of scraped resources"""
        classified_resources = []
        
        for resource in resources:
            try:
                classified_resource = await self._classify_resource(resource)
                if classified_resource:
                    classified_resources.append(classified_resource)
                
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error classifying resource {resource.url}: {e}")
                continue
        
        return classified_resources
    
    async def _classify_resource(self, resource) -> Optional[ClassifiedResource]:
        """Classify a single resource"""
        try:
            # Generate classification
            classification = await self._generate_classification(
                resource.title, resource.content, resource.url
            )
            
            # Generate embedding
            embedding = await self._generate_embedding(resource.content)
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                resource.content, classification
            )
            
            return ClassifiedResource(
                url=resource.url,
                title=resource.title,
                content=resource.content,
                markdown=resource.markdown,
                source_site=resource.source_site,
                resource_type=classification['resource_type'],
                difficulty_level=classification['difficulty_level'],
                topics=classification['topics'],
                quality_score=quality_score,
                embedding=embedding,
                metadata={
                    'relevance_score': resource.relevance_score,
                    'source_metadata': resource.metadata,
                    'classified_at': asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            print(f"Error classifying resource: {e}")
            return None
    
    async def _generate_classification(self, title: str, content: str, url: str) -> Dict:
        """Generate classification using LLM"""
        system_prompt = """
        You are an expert in Machine-Learned Interatomic Potentials (MLIPs) and educational content analysis.
        Your task is to classify educational content for MLIP curriculum development.

        Analyze the given content and classify it according to:
        1. Resource type (paper, lecture, exercise, documentation, tutorial)
        2. Difficulty level (beginner, intermediate, advanced, expert)
        3. Relevant topics (list of specific MLIP-related topics)

        Resource types:
        - paper: Academic papers, research articles, preprints, conference proceedings
        - lecture: Video lectures, course materials, presentations, slides
        - exercise: Hands-on exercises, coding tutorials, practical work, assignments
        - documentation: API docs, software documentation, technical guides, manuals
        - tutorial: Step-by-step guides, how-to articles, walkthroughs, getting started

        Difficulty levels:
        - beginner: Introduction to concepts, basic understanding required, accessible to newcomers
        - intermediate: Some background knowledge needed, practical applications, moderate complexity
        - advanced: Deep technical knowledge required, research-level content, complex implementations
        - expert: Cutting-edge research, requires extensive domain expertise, novel methodologies

        Topics should include specific MLIP-related terms such as:
        - equivariant neural networks, graph neural networks, message passing
        - force fields, interatomic potentials, molecular dynamics
        - DFT, ab-initio calculations, quantum mechanics
        - MACE, NequIP, SchNet, Allegro, CHGNet (specific frameworks)
        - materials properties, crystal structures, phase transitions
        - training data, datasets, benchmarks, evaluation metrics
        - And other relevant technical topics

        Respond with a JSON object containing exactly these fields:
        {
            "resource_type": "one of the resource types above",
            "difficulty_level": "one of the difficulty levels above",
            "topics": ["list", "of", "relevant", "topics"]
        }
        """
        
        # Truncate content if too long
        content_preview = content[:2000] + "..." if len(content) > 2000 else content
        
        human_prompt = f"""
        Please classify this content:

        Title: {title}
        URL: {url}
        Content: {content_preview}

        Respond with the JSON object as specified in the system prompt.
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            response = self.model(messages)
            response_text = response.content.strip()
            
            # Try to extract JSON from response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Parse JSON response
            classification = json.loads(response_text)
            
            # Validate response format
            required_fields = ['resource_type', 'difficulty_level', 'topics']
            if not all(field in classification for field in required_fields):
                raise ValueError("Missing required fields in classification")
            
            return classification
            
        except Exception as e:
            # Fallback classification
            return self._fallback_classification(title, url, str(e))
    
    def _fallback_classification(self, title: str, url: str, error: str) -> Dict:
        """Fallback classification when LLM fails"""
        
        # Simple heuristics for resource type
        if 'arxiv.org' in url or 'paper' in title.lower():
            resource_type = 'paper'
        elif 'youtube.com' in url or 'lecture' in title.lower():
            resource_type = 'lecture'
        elif 'github.com' in url and ('tutorial' in title.lower() or 'example' in title.lower()):
            resource_type = 'exercise'
        elif 'docs' in url or 'documentation' in title.lower():
            resource_type = 'documentation'
        else:
            resource_type = 'tutorial'
        
        # Simple heuristics for difficulty
        if any(word in title.lower() for word in ['introduction', 'getting started', 'basics']):
            difficulty_level = 'beginner'
        elif any(word in title.lower() for word in ['advanced', 'expert', 'research']):
            difficulty_level = 'advanced'
        else:
            difficulty_level = 'intermediate'
        
        # Basic topics
        topics = ['machine learning', 'interatomic potentials']
        
        return {
            'resource_type': resource_type,
            'difficulty_level': difficulty_level,
            'topics': topics
        }
    
    async def _generate_embedding(self, content: str) -> np.ndarray:
        """Generate embedding for content"""
        # Use title + first 1000 characters for embedding
        embedding_text = content[:1000]
        
        # Run in executor to avoid blocking
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self.embedding_model.encode, embedding_text
        )
        
        return embedding
    
    async def _calculate_quality_score(self, content: str, classification: Dict) -> float:
        """Calculate quality score for the resource"""
        score = 0.5  # Base score
        
        # Length factor
        if len(content) > 1000:
            score += 0.1
        elif len(content) < 200:
            score -= 0.2
        
        # Resource type factor
        type_scores = {
            'paper': 0.9,
            'lecture': 0.8,
            'tutorial': 0.7,
            'exercise': 0.6,
            'documentation': 0.5
        }
        score += type_scores.get(classification['resource_type'], 0.5) * 0.2
        
        # Topics factor
        topic_count = len(classification['topics'])
        if topic_count > 3:
            score += 0.1
        elif topic_count < 2:
            score -= 0.1
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))
    
    async def batch_classify(self, content_list: List[Dict]) -> List[Dict]:
        """Classify multiple pieces of content"""
        results = []
        
        for content_item in content_list:
            try:
                classification = await self._generate_classification(
                    content_item['title'],
                    content_item['content'],
                    content_item['url']
                )
                results.append({
                    'id': content_item['id'],
                    'classification': classification
                })
            except Exception as e:
                # Log error and continue with next item
                print(f"Error classifying content {content_item['id']}: {e}")
                results.append({
                    'id': content_item['id'],
                    'classification': self._fallback_classification(
                        content_item['title'],
                        content_item['url'],
                        str(e)
                    )
                })
        
        return results
