import json
from app import app

client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 43
    sess['username'] = 'test_user'

resp = client.post('/api/history', json={
    'movie_id': 36,
    'duration_watched': 120,
    'completed': True
})
print("POST /api/history response:", resp.json)

resp_rating = client.post('/api/ratings', json={
    'movie_id': 36,
    'score': 5
})
print("POST /api/ratings response:", resp_rating.json)
