import httpx
from api_auth_manager import APIAuthManager

client = httpx.Client()

#APIAuthManager.getInstance().authenticate('http://localhost:8000', username='simone', pwd='simone')
APIAuthManager.getInstance().setAPIToken('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyMzBiZTNkZGQ4ZDYiLCJzdWIiOiIyOTY4MjYxMyIsImN0eXAiOiJ1c2VyIiwiaWF0IjoxNzI3ODg5NTQ3LCJleHAiOjE3NjA0ODY0MDAsImN0eCI6InNlc3Npb24ifQ.YzZ4cIY91Wm3E8YdMxcCJ5IxErJG-BPSx7ctDGuDEWs')

response = client.get('http://localhost:8000/api/whoami', headers=APIAuthManager.getInstance().getAuthHeader())
print(response.json())

client.close()
