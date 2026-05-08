### Description
Dockerfile (Dockerfile): A simple Dockerfile based on postgres:15 that exposes port 5432.

### docker-compose.yml set up
docker-compose.yml: Configured with a PostgreSQL service that builds from the Dockerfile, sets basic environment variables (database name, user, password), maps port 5432, and uses a persistent volume for /var/lib/postgresql/data.

### To start it:

Navigate to the project root.
- Run docker-compose up -d 
to start PostgreSQL in the background.'

### To stop it:
- docker-compose down

The data will persist in the postgres_data volume even if you stop and restart the container.
You can customize the database name, user, or password, edit the environment section in docker-compose.yml, as needed. 