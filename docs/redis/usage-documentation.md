# Redis usage

Run these commands from the repository root.

## Start Redis

Start only Redis in the background and wait until it is healthy:

```powershell
docker compose up -d --wait redis
```

Start the complete local stack, including PostgreSQL and Redis:

```powershell
docker compose up -d --wait
```

## Stop Redis

Stop the Redis container without removing it or its data:

```powershell
docker compose stop redis
```

Stop and remove all containers and networks created by this Compose project while preserving named
volumes:

```powershell
docker compose down
```

## Other useful commands

Check service state and health:

```powershell
docker compose ps redis
```

Follow Redis logs:

```powershell
docker compose logs --follow redis
```

Test connectivity:

```powershell
docker compose exec redis redis-cli ping
```

Open an interactive Redis CLI:

```powershell
docker compose exec redis redis-cli
```

Restart only Redis:

```powershell
docker compose restart redis
```

Rebuild Redis after changing its Dockerfile, then recreate the service:

```powershell
docker compose up -d --build --wait redis
```

Display recent logs without following them:

```powershell
docker compose logs --tail 100 redis
```

Inspect the effective Compose configuration:

```powershell
docker compose config
```

Remove and recreate only the Redis container while preserving its named volume:

```powershell
docker compose rm --stop --force redis
docker compose up -d --wait redis
```

Delete the entire Compose stack **and all named-volume data**, including PostgreSQL and Redis:

```powershell
docker compose down --volumes
```

The final command is destructive and cannot be undone unless the volume data has been backed up.
