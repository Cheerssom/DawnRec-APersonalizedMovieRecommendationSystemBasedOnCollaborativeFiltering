import json
from app import app

client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 43
    sess['username'] = 'gzhang'
    sess['role'] = 'user'

resp = client.get('/api/movies?search=黑豹&limit=5')
print("Search Black Panther:", resp.json)

resp = client.get('/api/recommendations/similar/36?limit=5')
print("Similar movies for 36:", resp.json)
