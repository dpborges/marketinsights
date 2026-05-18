### Description
Dockerfile (Dockerfile): A simple Dockerfile based on postgres:15 that exposes port 5432.

### docker-compose.yml set up
docker-compose.yml: Configured with a PostgreSQL service that builds from the Dockerfile, sets basic environment variables (database name, user, password), maps port 5432, and uses a persistent volume for /var/lib/postgresql/data.

### To start it:

Navigate to the project root.
- docker-compose up -d 
to start PostgreSQL in the background.'


### To stop it:
- docker-compose down

The data will persist in the postgres_data volume even if you stop and restart the container.
You can customize the database name, user, or password, edit the environment section in docker-compose.yml, as needed. 

### User accounts
USER        | PASSWORD
dbadmin     | dbadmin
mi_api_user | mp_api_user

### Following grants were provided so Alebmic can create version table in public schema when running as dbadmin
GRANT USAGE ON SCHEMA public TO dbadmin;
GRANT CREATE ON SCHEMA public TO dbadmin;

### To log in from the project root
 psql "postgresql://dbadmin:dbadmin@localhost:5432/marketinsights"

### To log into postgres marketinsights database  from project root directory
docker compose exec postgres psql -U postgres -d marketinsights

### To log in if already in the docker container shell
psql -U dbadmin -d marketinsights

### Run as the superuser in your container
docker compose exec postgres psql -U postgres -d marketinsights