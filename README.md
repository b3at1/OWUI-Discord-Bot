# Open WebUI Discord Bot

This repository is a rewrite of [this existing Open WebUI Discord Bot](https://github.com/ezavesky/openwebui_discord_bot) with some additional features. Some of the code is directly taken, and some is rewritten. 

## Usage

Docker is required to deploy, or you can run the Python directly.

First copy `.env.example` to `.env` and fill in the required values. 

Then, run `docker compose up --build -d` to start the bot.

## TAMU AI

There is a patch in place for use with the TAMU Open WebUI platform, which differs slightly from the original Open WebUI. If you are not using this platform, feel free to remove the patch and adjust the `Dockerfile` as necessary.