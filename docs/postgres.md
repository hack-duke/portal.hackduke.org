
# PostgreSQL

## Connecting to PostgreSQL

You can do this with any database client (`psql` for CLI, pgAdmin), but I like using Postico (available free for Mac). You can download it [here](https://eggerapps.at/postico2/).

Make sure you are connected to Tailscale. See [networking documentation](https://github.com/hack-duke/portal.hackduke.org/blob/master/docs/networking.md#installing-tailscale) for installation details. 

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