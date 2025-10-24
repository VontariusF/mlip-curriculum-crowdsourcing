"""
Smoke test for MLIP Curriculum Crowdsourcing System
Quick verification that all components are working
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()

def check_module_import(module_path, class_name=None):
    """Check if a module can be imported"""
    try:
        module = __import__(module_path, fromlist=[class_name] if class_name else [])
        if class_name:
            getattr(module, class_name)
        return True
    except Exception as e:
        print(f"FAILED: {module_path}.{class_name if class_name else ''} - {e}")
        return False

def check_command_exists(command):
    """Check if a command exists in PATH"""
    try:
        subprocess.run([command, '--version'], capture_output=True, check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"SUCCESS: Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"FAILED: Python {version.major}.{version.minor}.{version.micro} (requires 3.8+)")
        return False

def check_prerequisites():
    """Check all prerequisites are installed"""
    print("\nChecking prerequisites...")
    all_good = True
    
    # Check Python version
    if not check_python_version():
        all_good = False
    
    # Check Docker
    if check_command_exists('docker'):
        print("SUCCESS: Docker installed")
    else:
        print("FAILED: Docker not found - install Docker Desktop")
        all_good = False
    
    # Check Git
    if check_command_exists('git'):
        print("SUCCESS: Git installed")
    else:
        print("FAILED: Git not found - install Git")
        all_good = False
    
    # Check Node.js
    if check_command_exists('node'):
        print("SUCCESS: Node.js installed")
    else:
        print("FAILED: Node.js not found - install Node.js 18+")
        all_good = False
    
    return all_good

def check_firecrawl():
    """Check if Firecrawl is running"""
    try:
        import requests
        response = requests.get('http://localhost:3001/health', timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Firecrawl is running at http://localhost:3001")
            return True
        else:
            print(f"FAILED: Firecrawl health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"FAILED: Firecrawl not accessible - {e}")
        print("  Make sure Firecrawl is running: docker-compose up -d")
        return False

def check_environment_variables():
    """Check if required environment variables are set"""
    load_dotenv()
    
    required_vars = [
        'SCRAPING_AGENT_API_KEY',
        'CLASSIFICATION_AGENT_API_KEY',
        'FIRECRAWL_API_KEY',
        'FIRECRAWL_API_URL',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB',
        'POSTGRES_USER',
        'POSTGRES_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"FAILED: Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("SUCCESS: All required environment variables are set")
    return True

def check_database_connection():
    """Check database connection"""
    try:
        from src.database import DatabaseManager
        db_manager = DatabaseManager()
        # Try to create tables (this will test connection)
        db_manager.create_tables()
        print("SUCCESS: Database connection working")
        return True
    except Exception as e:
        print(f"FAILED: Database connection failed - {e}")
        return False

def main():
    """Run smoke test"""
    print("MLIP Curriculum Crowdsourcing System - Smoke Test")
    print("=" * 60)
    
    all_passed = True
    
    # Check prerequisites first
    if not check_prerequisites():
        all_passed = False
        print("\nWARNING: Prerequisites check failed. Please install missing software before continuing.")
    
    # Check Firecrawl
    print("\nChecking Firecrawl...")
    if not check_firecrawl():
        print("WARNING: Firecrawl not running. This is required for web scraping.")
        print("   To start Firecrawl: cd firecrawl && docker-compose up -d")
        # Don't fail the smoke test for Firecrawl issues
    
    # Check system files
    print("\nChecking system files...")
    required_files = [
        "main.py",
        "README.md",
        "requirements.txt",
        "docker-compose.yml",
        ".env",
        "src/scraping_agent.py",
        "src/classification_agent.py",
        "src/terminal_hub.py",
        "src/batch_processor.py",
        "src/database.py",
        "src/deduplication.py",
        "src/web_viewer.py",
        "src/seed_sources.json",
        "web_viewer/templates/index.html",
        "web_viewer/templates/resources.html",
        "web_viewer/templates/resource_detail.html",
        "web_viewer/static/style.css"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
            all_passed = False
        else:
            print(f"SUCCESS: {file_path}")
    
    if missing_files:
        print(f"\nMissing files: {', '.join(missing_files)}")
    
    # Check module imports
    print("\nChecking module imports...")
    module_imports = {
        "src.scraping_agent": "ScrapingAgent",
        "src.classification_agent": "ClassificationAgent",
        "src.terminal_hub": "TerminalHub",
        "src.batch_processor": "BatchProcessor",
        "src.database": "DatabaseManager",
        "src.deduplication": "DeduplicationManager",
        "src.web_viewer": "app"
    }
    
    import_success = True
    for module_path, class_name in module_imports.items():
        if not check_module_import(module_path, class_name):
            import_success = False
            all_passed = False
        else:
            print(f"SUCCESS: {module_path}.{class_name}")
    
    # Check environment variables
    print("\nChecking environment variables...")
    if not check_environment_variables():
        all_passed = False
    
    # Check database connection (optional - only if .env is properly configured)
    print("\nChecking database connection...")
    if not check_database_connection():
        print("WARNING: Database connection failed - check your .env configuration")
        print("   To start PostgreSQL: docker-compose up -d db")
        # Don't fail the smoke test for database issues
    
    # Final results
    print("\n" + "=" * 60)
    print("SMOKE TEST RESULTS")
    print("=" * 60)
    
    if all_passed:
        print("SUCCESS: All smoke tests passed!")
        print("\nSystem is ready to run. Next steps:")
        print("1. Start PostgreSQL: docker-compose up -d db")
        print("2. Initialize system: python main.py init")
        print("3. Run single batch: python main.py full-cycle")
        print("4. Run continuous: python main.py schedule")
        return True
    else:
        print("FAILED: Some smoke tests failed.")
        print("\nPlease check the errors above and fix them before proceeding.")
        print("\nCommon fixes:")
        print("- Install missing prerequisites (see README Prerequisites section)")
        print("- Set up Firecrawl: cd firecrawl && docker-compose up -d")
        print("- Start PostgreSQL: docker-compose up -d db")
        print("- Copy .env.example to .env and fill in your API keys")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
