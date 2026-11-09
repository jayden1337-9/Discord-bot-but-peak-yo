# Peak

A modular Python Discord bot designed for Wispbyte. The default command prefix is a comma.

## Features

- Consistent dark, text-first embeds
- Community information and role tools
- Reaction polls and moderator message cleanup
- Random utilities
- Cooperative boss encounters with health bars and contributor rankings
- Owner-only GitHub update and restart
- Supervisor restart loop with update validation and rollback

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

## Command index

### System
- `,ping` / `,latency`
- `,about` / `,botinfo`
- `,help` / `,commands`

### Community
- `,userinfo [member]` / `,profile`
- `,serverinfo` / `,server`
- `,avatar [member]` / `,pfp`
- `,roleinfo <role>`
- `,poll <question>`
- `,purge <amount>` (Manage Messages permission)

### Tools
- `,roll [sides]`
- `,coinflip`
- `,choose option one | option two`
- `,8ball <question>`

### Adventure
- `,bosses` / `,bestiary`
- `,boss challenge <warden|leviathan|sovereign>`
- `,boss status`
- `,attack` / `,strike`

### Owner
- `,reload` — pull GitHub updates and restart (owner only)

Boss encounters are currently in-memory and reset if the bot process restarts. Rewards are displayed as a reward pool only; no economy or currency is granted yet.
