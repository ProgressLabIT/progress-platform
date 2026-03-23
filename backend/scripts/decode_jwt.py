import timeit

import jwt

TOKEN_SECRET = "change-me-use-env-var-PROGRESS_JWT_SECRET"
ALGORITHM = "HS256"


sample_jwt_data = {
  'sub': '12005319',
  'ctyp': 'User',
  'scopes': ['lib:w', 'prod:w', 'admin'],
  'iat': 1590757921717,
  'exp': 1590758221717
}


encoded_jwt = jwt.encode(sample_jwt_data, TOKEN_SECRET, algorithm=ALGORITHM)



def decode_jwt():
  jwt.decode(encoded_jwt, TOKEN_SECRET, algorithms=[ALGORITHM])


trials = timeit.repeat(decode_jwt, repeat=10, number=1000)
performance = sum(trials)/len(trials)
print(performance)