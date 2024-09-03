import httpx
from api_auth_manager import APIAuthManager

client = httpx.Client()

APIAuthManager.getInstance().authenticate('http://localhost:8000', username='simone', pwd='simone')

response = client.get('http://localhost:8000/api/whoami', headers=APIAuthManager.getInstance().getAuthHeader())
print(response.json())

client.close()
