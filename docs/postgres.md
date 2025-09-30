
# PostgreSQL

## Connecting to PostgreSQL

> Please be mindful of running mass updates on the database. Run your queries through another member of the team if you are unsure. 

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

<img width="800" alt="Screenshot 2025-09-09 at 3 07 20 AM" src="https://github.com/user-attachments/assets/53cde9ba-229b-405f-886d-ed17ecd8d34d" />

Use the bottom left `Tables` menu to select a table to view.

<img width="195" height="178" alt="Screenshot 2025-09-29 at 9 56 08 PM" src="https://github.com/user-attachments/assets/4de6bc07-c97f-4da9-bc9a-22bf5977fa3e" />

Run queries on the database with the `SQL Query` tool.

<img width="946" height="155" alt="Screenshot 2025-09-29 at 9 55 54 PM" src="https://github.com/user-attachments/assets/6b023432-cf75-4a8c-ae26-dcf41d8f241e" />

## Windows Alternative (pgAdmin)
Download the latest release of the application [here](https://www.pgadmin.org/download/pgadmin-4-macos/).

<img width="800" alt="Screenshot 2025-09-29 at 9 26 50 PM" src="https://github.com/user-attachments/assets/5b7463de-c8d7-4ef4-a72c-cbfaf1e94b2e" />

Click `Add New Server`. Fill in the fields as instructed above. Make sure to check the `Save Password` box.

To run queries, use the `Query Tool` in the top left. 

<img width="756" height="184" alt="Screenshot 2025-09-29 at 9 37 58 PM" src="https://github.com/user-attachments/assets/10e1cd1d-0eab-4616-996e-5645827dec4c" />

To view the tables in the database, click `hackduke > Databases > hackathon > Schemas > public > Tables`. 

<img src="https://github.com/user-attachments/assets/c9f2cd51-8011-4278-b4b3-d8eac8bc6276" height="500">

You can select each a table that you wish to view and click `All Rows` to generate a query to view the data.  
