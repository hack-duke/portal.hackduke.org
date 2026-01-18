## Databases
- DB_NAME=hackathon for prod ... be careful with this 
- DB_NAME=test is for testing 

## To load env vars for alembic 
run command `source alembic/.env`
to check it worked:
- printenv | grep DB
    - (print env vars associated with DB)
- alembic current 
    - (prints db url, also shows what most current version is)

## To apply alembic migrations 
- `alembic upgrade head`
