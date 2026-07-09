import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.counterfeit_vision.indian_note_detector import check_indian_note
import base64

# Create a dummy image
b64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
img_bytes = base64.b64decode(b64_image)

try:
    result = check_indian_note(img_bytes)
    print("SUCCESS:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
