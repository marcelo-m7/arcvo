"""Test hermes chat endpoint."""
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
import json

client = TestClient(app)

# Generate admin JWT token
token = create_access_token(subject="admin", expires_minutes=60)
headers = {"Authorization": f"Bearer {token}"}

print('Testing: POST /api/v1/hermes/chat')
print('Message: "List available tools"')
print()

r = client.post(
    '/api/v1/hermes/chat',
    json={"message": "List available tools"},
    headers=headers
)

print(f'Status: {r.status_code}')
data = r.json()
print("Response (first 600 chars):")
print(json.dumps(data, indent=2)[:600])
if len(json.dumps(data, indent=2)) > 600:
    print("...")
