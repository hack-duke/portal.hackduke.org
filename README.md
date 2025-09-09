[![Netlify Status](https://api.netlify.com/api/v1/badges/54be151e-1377-4bcf-a6c4-03f9c87c2546/deploy-status)](https://app.netlify.com/sites/hackduke-portal/deploys)

# portal

## Deployment

The frontend is deployed on Netlify (builds the `portal-frontend` folder and serves from it)

The backend is deployed on EC2:
    - Docker compose w/ two containers
    - First container is Caddy for SSL termination and reverse proxying
    - Second container is running portal-backend

## Connecting to PostgreSQL

You can do this with any database client (`psql` for CLI, pgAdmin), but I like using Postico (available free for Mac). You can download it [here](https://eggerapps.at/postico2/).

Make sure you are connected to Tailscale. See [networking documentation](https://eggerapps.at/postico2/) for installation details. 

Open Postico. Click `New Server` to create a new connection. Name your server. 

Fill in the appropriate fields:
- `host` should be the private IPv4 address of the `portal-db` EC2 instance 
- `port` can be left as `5432`
- `database` is `hackathon`
- `user` and `password` should be able to be found in the latest `.env` files. If you are having trouble finding them just send a message in the group.

<img width="438" height="512" alt="Screenshot 2025-09-09 at 3 03 18 AM" src="https://github.com/user-attachments/assets/be608742-94e0-449a-a616-67274a8de74e" />

Click `Test`. If unsuccessful, check your Tailscale connection. If successful, `Connect`.

<img width="943" height="564" alt="Screenshot 2025-09-09 at 3 07 20 AM" src="https://github.com/user-attachments/assets/53cde9ba-229b-405f-886d-ed17ecd8d34d" />

Success! You now have access to view and modify the database through Postico. Please be mindful of running mass updates on the database. Run your queries through another member of the team if you are unsure. 
