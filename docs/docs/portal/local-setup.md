# Local Development Setup

This guide walks you through setting up the HackDuke Portal on your local machine for development.

## 1. Development Environment Setup

This project uses Dev Containers for a consistent development environment. Follow the [Development Environment guide](./devcontainer.md) to set up your container.

## 2. Environment Variables

You will need two separate `.env` files for the application to run:

1. **Backend `.env`** - Place in the `backend/` folder
2. **Frontend `.env`** - Place in the `frontend/` folder

> **Important:** Request both `.env` files from a team member. These files contain sensitive configuration including Auth0 credentials, AWS credentials, and database connection details.

> **Note:** Verify that frontend `.env` has `BACKEND_URL=localhost:3000` and backend `.env` has `FRONTEND_URL=localhost:8000` for local development.

## 3. Database Setup

For accessing the production/staging database:

1. Install and configure Tailscale - see [Networking guide](./networking.md#installing-tailscale)
2. Get database credentials from a team member
3. Verify the backend `.env` file (in `backend/` folder) has the correct `DB_HOST` IP address
4. Verify connection using the [PostgreSQL guide](./postgres.md)

## 4. Running the Application

### Backend

From the project root:

```bash
make backend
```

The backend API will be available at `http://localhost:8000`

You can test if the backend is successfully up with this command

```bash
curl http://localhost:8000/health
```

If you get : `"{"message":"OK"}"` then your backend is up and running.

### Frontend

From the project root:

```bash
make frontend
```

The frontend will be available at `http://localhost:3000`. You can go to `http://localhost:3000` in your browser and be able to see the local instance of the website

## 5. Running Tests

```bash
make test
```

> **Note:** Tests run automatically as a GitHub Action on every branch and must pass before merging a PR into main.

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
