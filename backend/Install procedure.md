# Install procedure

1. Download and run db (arango) container
    + Generate random root password and save it in env variable
    
2. Setup blank DB by running (JS) script to create:
    * collections
    * indexes
    * standard users:
        - super admin user (Progress Lab technicians)
        - api (used by Progress APIs)
        - customer admin (???)

e.g. 
```javascript

```

3. Download and run backend (fastapi) container (see https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker)

4. Download and run frontend (nginx) container

