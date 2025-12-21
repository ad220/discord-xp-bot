python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo systemctl enable $PWD/discord_xpbot.service
sudo systemctl start discord_xpbot.service
