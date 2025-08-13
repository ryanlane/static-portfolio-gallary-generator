import pytest
import sqlite3
import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from app.main import app, get_db
from PIL import Image
import io
import json

class TestConfig:
    """Test configuration"""
    TEST_DB = 'test_gallery.db'
    TEST_STATIC_DIR = 'test_static'

@pytest.fixture
def test_client():
    """Create a test client with isolated database"""
    # Create test directories
    os.makedirs('test_static/thumbs', exist_ok=True)
    
    # Override database path for testing
    original_db_path = app.state.db_path if hasattr(app.state, 'db_path') else None
    
    def get_test_db():
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Override the dependency
    app.dependency_overrides[get_db] = get_test_db
    
    # Initialize test database
    conn = get_test_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS galleries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        featured_image_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gallery_id INTEGER,
        filename TEXT,
        title TEXT,
        description TEXT,
        camera_type TEXT,
        lens TEXT,
        settings TEXT,
        exif TEXT,
        enabled INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(gallery_id) REFERENCES galleries(id)
    )''')
    conn.commit()
    conn.close()
    
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()
    if os.path.exists(TestConfig.TEST_DB):
        os.remove(TestConfig.TEST_DB)
    if os.path.exists(TestConfig.TEST_STATIC_DIR):
        shutil.rmtree(TestConfig.TEST_STATIC_DIR)

@pytest.fixture
def sample_gallery(test_client):
    """Create a sample gallery for testing"""
    response = test_client.post("/create-gallery", data={
        "title": "Test Gallery",
        "description": "A test gallery"
    })
    assert response.status_code == 303  # Redirect after creation
    
    # Get the gallery ID from database
    conn = sqlite3.connect(TestConfig.TEST_DB)
    conn.row_factory = sqlite3.Row
    gallery = conn.execute('SELECT * FROM galleries WHERE title=?', ("Test Gallery",)).fetchone()
    conn.close()
    
    return dict(gallery)

@pytest.fixture
def sample_image():
    """Create a sample image file for testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return ("test_image.jpg", img_bytes, "image/jpeg")

class TestGalleryOperations:
    """Test gallery CRUD operations"""
    
    def test_index_page_loads(self, test_client):
        """Test that the index page loads successfully"""
        response = test_client.get("/")
        assert response.status_code == 200
        assert "Gallery" in response.text
    
    def test_create_gallery(self, test_client):
        """Test gallery creation"""
        response = test_client.post("/create-gallery", data={
            "title": "New Gallery",
            "description": "Test description"
        })
        assert response.status_code == 303  # Redirect after creation
        
        # Verify gallery was created
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        gallery = conn.execute('SELECT * FROM galleries WHERE title=?', ("New Gallery",)).fetchone()
        conn.close()
        
        assert gallery is not None
        assert gallery['title'] == "New Gallery"
        assert gallery['description'] == "Test description"
    
    def test_view_gallery(self, test_client, sample_gallery):
        """Test viewing a gallery"""
        response = test_client.get(f"/gallery/{sample_gallery['id']}")
        assert response.status_code == 200
        assert sample_gallery['title'] in response.text

class TestImageOperations:
    """Test image management operations"""
    
    def test_add_image_page(self, test_client, sample_gallery):
        """Test that add image page loads"""
        response = test_client.get(f"/gallery/{sample_gallery['id']}/add-image")
        assert response.status_code == 200
        assert "Add Image" in response.text or "upload" in response.text.lower()
    
    def test_upload_multiple_images(self, test_client, sample_gallery, sample_image):
        """Test multiple image upload"""
        filename, file_data, content_type = sample_image
        
        # Create test directories
        os.makedirs(f'static/gallery_{sample_gallery["id"]}', exist_ok=True)
        os.makedirs('static/thumbs', exist_ok=True)
        
        files = [("files", (filename, file_data, content_type))]
        
        response = test_client.post(
            f"/gallery/{sample_gallery['id']}/upload-multiple",
            files=files
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["success"] is True
    
    def test_toggle_image_enabled(self, test_client, sample_gallery):
        """Test toggling image enabled status"""
        # First create an image
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, enabled, sort_order) 
                      VALUES (?, ?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Test Image', 1, 0))
        image_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Test toggle
        response = test_client.post(f"/image/{image_id}/toggle-enabled")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert result["enabled"] is False  # Should be disabled after toggle
        
        # Verify in database
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        image = conn.execute('SELECT * FROM images WHERE id=?', (image_id,)).fetchone()
        conn.close()
        
        assert image['enabled'] == 0
    
    def test_update_image_metadata(self, test_client, sample_gallery):
        """Test updating image metadata"""
        # Create an image
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                      VALUES (?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Original Title', 0))
        image_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Update metadata
        response = test_client.post(f"/image/{image_id}/update", data={
            "title": "Updated Title",
            "description": "New description",
            "camera_type": "Canon EOS R5",
            "lens": "24-70mm",
            "settings": "f/2.8, 1/250s, ISO 400"
        })
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # Verify update
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        image = conn.execute('SELECT * FROM images WHERE id=?', (image_id,)).fetchone()
        conn.close()
        
        assert image['title'] == "Updated Title"
        assert image['description'] == "New description"
        assert image['camera_type'] == "Canon EOS R5"
    
    def test_delete_image(self, test_client, sample_gallery):
        """Test deleting an image"""
        # Create an image
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                      VALUES (?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Test Image', 0))
        image_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Delete image
        response = test_client.post(f"/image/{image_id}/delete")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # Verify deletion
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        image = conn.execute('SELECT * FROM images WHERE id=?', (image_id,)).fetchone()
        conn.close()
        
        assert image is None

class TestFeaturedImages:
    """Test featured image functionality"""
    
    def test_set_featured_image(self, test_client, sample_gallery):
        """Test setting an image as featured"""
        # Create an image
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                      VALUES (?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Test Image', 0))
        image_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Set as featured
        response = test_client.post(f"/gallery/{sample_gallery['id']}/set-featured/{image_id}")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # Verify in database
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        gallery = conn.execute('SELECT * FROM galleries WHERE id=?', (sample_gallery['id'],)).fetchone()
        conn.close()
        
        assert gallery['featured_image_id'] == image_id
    
    def test_remove_featured_image(self, test_client, sample_gallery):
        """Test removing featured image status"""
        # Create and set featured image
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                      VALUES (?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Test Image', 0))
        image_id = cur.lastrowid
        cur.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', 
                   (image_id, sample_gallery['id']))
        conn.commit()
        conn.close()
        
        # Remove featured status
        response = test_client.post(f"/gallery/{sample_gallery['id']}/remove-featured")
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        
        # Verify removal
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        gallery = conn.execute('SELECT * FROM galleries WHERE id=?', (sample_gallery['id'],)).fetchone()
        conn.close()
        
        assert gallery['featured_image_id'] is None

class TestImageOrdering:
    """Test drag and drop image ordering"""
    
    def test_reorder_images(self, test_client, sample_gallery):
        """Test reordering images"""
        # Create multiple images
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        
        image_ids = []
        for i in range(3):
            cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                          VALUES (?, ?, ?, ?)''',
                       (sample_gallery['id'], f'test{i}.jpg', f'Image {i}', i))
            image_ids.append(cur.lastrowid)
        
        conn.commit()
        conn.close()
        
        # Reorder: reverse the order
        new_order = [
            {"id": image_ids[2], "sort_order": 0},
            {"id": image_ids[1], "sort_order": 1},
            {"id": image_ids[0], "sort_order": 2}
        ]
        
        response = test_client.post(
            f"/gallery/{sample_gallery['id']}/reorder",
            json={"image_order": new_order}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        
        # Verify new order
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        images = conn.execute(
            'SELECT * FROM images WHERE gallery_id=? ORDER BY sort_order ASC',
            (sample_gallery['id'],)
        ).fetchall()
        conn.close()
        
        assert len(images) == 3
        assert images[0]['id'] == image_ids[2]  # Last should be first
        assert images[1]['id'] == image_ids[1]  # Middle stays middle
        assert images[2]['id'] == image_ids[0]  # First should be last

class TestSettings:
    """Test settings and admin functionality"""
    
    def test_settings_page(self, test_client):
        """Test settings page loads"""
        response = test_client.get("/settings")
        assert response.status_code == 200
        assert "Settings" in response.text
    
    def test_database_reset(self, test_client, sample_gallery):
        """Test database reset functionality"""
        # Create some data first
        conn = sqlite3.connect(TestConfig.TEST_DB)
        cur = conn.cursor()
        cur.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                      VALUES (?, ?, ?, ?)''',
                   (sample_gallery['id'], 'test.jpg', 'Test Image', 0))
        conn.commit()
        conn.close()
        
        # Reset database
        response = test_client.post("/settings/reset")
        assert response.status_code == 303  # Redirect after reset
        
        # Verify data is gone
        conn = sqlite3.connect(TestConfig.TEST_DB)
        conn.row_factory = sqlite3.Row
        galleries = conn.execute('SELECT * FROM galleries').fetchall()
        images = conn.execute('SELECT * FROM images').fetchall()
        conn.close()
        
        assert len(galleries) == 0
        assert len(images) == 0

class TestErrorHandling:
    """Test error conditions and edge cases"""
    
    def test_nonexistent_gallery(self, test_client):
        """Test accessing nonexistent gallery"""
        response = test_client.get("/gallery/99999")
        # Should handle gracefully, may return 200 with empty content or 404
        assert response.status_code in [200, 404]
    
    def test_invalid_image_operations(self, test_client):
        """Test operations on nonexistent images"""
        # Toggle nonexistent image
        response = test_client.post("/image/99999/toggle-enabled")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
        
        # Delete nonexistent image
        response = test_client.post("/image/99999/delete")
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
    
    def test_invalid_reorder_data(self, test_client, sample_gallery):
        """Test reordering with invalid data"""
        response = test_client.post(
            f"/gallery/{sample_gallery['id']}/reorder",
            json={"invalid": "data"}
        )
        assert response.status_code == 200
        # Should handle gracefully even with invalid data

if __name__ == "__main__":
    pytest.main([__file__])
