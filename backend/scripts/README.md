# Scripts Documentation

This document provides detailed information about the utility scripts available in the `scripts` directory.

## Development Scripts

### connect_to_db.sh
**Purpose**: Establishes a connection to the PostgreSQL database.
**Usage**:
```bash
./connect_to_db.sh
```
**Description**: This script connects to the database using the environment variables configured in your `.env` file. It's useful for:
- Debugging database issues
- Running manual queries
- Checking database state
- Verifying connections

### migration.sh
**Purpose**: Manages database migrations.
**Usage**:
```bash
./migration.sh [command]
```
**Commands**:
- `up`: Apply all pending migrations
- `down`: Rollback the last migration
- `status`: Show migration status
- `create`: Create a new migration

### run_sanity_check.sh
**Purpose**: Runs basic sanity checks on the application.
**Usage**:
```bash
./run_sanity_check.sh
```
**Description**: This script:
- Checks environment variables
- Verifies database connection
- Tests API endpoints
- Validates module structure
- Useful for quick health checks
