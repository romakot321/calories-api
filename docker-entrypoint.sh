#!/bin/bash
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database to be ready..."
    max_attempts=30
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if alembic current &> /dev/null; then
            echo "Database is ready!"
            return 0
        fi

        attempt=$((attempt + 1))
        echo "Database is unavailable - attempt $attempt/$max_attempts"
        sleep 2
    done

    echo "Database failed to become ready after $max_attempts attempts"
    return 1
}

# Wait for database and run migrations
# wait_for_db

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec proxychains4 gunicorn src.main:app -w 1 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80 --forwarded-allow-ips="*"
