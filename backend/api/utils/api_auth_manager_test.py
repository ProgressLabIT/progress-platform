import httpx
from api_auth_manager import APIAuthManager

client = httpx.Client()

#APIAuthManager.getInstance().authenticate('http://localhost:8000', username='simone', pwd='simone')
APIAuthManager.getInstance().setAPIToken('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiYTU5ZWFlMjAxYTkiLCJzdWIiOiIyOTIxMjQxNCIsImN0eXAiOiJ1c2VyIiwiaWF0IjoxNzI3NzA1NDU3LCJleHAiOjQ4ODM0NjU0NTcsImN0eCI6InNlc3Npb24ifQ.TUwe9KPFG6Zn31TlO0i8XMqNK23hk-IKAYhv7EG5AxA')

response = client.get('http://localhost:8000/api/whoami', headers=APIAuthManager.getInstance().getAuthHeader())
print(response.json())

client.close()
