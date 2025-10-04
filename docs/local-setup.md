# Local Development Setup

This guide walks you through setting up the HackDuke Portal on your local machine for development.

## Prerequisites

- Docker
- VS Code or Cursor with the Dev Containers extension
- Node.js and npm (for running frontend outside container)

## 1. Development Environment Setup

This project uses Dev Containers for a consistent development environment. Follow the [Development Environment guide](./devcontainer.md) to set up your container.

## 2. Environment Variables

You will need a `.env` file in the project root for the application to run.

> **Important:** Request the `.env` file from a team member. This file contains sensitive configuration including Auth0 credentials, AWS credentials, and database connection details.

## 3. Database Setup

For accessing the production/staging database:

1. Install and configure Tailscale - see [Networking guide](./networking.md#installing-tailscale)
2. Get database credentials from a team member
3. Update your `.env` file with the remote `DB_HOST` IP address
4. Verify connection using the [PostgreSQL guide](./postgres.md)

## 4. Running the Application

### Backend

From the project root:

```bash
make backend
```

Or manually:

```bash
cd portal-backend-python
PYTHONPATH=/workspaces/portal.hackduke.org uvicorn server:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend

From the project root:

```bash
make frontend
```

Or manually:

```bash
cd portal-frontend
npm install  # first time only
npm start
```

The frontend will be available at `http://localhost:3000`

## 5. Verify Setup

1. **Check backend health:**

   ```bash
   curl http://localhost:8000/health
   ```

   Should return: `{"message": "OK"}`

2. **Check frontend:** Navigate to `http://localhost:3000` in your browser

3. **Test authentication:** See the [Auth guide](./auth.md#testing-authenticated-endpoints) for testing authenticated endpoints

## 6. Running Tests

```bash
make test
```

Or manually:

```bash
pytest
```

## Troubleshooting

### Database Connection Issues

- If using local PostgreSQL, ensure Docker container is running: `docker ps`
- If using remote database via Tailscale, verify you're connected: check Tailscale status
- Verify credentials in `.env` match your database setup

### Port Already in Use

- Backend (8000): Check if another service is using the port
- Frontend (3000): React will automatically try port 3001 if 3000 is busy
- PostgreSQL (5432): Stop any other PostgreSQL instances or change the port mapping in `postgres/docker-compose.yml`

### Module Not Found Errors

- Ensure you're running commands from within the dev container
- Verify `PYTHONPATH` is set correctly when running backend
- For frontend, try removing `node_modules` and running `npm install` again

## Next Steps

- Read the [Auth documentation](./auth.md) to understand authentication flow
- Review [SQLAlchemy & Alembic](./sqlalchemy.md) before making database changes
- Check the [Networking guide](./networking.md) for production infrastructure details
