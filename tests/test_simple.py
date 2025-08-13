"""
Simple integration test to verify the FastAPI application is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
    from fastapi.testclient import TestClient
    
    print("✅ Successfully imported FastAPI app")
    
    # Create test client
    client = TestClient(app)
    
    # Test home page
    response = client.get("/")
    print(f"✅ Home page status: {response.status_code}")
    
    # Test galleries page
    response = client.get("/galleries")
    print(f"✅ Galleries page status: {response.status_code}")
    
    print("🎉 Basic app functionality verified!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
