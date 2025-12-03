import unittest
import os
import sys
import hashlib
from PIL import Image
from PIL.ExifTags import TAGS

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.metadata_extractor import MetadataExtractor

class TestMetadataExtractor(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Create a dummy text file
        self.txt_file = os.path.join(self.test_dir, "test.txt")
        self.txt_content = b"Hello World"
        with open(self.txt_file, "wb") as f:
            f.write(self.txt_content)
            
        # Create a dummy image file (no EXIF for basic test, but we check structure)
        self.img_file = os.path.join(self.test_dir, "test.jpg")
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(self.img_file)

    def tearDown(self):
        # Clean up
        if os.path.exists(self.txt_file):
            os.remove(self.txt_file)
        if os.path.exists(self.img_file):
            os.remove(self.img_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_hash_calculation(self):
        print("\nTesting Hash Calculation...")
        metadata = MetadataExtractor.get_file_metadata(self.txt_file)
        
        expected_hash = hashlib.sha256(self.txt_content).hexdigest()
        self.assertIn("hash_sha256", metadata)
        self.assertEqual(metadata["hash_sha256"], expected_hash)
        print(f"Hash Verified: {metadata['hash_sha256']}")

    def test_image_metadata_structure(self):
        print("\nTesting Image Metadata Structure...")
        metadata = MetadataExtractor.get_file_metadata(self.img_file)
        
        self.assertIn("width", metadata)
        self.assertIn("height", metadata)
        self.assertIn("hash_sha256", metadata)
        print("Image metadata structure verified.")

if __name__ == '__main__':
    unittest.main()
