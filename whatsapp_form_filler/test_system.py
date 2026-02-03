"""
Test script to verify all components are working.
Run this before using main.py to ensure everything is set up correctly.
"""
import sys

def test_imports():
    """Test all imports work."""
    print("🧪 Testing imports...")
    
    try:
        from config import settings
        print("  ✅ config.settings")
    except Exception as e:
        print(f"  ❌ config.settings: {e}")
        return False
    
    try:
        from database.models import FormSubmission, FieldMapping
        print("  ✅ database.models")
    except Exception as e:
        print(f"  ❌ database.models: {e}")
        return False
    
    try:
        from utils import HumanBehavior, RateLimiter, NotificationManager
        print("  ✅ utils")
    except Exception as e:
        print(f"  ❌ utils: {e}")
        return False
    
    try:
        from plugins import MicrosoftFormsPlugin
        print("  ✅ plugins")
    except Exception as e:
        print(f"  ❌ plugins: {e}")
        return False
    
    try:
        from agents import BrowserAutomationAgent, FormIntelligenceAgent
        print("  ✅ agents")
    except Exception as e:
        print(f"  ❌ agents: {e}")
        return False
    
    try:
        from orchestrator import FormFillingOrchestrator
        print("  ✅ orchestrator")
    except Exception as e:
        print(f"  ❌ orchestrator: {e}")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✅ playwright")
    except Exception as e:
        print(f"  ❌ playwright: {e}")
        return False
    
    return True


def test_config():
    """Test configuration is valid."""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import settings
        
        print(f"  Student Name: {settings.student_name}")
        print(f"  Student ID: {settings.student_id}")
        print(f"  Database Path: {settings.database_path}")
        print(f"  Logs Directory: {settings.logs_dir}")
        print(f"  Headless Mode: {settings.headless_mode}")
        print(f"  OpenAI Configured: {settings.has_openai}")
        print(f"  Telegram Configured: {settings.has_telegram}")
        
        print("  ✅ Configuration valid")
        return True
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def test_database():
    """Test database initialization."""
    print("\n🧪 Testing database...")
    
    try:
        import os
        from config import settings
        
        # Check if database exists or can be created
        db_dir = os.path.dirname(settings.database_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"  Created data directory: {db_dir}")
        
        print(f"  Database will be created at: {settings.database_path}")
        print("  ✅ Database path accessible")
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


def test_playwright():
    """Test Playwright browser launch."""
    print("\n🧪 Testing Playwright browser...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("about:blank")
            browser.close()
        
        print("  ✅ Playwright browser working")
        return True
    except Exception as e:
        print(f"  ❌ Playwright error: {e}")
        print("\n  💡 Run: .\\venv\\Scripts\\playwright.exe install chromium")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("WhatsApp Form Auto-Fill System - Component Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Database", test_database()))
    results.append(("Playwright", test_playwright()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Edit .env file with your student information")
        print("2. Run: python main.py")
        print("3. Paste a Microsoft Forms URL to test")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
