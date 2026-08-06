# Redis setup

Redis runs as a Docker Compose service for local development and caching. The image is built from
`docker/redis/Dockerfile` and uses the official `redis:8.6.5-alpine` image.

## Prerequisites

- Docker Desktop, or Docker Engine with the Docker Compose plugin
- Ports `6379` and `5432` available if starting the complete Compose stack

Confirm Docker and Compose are available:

```powershell
docker --version
docker compose version
```

## Build and initialize Redis

From the repository root, build the Redis image:

```powershell
docker compose build redis
```

Start Redis and wait for its health check:

```powershell
docker compose up -d --wait redis
```

Verify the server responds:

```powershell
docker compose exec redis redis-cli ping
```

The expected response is `PONG`.

## Connection settings

Applications running directly on the host connect with:

```text
redis://localhost:6379
```

Applications running as services in the same Compose project connect using the Compose service
name:

```text
redis://redis:6379
```

Keep the URL in environment-based application settings; do not hardcode it in source code. A
typical local variable is `REDIS_URL=redis://localhost:6379`.

## Persistence and networking

Redis append-only persistence is enabled with an `everysec` synchronization policy. Data is stored
in the `redis_data` Docker named volume and survives ordinary container recreation.

Port 6379 is published only on `127.0.0.1`, preventing access from other network hosts. The current
configuration does not require a password and is intended for local development only. Production
deployments should keep Redis on a private network and configure authentication, encryption, secret
management, backups, resource limits, and an appropriate persistence policy for the platform.
