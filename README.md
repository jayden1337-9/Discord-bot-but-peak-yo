# Discord-bot-but-peak-yo

A modular Python Discord bot designed for Wispbyte.

## Features

- Consistent Discord embeds and a central command directory
- Latency, bot information, member information, server information and avatar commands
- Dice rolls, random choice and a simple 8-ball
- Cooperative server boss encounters with health, attack cooldowns and contributor rankings
- Owner-only controlled GitHub update and restart
- Supervisor restart loop with validation and rollback on failed updates

## Requirements

- Python 3.10+
- Git installed on the host
- A Discord bot token

## Environment variables

Set these in Wispbyte's environment/settings panel. Never commit real tokens.

- `DISCORD_TOKEN` — required Discord bot token
- `BOT_OWNER_ID` — Discord user ID allowed to use `,reload`
- `COMMAND_PREFIX` — command prefix (default: `,`)
- `GITHUB_TOKEN` — fine-grained GitHub token with Contents: Read-only
- `GITHUB_BRANCH` — branch to pull (default: `main`)

## Startup

Install dependencies with `pip install -r requirements.txt`, then use:

```sh
python run.py
```

Enable **Message Content Intent** in the Discord Developer Portal for prefix commands.

## Commands

### General
- `,ping`
- `,about`
- `,help`
- `,userinfo [member]`
- `,serverinfo`
- `,avatar [member]`
- `,roll [sides]`
- `,choose option one | option two | option three`
- `,8ball <question>`

### Adventure
- `,bosses`
- `,boss challenge <warden|leviathan|sovereign>`
- `,boss status`
- `,attack`

Boss encounters are currently in-memory and reset if the bot process restarts. Rewards are displayed as a reward pool only; no economy or currency is granted yet.
