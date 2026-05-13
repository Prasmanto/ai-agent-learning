# Deploy Your Crypto Agent to a VPS (Ubuntu 22.04)

This guide takes you from a freshly-bought VPS to a **24/7 public chat
agent** at `http://YOUR_SERVER_IP:8501`, in about 15 minutes.

Tested on **Hetzner CX22** and **DigitalOcean Basic Droplet** with
**Ubuntu 22.04**. Any Ubuntu 22.04/24.04 VPS with 1 GB+ RAM works.

---

## Before you start

- [ ] You bought a VPS and received an **IP address** + **root password**
- [ ] You set an OpenAI **monthly spending limit** at
      https://platform.openai.com/settings/organization/limits (start with $5)
- [ ] You have your OpenAI API key ready (`sk-...`)

---

## Step 1 — SSH into the server

From your laptop terminal:

```bash
ssh root@YOUR_SERVER_IP
```

First time it asks "Are you sure you want to continue connecting?" → type `yes`.
Paste the password from your VPS provider's email.

You're now on the server. Your prompt changes to something like `root@crypto-agent:~#`.

> **Windows users:** install [PuTTY](https://www.putty.org/) and use its GUI.

---

## Step 2 — Update the system

```bash
apt update && apt upgrade -y
```

Takes ~2 minutes. If it asks about kernel upgrades or config files, just press Enter to accept defaults.

---

## Step 3 — Create a non-root user (safer)

Never run a public service as `root`. Make a regular user:

```bash
adduser kiro                    # pick any name; set a password when prompted
usermod -aG sudo kiro           # give them sudo rights
su - kiro                       # switch to that user
```

From here on, your prompt is `kiro@crypto-agent:~$`.

---

## Step 4 — Install dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git tmux nano ufw
python3 --version    # should print 3.10 or higher
```

---

## Step 5 — Clone the repo

```bash
cd ~
git clone https://github.com/Prasmanto/ai-agent-learning.git
cd ai-agent-learning
```

---

## Step 6 — Set up Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Your prompt should now show `(.venv)` at the start. That means you're using the sandboxed Python.

---

## Step 7 — Configure your secrets

```bash
cp .env.example .env
nano .env
```

Replace `sk-replace-with-your-real-key` with your real OpenAI key.

- Save with **Ctrl+O** → Enter
- Exit with **Ctrl+X**

---

## Step 8 — Smoke test

Run Lesson 1 to confirm the basic wiring works:

```bash
python lessons/01_hello_llm.py
```

You should see the model reply with a few paragraphs about blockchain. **Good — everything works.**

If you hit an error, see the **Troubleshooting** section at the bottom.

---

## Step 9 — Open the firewall for Streamlit

Streamlit listens on port **8501**. We need to let that through the firewall.

```bash
sudo ufw allow OpenSSH           # keep SSH open (important!)
sudo ufw allow 8501/tcp          # allow Streamlit
sudo ufw --force enable
sudo ufw status                  # confirm both rules are listed
```

> **DigitalOcean / AWS users**: you may also need to open port 8501 in the
> web-console **"Firewalls"** or **"Security Groups"** section.
> Hetzner has no external firewall by default, so `ufw` is enough.

---

## Step 10 — Make the agent run 24/7 (systemd service)

This is the "always online" magic. `systemd` is Linux's built-in process manager. We'll tell it:

- Start Streamlit when the server boots
- Restart Streamlit automatically if it crashes
- Log everything for later debugging

The service file is in the repo at `deploy/crypto-agent.service`. Install it:

```bash
# Copy the service file into systemd's config directory
sudo cp ~/ai-agent-learning/deploy/crypto-agent.service /etc/systemd/system/

# Tell systemd to re-read its config
sudo systemctl daemon-reload

# Start the service now
sudo systemctl start crypto-agent

# Start it automatically on every reboot
sudo systemctl enable crypto-agent

# Check that it's running
sudo systemctl status crypto-agent
```

You should see `Active: active (running)` in green. Press `q` to exit the status view.

---

## Step 11 — Visit your agent in a browser

Open:

```
http://YOUR_SERVER_IP:8501
```

🎉 **Your crypto agent is now live on the internet, and will stay up even after you close SSH or reboot the server.**

---

## Daily operations

### See live logs
```bash
sudo journalctl -u crypto-agent -f       # -f = follow (Ctrl+C to exit)
```

### Restart after editing code
```bash
cd ~/ai-agent-learning
git pull                                  # grab latest changes from GitHub
sudo systemctl restart crypto-agent
```

### Stop the agent (save tokens when not using it)
```bash
sudo systemctl stop crypto-agent
```

### Start it back up
```bash
sudo systemctl start crypto-agent
```

### Update dependencies
```bash
cd ~/ai-agent-learning
source .venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart crypto-agent
```

---

## ⚠️ Security warning — read this

Your agent is now on the **public internet** with **no password**. Anyone with your IP can chat with it on **your** OpenAI credit. Before sharing the URL anywhere:

1. **Hard limit your OpenAI spending** (do this NOW):
   https://platform.openai.com/settings/organization/limits → set monthly budget to $5

2. **Consider adding Basic Auth** (see `deploy/README.md` for an Nginx-based example — we can add this later).

3. **Stop the service when not using it** if you're not confident in the security yet:
   ```bash
   sudo systemctl stop crypto-agent
   ```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `systemctl status` shows `Failed` | `.env` missing or bad key | Check `cat ~/ai-agent-learning/.env` — the key must be a real `sk-...` |
| Browser says "can't connect" | Firewall not open | `sudo ufw status` should show `8501/tcp ALLOW`. For DO/AWS, check cloud-console firewall too. |
| `ModuleNotFoundError: No module named 'openai'` | Venv not activated in the service | Check that `deploy/crypto-agent.service` uses `/home/kiro/ai-agent-learning/.venv/bin/python` as `ExecStart`. |
| `sudo: command not found` (you're still root) | You skipped step 3 | Either keep using the root commands (drop `sudo`) or run `adduser` now. |
| OpenAI `RateLimitError: insufficient_quota` | No billing on OpenAI account | Add $5 credit at https://platform.openai.com/settings/organization/billing |
| Streamlit says "permission denied" on port 8501 | Port conflict or insufficient perms | `sudo lsof -i :8501` to see what's using it; kill or pick another port. |

---

## Common customizations

### Run on a different port
Edit `deploy/crypto-agent.service`, change `--server.port=8501` to another port (e.g. `80` if you want bare IP access — but that needs `sudo` privileges, easier to keep 8501).

### Run a different lesson instead
Edit `deploy/crypto-agent.service`, change the `ExecStart` line's script path from `lessons/07_streamlit_ui.py` to whatever you want.

### Change the user name (if you didn't use `kiro`)
Edit `deploy/crypto-agent.service` and replace `kiro` with your username in `User=`, `Group=`, and all the paths.
