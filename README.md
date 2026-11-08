[![Netlify Status](https://api.netlify.com/api/v1/badges/54be151e-1377-4bcf-a6c4-03f9c87c2546/deploy-status)](https://app.netlify.com/sites/hackduke-portal/deploys)

# portal

## Docs

- [Development Environment](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/devcontainer.md)
- [Local-setup](docs/local-setup.md)
- [HackDuke restoration and DuQuantum archive](docs/hackduke-restoration.md)
- [PostgreSQL](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/postgres.md)
- [Networking & Tailscale](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/networking.md)
- Portal
  - [Auth](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/auth.md)
  - [SQLAlchemy & Alembic](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/sqlalchemy.md)

## Deployment

The frontend is deployed on Netlify (builds the `portal-frontend` folder and serves from it)

The complete DuQuantum 2026 portal is preserved on the
[`duquantum-2026` branch](https://github.com/hack-duke/portal.hackduke.org/tree/duquantum-2026).

The backend is deployed on EC2: - Docker compose w/ two containers - First container is Caddy for SSL termination and reverse proxying - Second container is running portal-backend
