# portal

## Deployment

The frontend is deployed on Netlify (builds the `portal-frontend` folder and serves from it)

The backend is deployed on EC2:
    - Docker compose w/ two containers
    - First container is Caddy for SSL termination and reverse proxying
    - Second container is running portal-backend

The backend fetches the `portal-backend` container from ECR, make sure to push if you're making changes otherwise they won't be reflected (I'll add CI/CD later).