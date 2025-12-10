from services.extraction_service import AndroidFileExtractor
import sys

# Mocking adbutils to avoid connection errors during test
import unittest.mock
sys.modules['adbutils'] = unittest.mock.MagicMock()

extractor = AndroidFileExtractor()

# Test cases
test_cases = [
    ('293,', 293),
    ('1000', 1000),
    (' 500 ', 500),
    (None, 0),
    ('invalid', 0),
    (123, 123)
]

print("Testing _safe_int...")
for input_val, expected in test_cases:
    result = extractor._safe_int(input_val)
    print(f"Input: {input_val!r} -> Output: {result!r} (Expected: {expected!r})")
    if result != expected:
        print("FAIL")
        sys.exit(1)

print("SUCCESS")
