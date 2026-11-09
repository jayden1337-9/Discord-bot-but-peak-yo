# Discord-bot-but-peak-yo

A modular Python Discord bot designed to run on Wispbyte.

## Requirements

- Python 3.10+
- A Discord bot token
- Git installed on the host

## Environment variables

Set these in Wispbyte's environment/settings panel. Never commit real tokens.

- `DISCORD_TOKEN` — required Discord bot token
- `BOT_OWNER_ID` — Discord user ID allowed to use `!reload`
- `COMMAND_PREFIX` — command prefix (default: `!`)
- `GITHUB_TOKEN` — fine-grained GitHub token with Contents: Read-only
- `GITHUB_BRANCH` — branch to pull (default: `main`)

## Startup

Use this as the Wispbyte startup command:

```sh
python run.py
```

The supervisor restarts the bot after unexpected exits, using a short backoff.
The owner-only `!reload` command requests a controlled restart. The supervisor
then pulls the latest `main` branch, checks Python syntax, installs requirements,
and starts the bot again. If validation fails, it restores the previous code.

## Starter commands

- `!ping`
- `!about`
- `!help`
- `!reload` (owner only)

Enable **Message Content Intent** in the Discord Developer Portal for prefix commands.
