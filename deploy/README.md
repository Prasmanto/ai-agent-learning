# `deploy/` — run your agent 24/7 on a VPS

This folder contains everything you need to deploy the agent as an
always-on service on an Ubuntu 22.04+ VPS.

## Files

| File | Purpose |
|---|---|
| [`VPS_SETUP.md`](./VPS_SETUP.md) | Full step-by-step guide: SSH in, install deps, configure the service, open the firewall, verify. **Start here.** |
| [`crypto-agent.service`](./crypto-agent.service) | A systemd unit file that runs the Streamlit agent (lesson 7) on boot, auto-restarts on crashes, and logs to journald. |

## TL;DR

```bash
# on the VPS, after cloning the repo and installing deps:
sudo cp deploy/crypto-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now crypto-agent
```

Then visit `http://YOUR_SERVER_IP:8501`.

## Future add-ons (not included yet)

When you're ready, we can layer these on top:

- **Nginx reverse proxy** — serve the agent on plain port 80/443 (no `:8501` in the URL)
- **HTTPS with Let's Encrypt** — `https://yourdomain.com` instead of `http://IP`
- **Basic auth** — add a username/password so not *anyone* can chat with your agent
- **Cloudflare Tunnel** — skip the firewall entirely and get HTTPS for free

Ask Kiro when you reach that point.
