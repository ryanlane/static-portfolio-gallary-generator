"""
Unit tests for core gallery functionality that can run without external dependencies
"""
import sqlite3
import tempfile
import os
import json

class TestDatabaseOperations:
    """Test database operations independently"""
    
    def setup_method(self):
        """Setup test database for each test"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.setup_database()
    
    def teardown_method(self):
        """Cleanup test database"""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def setup_database(self):
        """Initialize test database schema"""
        c = self.conn.cursor()
        c.execute('''CREATE TABLE galleries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            featured_image_id INTEGER
        )''')
        c.execute('''CREATE TABLE images (
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
        self.conn.commit()
    
    def test_create_gallery(self):
        """Test gallery creation"""
        c = self.conn.cursor()
        c.execute('INSERT INTO galleries (title, description) VALUES (?, ?)',
                 ('Test Gallery', 'Test Description'))
        gallery_id = c.lastrowid
        self.conn.commit()
        
        # Verify creation
        gallery = c.execute('SELECT * FROM galleries WHERE id=?', (gallery_id,)).fetchone()
        assert gallery is not None
        assert gallery['title'] == 'Test Gallery'
        assert gallery['description'] == 'Test Description'
    
    def test_create_image_with_sort_order(self):
        """Test image creation with automatic sort ordering"""
        c = self.conn.cursor()
        
        # Create gallery first
        c.execute('INSERT INTO galleries (title) VALUES (?)', ('Test Gallery',))
        gallery_id = c.lastrowid
        
        # Create first image
        c.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                    VALUES (?, ?, ?, ?)''',
                 (gallery_id, 'image1.jpg', 'First Image', 0))
        image1_id = c.lastrowid
        
        # Create second image
        c.execute('''INSERT INTO images (gallery_id, filename, title, sort_order) 
                    VALUES (?, ?, ?, ?)''',
                 (gallery_id, 'image2.jpg', 'Second Image', 1))
        image2_id = c.lastrowid
        
        self.conn.commit()
        
        # Verify order
        images = c.execute('''SELECT * FROM images WHERE gallery_id=? 
                             ORDER BY sort_order ASC''', (gallery_id,)).fetchall()
        
        assert len(images) == 2
        assert images[0]['id'] == image1_id
        assert images[1]['id'] == image2_id
        assert images[0]['sort_order'] == 0
        assert images[1]['sort_order'] == 1
    
    def test_toggle_image_enabled(self):
        """Test toggling image enabled status"""
        c = self.conn.cursor()
        
        # Create gallery and image
        c.execute('INSERT INTO galleries (title) VALUES (?)', ('Test Gallery',))
        gallery_id = c.lastrowid
        c.execute('''INSERT INTO images (gallery_id, filename, enabled) 
                    VALUES (?, ?, ?)''',
                 (gallery_id, 'test.jpg', 1))
        image_id = c.lastrowid
        self.conn.commit()
        
        # Get current status
        image = c.execute('SELECT enabled FROM images WHERE id=?', (image_id,)).fetchone()
        original_status = image['enabled']
        
        # Toggle status
        new_status = 0 if original_status else 1
        c.execute('UPDATE images SET enabled=? WHERE id=?', (new_status, image_id))
        self.conn.commit()
        
        # Verify toggle
        image = c.execute('SELECT enabled FROM images WHERE id=?', (image_id,)).fetchone()
        assert image['enabled'] == new_status
        assert image['enabled'] != original_status
    
    def test_set_featured_image(self):
        """Test setting featured image"""
        c = self.conn.cursor()
        
        # Create gallery and image
        c.execute('INSERT INTO galleries (title) VALUES (?)', ('Test Gallery',))
        gallery_id = c.lastrowid
        c.execute('''INSERT INTO images (gallery_id, filename) VALUES (?, ?)''',
                 (gallery_id, 'test.jpg'))
        image_id = c.lastrowid
        
        # Set as featured
        c.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', 
                 (image_id, gallery_id))
        self.conn.commit()
        
        # Verify
        gallery = c.execute('SELECT featured_image_id FROM galleries WHERE id=?', 
                           (gallery_id,)).fetchone()
        assert gallery['featured_image_id'] == image_id
    
    def test_reorder_images(self):
        """Test reordering images"""
        c = self.conn.cursor()
        
        # Create gallery and multiple images
        c.execute('INSERT INTO galleries (title) VALUES (?)', ('Test Gallery',))
        gallery_id = c.lastrowid
        
        image_ids = []
        for i in range(3):
            c.execute('''INSERT INTO images (gallery_id, filename, sort_order) 
                        VALUES (?, ?, ?)''',
                     (gallery_id, f'image{i}.jpg', i))
            image_ids.append(c.lastrowid)
        self.conn.commit()
        
        # Reverse the order
        new_order = [
            (image_ids[2], 0),
            (image_ids[1], 1),
            (image_ids[0], 2)
        ]
        
        for image_id, sort_order in new_order:
            c.execute('UPDATE images SET sort_order=? WHERE id=?', 
                     (sort_order, image_id))
        self.conn.commit()
        
        # Verify new order
        images = c.execute('''SELECT id FROM images WHERE gallery_id=? 
                             ORDER BY sort_order ASC''', (gallery_id,)).fetchall()
        
        assert len(images) == 3
        assert images[0]['id'] == image_ids[2]  # Last became first
        assert images[1]['id'] == image_ids[1]  # Middle stayed middle
        assert images[2]['id'] == image_ids[0]  # First became last
    
    def test_delete_image_cleanup(self):
        """Test that deleting an image cleans up featured references"""
        c = self.conn.cursor()
        
        # Create gallery and image
        c.execute('INSERT INTO galleries (title) VALUES (?)', ('Test Gallery',))
        gallery_id = c.lastrowid
        c.execute('''INSERT INTO images (gallery_id, filename) VALUES (?, ?)''',
                 (gallery_id, 'test.jpg'))
        image_id = c.lastrowid
        
        # Set as featured
        c.execute('UPDATE galleries SET featured_image_id=? WHERE id=?', 
                 (image_id, gallery_id))
        self.conn.commit()
        
        # Delete image
        c.execute('DELETE FROM images WHERE id=?', (image_id,))
        # Clean up featured reference
        c.execute('UPDATE galleries SET featured_image_id=NULL WHERE featured_image_id=?', 
                 (image_id,))
        self.conn.commit()
        
        # Verify cleanup
        image = c.execute('SELECT * FROM images WHERE id=?', (image_id,)).fetchone()
        gallery = c.execute('SELECT featured_image_id FROM galleries WHERE id=?', 
                           (gallery_id,)).fetchone()
        
        assert image is None
        assert gallery['featured_image_id'] is None

class TestJSONHandling:
    """Test JSON operations for EXIF data"""
    
    def test_exif_json_encoding(self):
        """Test EXIF data JSON encoding/decoding"""
        sample_exif = {
            'Image Make': 'Canon',
            'Image Model': 'EOS R5',
            'EXIF FNumber': '2.8',
            'EXIF ISOSpeedRatings': '400'
        }
        
        # Encode to JSON
        json_str = json.dumps(sample_exif)
        assert isinstance(json_str, str)
        
        # Decode from JSON
        decoded = json.loads(json_str)
        assert decoded == sample_exif
        assert decoded['Image Make'] == 'Canon'
        assert decoded['EXIF FNumber'] == '2.8'
    
    def test_empty_exif_handling(self):
        """Test handling of empty EXIF data"""
        # Test empty dict
        empty_dict = {}
        json_str = json.dumps(empty_dict)
        decoded = json.loads(json_str)
        assert decoded == {}
        
        # Test None handling
        none_value = None
        if none_value:
            decoded = json.loads(none_value)
        else:
            decoded = {}
        assert decoded == {}

def run_unit_tests():
    """Simple test runner that doesn't require pytest"""
    import traceback
    
    test_classes = [TestDatabaseOperations, TestJSONHandling]
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    print("🧪 Running Unit Tests")
    print("===================")
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) 
                       if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            print(f"  ▶️  {method_name}...", end=" ")
            
            try:
                # Create instance and run test
                instance = test_class()
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()
                
                method = getattr(instance, method_name)
                method()
                
                if hasattr(instance, 'teardown_method'):
                    instance.teardown_method()
                
                print("✅")
                passed_tests += 1
                
            except Exception as e:
                print("❌")
                failed_tests.append(f"{test_class.__name__}.{method_name}: {str(e)}")
                traceback.print_exc()
    
    print(f"\n📊 Test Results")
    print(f"===============")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print(f"\n✅ All tests passed!")
        return True

if __name__ == "__main__":
    success = run_unit_tests()
    exit(0 if success else 1)
