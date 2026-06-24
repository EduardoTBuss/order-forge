#!/bin/bash

# Database settings from environment variables
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-postgres}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-postgres}

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Error: One or more required environment variables are not set."
    exit 1
fi

echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "DB_NAME=$DB_NAME"
echo "DB_USER=$DB_USER"

# Install the PostgreSQL client if necessary
install_postgresql_client() {
    echo "Checking if PostgreSQL client is installed..."
    if ! command -v psql &> /dev/null; then
        echo "PostgreSQL client not found. Installing..."
        apt update -y
        apt install -y postgresql-client
    else
        echo "PostgreSQL client already installed."
    fi
}

install_postgresql_client

# Connect to the database interactively
echo "Connecting to the database..."
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -d "$DB_NAME" \
    -U "$DB_USER"
