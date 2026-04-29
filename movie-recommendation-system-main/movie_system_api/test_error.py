from app import app
import json

client = app.test_client()

with client.session_transaction() as sess:
    sess['user_id'] = 1

response = client.post('/api/history', json={
    'movie_id': 'invalid_id', # This should cause an error
    'duration_watched': 0,
    'completed': False
})
print("Status:", response.status_code)
print("Response text:", response.text)
