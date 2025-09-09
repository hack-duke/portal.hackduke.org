[![Netlify Status](https://api.netlify.com/api/v1/badges/54be151e-1377-4bcf-a6c4-03f9c87c2546/deploy-status)](https://app.netlify.com/sites/hackduke-portal/deploys)

# portal

## Deployment

The frontend is deployed on Netlify (builds the `portal-frontend` folder and serves from it)

The backend is deployed on EC2:
    - Docker compose w/ two containers
    - First container is Caddy for SSL termination and reverse proxying
    - Second container is running portal-backend
