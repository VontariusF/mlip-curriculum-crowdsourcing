"""
Simple web viewer for browsing the MLIP curriculum
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import markdown
from markdown.extensions import codehilite, fenced_code

from .database import db_manager, Resource

app = FastAPI(title="MLIP Curriculum Viewer", version="1.0.0")

# Set up templates
templates = Jinja2Templates(directory="web_viewer/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="web_viewer/static"), name="static")

# Configure markdown
md = markdown.Markdown(
    extensions=[
        'codehilite',
        'fenced_code',
        'tables',
        'toc',
        'attr_list'
    ],
    extension_configs={
        'codehilite': {
            'css_class': 'highlight'
        }
    }
)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main curriculum page"""
    session = db_manager.get_session()
    
    try:
        # Get statistics
        total_resources = session.query(Resource).count()
        
        # Get resources by type
        resource_types = {}
        for resource_type in ['paper', 'lecture', 'exercise', 'documentation', 'tutorial']:
            count = session.query(Resource).filter(Resource.resource_type == resource_type).count()
            resource_types[resource_type] = count
        
        # Get resources by difficulty
        difficulty_levels = {}
        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            count = session.query(Resource).filter(Resource.difficulty_level == difficulty).count()
            difficulty_levels[difficulty] = count
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "total_resources": total_resources,
            "resource_types": resource_types,
            "difficulty_levels": difficulty_levels
        })
    
    finally:
        session.close()

@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request, resource_type: Optional[str] = None, 
                   difficulty: Optional[str] = None, search: Optional[str] = None):
    """Browse resources with filtering"""
    session = db_manager.get_session()
    
    try:
        query = session.query(Resource)
        
        # Apply filters
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        
        if difficulty:
            query = query.filter(Resource.difficulty_level == difficulty)
        
        if search:
            query = query.filter(
                Resource.title.ilike(f"%{search}%") |
                Resource.content_markdown.ilike(f"%{search}%")
            )
        
        resources = query.order_by(Resource.scraped_at.desc()).limit(100).all()
        
        return templates.TemplateResponse("resources.html", {
            "request": request,
            "resources": resources,
            "resource_type": resource_type,
            "difficulty": difficulty,
            "search": search
        })
    
    finally:
        session.close()

@app.get("/resource/{resource_id}", response_class=HTMLResponse)
async def resource_detail(request: Request, resource_id: str):
    """View individual resource"""
    session = db_manager.get_session()
    
    try:
        resource = session.query(Resource).filter(Resource.id == resource_id).first()
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Convert markdown to HTML
        content_html = md.convert(resource.content_markdown)
        
        return templates.TemplateResponse("resource_detail.html", {
            "request": request,
            "resource": resource,
            "content_html": content_html
        })
    
    finally:
        session.close()

@app.get("/api/resources")
async def api_resources(resource_type: Optional[str] = None, 
                       difficulty: Optional[str] = None,
                       limit: int = 50):
    """API endpoint for resources"""
    session = db_manager.get_session()
    
    try:
        query = session.query(Resource)
        
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        
        if difficulty:
            query = query.filter(Resource.difficulty_level == difficulty)
        
        resources = query.order_by(Resource.scraped_at.desc()).limit(limit).all()
        
        return [
            {
                "id": str(resource.id),
                "title": resource.title,
                "url": resource.url,
                "resource_type": resource.resource_type,
                "difficulty_level": resource.difficulty_level,
                "source_site": resource.source_site,
                "scraped_at": resource.scraped_at.isoformat(),
                "topics": resource.topics
            }
            for resource in resources
        ]
    
    finally:
        session.close()

@app.get("/api/stats")
async def api_stats():
    """API endpoint for statistics"""
    session = db_manager.get_session()
    
    try:
        total_resources = session.query(Resource).count()
        
        # Resources by type
        resource_types = {}
        for resource_type in ['paper', 'lecture', 'exercise', 'documentation', 'tutorial']:
            count = session.query(Resource).filter(Resource.resource_type == resource_type).count()
            resource_types[resource_type] = count
        
        # Resources by difficulty
        difficulty_levels = {}
        for difficulty in ['beginner', 'intermediate', 'advanced', 'expert']:
            count = session.query(Resource).filter(Resource.difficulty_level == difficulty).count()
            difficulty_levels[difficulty] = count
        
        # Top sources
        top_sources = session.query(Resource.source_site).group_by(Resource.source_site).count()
        
        return {
            "total_resources": total_resources,
            "resource_types": resource_types,
            "difficulty_levels": difficulty_levels,
            "top_sources": top_sources
        }
    
    finally:
        session.close()

@app.get("/curriculum/{path:path}")
async def curriculum_files(path: str):
    """Serve curriculum markdown files"""
    curriculum_path = Path("curriculum") / path
    
    if not curriculum_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if curriculum_path.is_file() and curriculum_path.suffix == '.md':
        # Convert markdown to HTML and serve
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        html_content = md.convert(markdown_content)
        
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Curriculum - {path}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <div class="container">
                {html_content}
            </div>
        </body>
        </html>
        """)
    
    return FileResponse(curriculum_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
