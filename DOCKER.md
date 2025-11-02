# Docker Deployment Guide

This guide explains how to run Castersugar using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, but recommended)

## Quick Start with Docker Compose

The easiest way to run Castersugar is using Docker Compose:

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start the container in the background
- Expose the application on port 5005

Access the application at: http://localhost:5005

## Building the Docker Image Manually

If you prefer to build and run manually:

```bash
# Build the image
docker build -t castersugar .

# Run the container
docker run -d \
  --name castersugar \
  --network host \
  -p 5005:5005 \
  castersugar
```

## Important Notes

### Network Mode

The docker-compose.yml uses `network_mode: host` to ensure the container can:
- Discover Chromecast devices on your local network
- Communicate with Chromecast devices
- Access local DynamoDB (if running locally)

If you don't need Chromecast discovery or prefer network isolation, you can:
1. Remove the `network_mode: host` line
2. Keep only the `ports` mapping

### Environment Variables

You can pass environment variables to configure the application:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  # Add other environment variables here
```

## Development Mode

For development, you can mount your local code into the container:

Uncomment the volume mounts in `docker-compose.yml`:

```yaml
volumes:
  - ./app:/app/app
  - ./main.py:/app/main.py
```

Then restart:

```bash
docker-compose restart
```

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Stop the container
docker-compose stop

# Start the container
docker-compose start

# Rebuild and restart
docker-compose up -d --build

# Remove everything
docker-compose down
```

## Troubleshooting

### Chromecast devices not found
- Ensure `network_mode: host` is enabled in docker-compose.yml
- Check that your Chromecast devices are on the same network as the Docker host

### Port already in use
If port 5005 is already in use, change the port mapping in docker-compose.yml:

```yaml
ports:
  - "8080:5005"  # Maps host port 8080 to container port 5005
```

### DynamoDB connection issues
Ensure your DynamoDB endpoint is accessible from the container. If running DynamoDB locally, use `network_mode: host` or configure the correct network bridge.
