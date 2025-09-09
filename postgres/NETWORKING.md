# Networking

We use [Tailscale](https://tailscale.com/) for secure networking across our infrastructure. Tailscale allows us to configure a private network (called a "tailnet") that allows our servers, services, and machines to communicate without exposing public ports. 

This document provides an overview of the networking infrastructure used for our private network.

## Installing Tailscale
Install Tailscale on your machine using this [link](https://tailscale.com/kb/1347/installation).

Launch the app and add your device to our tailnet by logging in with the HackDuke email. We are on the Tailscale starter plan (3 users, 100 devices per user), so it's better to add additional devices rather than users to our network. 

You should see a screen like the following. Verify your device details and click `Connect`.

<div align="center">
  <img width="400" alt="image" src="https://github.com/user-attachments/assets/75364378-4945-4d72-a237-28d5bc0a33d9" />
</div>

You're all set! You should be added to the Tailscale network and able to access our private cloud. You can find the Tailscale app minimized in the System Tray (Windows) or the Menu Bar (MacOS). If you'd like, you can configure Tailscale to start automatically on startup for convenience.

If you aren't able to access anything (e.g. timeouts on DB connections), try disconnecting and reconnecting from the network in the Tailscale client. You may need to periodically reauthenticate with the HackDuke email as your Tailscale session expires.

## User Management

You can manage the configuration of the Tailscale network from the [admin console](https://login.tailscale.com/admin). Here, you can view a list of all of the machines in the network, manage access, tags, and recent activity.

<img width="1171" height="480" alt="Screenshot 2025-09-09 at 2 03 01 AM" src="https://github.com/user-attachments/assets/969eefd0-7823-4e64-b203-1dd0a6b8e50e" />

Make sure to periodically cleanse old and unused devices from the network. This secures the network and helps us stay under our free-tier limits.

## Usage

To SSH into a private EC2 instance, make sure you are connected to the Tailscale network and run:
```
ssh -i "your_key_file.pem" <username>@<ec2_private_ip>
```

## How does it work?

### AWS VPC: A Refresher

An Amazon **Virtual Private Cloud (VPC)** is your logically isolated private network in AWS. It defines the IP addressing, routing, and access control for all resources you launch inside it (EC2 instances, RDS databases, load balancers, etc.).

<div align="center">
  <img width="800" alt="image" src="https://github.com/user-attachments/assets/22e44ca1-7aa1-4320-959b-e4666833c2e2" />
</div>

Each VPC is defined by a **CIDR block**, which specifies the private IP address range available to resources inside it. Within a VPC, you create **subnets** that divide this IP space into smaller segments. 

Subnets can be designated as **public** (accessible from the internet through an Internet Gateway) or **private** (isolated from direct internet access, usually connected outward through a NAT Gateway). In our case, we place our PostgreSQL database instance inside a private subnet within the VPC rather than exposing it to the public.  This approach simplifies access management—developers can connect with standard database credentials—while reducing the attack surface by keeping the network closed to external threats.

### Connecting Tailscale

Normally, private subnets can only reach the internet outbound (via a NAT Gateway) and cannot be reached from outside. However, by running a Tailscale router inside the VPC, we can extend our tailnet directly into AWS. This means that developers’ laptops, CI runners, or other machines already on Tailscale can connect to those private resources securely, without opening up public ports.

The way we do this is with a **subnet router**. This runs on a lightweight EC2 instance on the public subnet and routes traffic from our tailnet into the private subnets.

<div align="center">
  <img width="800" alt="image" src="https://github.com/user-attachments/assets/96675017-fff6-41ea-b5d1-061386131e49" />
</div>

The setup is relatively straightforward and discussed at length [here]((https://tailscale.com/kb/1021/install-aws#step-7-verify-your-connection)). 

Notice that we created a new **security group** (`tailscale-subnet-router`). This defines which inbound and outbound traffic is permitted through our router.

<img width="1254" height="208" alt="Screenshot 2025-09-09 at 2 28 45 AM" src="https://github.com/user-attachments/assets/a552ebf4-9ba3-42cf-8e41-0c965038a058" />

Looking at this in AWS console, we see two inbound rules defined:

1. Allows PostgreSQL connection over port 5432. Allows us to connect to the postgres database using psql or Postico from our local machines. Traffic is then forwarded over the desired port to our self-hosted postgres container.
2. Allows SSH over port 22. Allows for SSH directly into our subnet router. Useful for debugging.

We also needed to disable key expiry on the subnet router to prevent Tailscale periodically from prompting our server for re-authentication. 

Once our subnet router is up and running, we advertise the desired routes for our subnets. This declares which subnets our router can forward to—in our case the IPs corresponding to our self-hosted DB. 
```
sudo tailscale set --advertise-routes=10.0.0.0/24,10.0.1.0/24
```

Upon advertising, there is an additional verification step in the Tailscale console. Verify the subnet routes in `Awaiting Approval`.

<img width="617" height="216" alt="Screenshot 2025-09-09 at 2 40 41 AM" src="https://github.com/user-attachments/assets/2e3261f7-b850-46af-9ef3-634d3fc27e12" />

### CI/CD with Tailscale
Our GitHub Actions runners use ephemeral Tailscale auth keys to join the tailnet, so CI jobs can reach private DBs without exposing secrets over the public internet. [Official Tailscale Github Action Docs](https://tailscale.com/kb/1276/tailscale-github-action).

A good example of this can be found in our deployment workflow in `.github/deploy-db.yml`. 

We connect to the tailnet using the Tailscale Github Action.
```
- name: Connect to Tailnet
        uses: tailscale/github-action@v3
        with:
          oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
          oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
          tags: tag:ci
```

The `tag:ci` is required to grant access permissions to the ephemeral node created by our workflow, since our action is not associated with any Tailscale user.

Once we're connected to the tailnet, we can use [Tailscale SSH](https://tailscale.com/kb/1193/tailscale-ssh) to connect into our EC2 instances. 

