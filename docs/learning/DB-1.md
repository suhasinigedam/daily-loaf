# DB-1: Local Postgres and S3 with Docker Compose

## What I built
i have set up local database postgress and fake S3 storage on my machine using Docker.
docker-compose.yml file describes what are they.

## What I learned
- Image → like an installer: a packaged program I download once.
- Container → a running copy of an image, like an app that is open.
- Docker Compose → a file that lists several containers and starts them together.
- Volume → a storage box on my Mac where Postgres keeps data, so it is not lost.
- Healthcheck → Docker asks the database "are you ready?" and marks it healthy.
- -d → runs everything in the background, so my terminal stays free.

## Check-yourself answers
1. `docker compose down` removes the containers but keeps the volume, so my data stays.
   `down -v` also deletes the volume, so all data is gone.
2. `5432:5432` means: port 5432 on my Mac goes to port 5432 inside the container.
   Left = my Mac, right = container. Moto uses 5001:5000 because AirPlay uses 5000 on my Mac.

## What was hard / what I'd do differently
- The minio/minio image no longer exists on Docker Hub, so I switched to Moto.
- Port 5000 was busy (macOS AirPlay), so I mapped 5001 on my Mac to 5000 in the container.

## Interview line
"I run my local stack with Docker Compose — Postgres, an S3 emulator and later
Elasticsearch — so anyone can start the whole project with one command."