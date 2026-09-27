import requests

base = 'http://localhost:8000/api/v1'

print('csrf request...')
r = requests.get(base + '/auth/csrf/', timeout=20)
print('csrf status', r.status_code)
print(r.text[:300])

payload = {
    'full_name': 'Test User',
    'username': 'testuserflow1',
    'email': 'testuserflow1@example.com',
    'phone': '+15551234567',
    'date_of_birth': '2004-01-01',
    'password': 'StrongPass1',
    'interests': ['strategy', 'puzzle'],
    'play_styles': ['competitive', 'casual'],
    'terms_accepted': True,
    'region': 'US',
    'age_group': '18-24',
}

print('register request...')
res = requests.post(base + '/accounts/register/', json=payload, timeout=25)
print('register status', res.status_code)
print(res.text[:1200])
