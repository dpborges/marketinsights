FROM redis:8.6.5-alpine

# Persist writes to /data using Redis append-only files. The Compose service
# mounts /data as a named volume.
CMD ["redis-server", "--appendonly", "yes", "--appendfsync", "everysec", "--loglevel", "warning"]

EXPOSE 6379
