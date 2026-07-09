from fastapi.testclient import TestClient
from app.main import app
import io
from PIL import Image

client = TestClient(app)

img = Image.new('RGB', (224, 224), color='red')
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_byte_arr.seek(0)

response = client.post(
    "/api/vision/check-note",
    files={"file": ("dummy.jpg", img_byte_arr, "image/jpeg")}
)

print(f"Status: {response.status_code}")
print(f"Body: {response.json()}")
