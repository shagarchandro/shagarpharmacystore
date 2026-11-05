Putting Shagar Medical Store on a server (notes, not tested on a real VPS)
1. Copy the whole project to /opt/shagar and create a user:  useradd -r -s /usr/sbin/nologin shagar ; chown -R shagar /opt/shagar/server/data
2. First start: run it once by hand. It prints a one-time SETUP CODE; open /admin/login.html (through an SSH tunnel, or http://127.0.0.1:8000 on the server) and create the Owner account there:
     sudo -u shagar python3 /opt/shagar/server/server.py --host 127.0.0.1 --port 8000
   (use --no-demo for an empty shop; stop it with Ctrl+C once the Owner exists. For unattended installs use --owner-password or --random-owner-password instead.)
3. Install shagar.service so it starts at boot and restarts on failure.
4. Put HTTPS in front with Caddy (Caddyfile) or Nginx (nginx.conf). Point your domain to the server first.
5. Firewall: allow only ports 22 (ssh), 80 and 443. The server itself listens on 127.0.0.1 only.
6. Backups: the server makes a daily copy in server/data/backups (14 kept); also copy that folder off the machine regularly.
   Restore: stop the service, copy a backup file over server/data/shop.db, start the service.
7. Health check for monitoring tools: GET /api/health
8. Lost Owner password: python3 server/server.py --reset-password owner   (run on the server)
