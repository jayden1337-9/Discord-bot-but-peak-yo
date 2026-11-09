# Peak / Anime Chronicles

A comma-prefix Discord bot for community tools and a persistent anime-themed RPG. Built with Python and discord.py for lightweight hosting such as Wispbyte.

## Features

- Dark, text-first Discord embeds with no decorative emoji spam
- Community tools, polls, moderation utilities and random tools
- Anime character roster inspired by Jujutsu Kaisen, One Piece, Naruto, Bleach, Dragon Ball and more
- Character-specific signature abilities, a material-and-level gated universal skill tree, race passives, clan-based melee/sword/magic bonuses and character mastery
- Three craftable anime boss keys for JJK, JoJo and Naruto boss pools, plus clan rerolls and expanded bloodlines
- Five craftable weapons with distinct damage ranges and signature abilities
- Ten unlockable dimensions with victory, level and material requirements; each grants a different damage affinity
- Thirty-nine raid bosses across Jujutsu Kaisen, JoJo's Bizarre Adventure, Naruto, One Piece, Bleach, Demon Slayer, My Hero Academia, Dragon Ball and more, including eight beginner-friendly encounters
- Nine forgeable signature weapons and ten universal combat skills
- Eight permanent relic pieces across armor, relic and core slots, with attack and defense bonuses
- A persistent ten-floor solo Rift Tower with escalating bosses, floor rewards and saved best records
- Collectible boss materials, healing potions, battle tonics, focus elixirs and awakening crystals
- Cooperative turn-based boss raids with party turns, escalating boss phases, retaliation and rewards
- Party scaling, a six-player raid limit, raid exit/abandon controls and Phoenix Feather revives
- Custom weapon builder and owner-only damage controls
- Persistent JSON player profiles, inventories, weapons and active raids
- Huge-number display for existing high-level profiles\n- Exact symbolic googolplex swarm rewards, tracked without expanding their decimal digits; symbolic XP is kept separate from ordinary level calculations
- Owner-only GitHub update/restart with validation and rollback

## Requirements

- Python 3.10+
- Git installed on the host
- A Discord bot token
- Message Content Intent enabled in the Discord Developer Portal

## Environment

Set these in the Wispbyte environment/settings panel. Never commit real tokens.

- `DISCORD_TOKEN` — required Discord bot token
- `BOT_OWNER_ID` — numeric Discord user ID allowed to use owner commands
- `COMMAND_PREFIX` — command prefix (default: `,`)
- `GITHUB_TOKEN` — GitHub token with repository Contents read access, used by the supervisor to pull updates
- `GITHUB_BRANCH` — branch to pull (default: `main`)
- `BOT_DATA_DIR` — optional persistent data directory (default: `/home/container/data`)
- `LOG_LEVEL` — logging level (default: `INFO`)

## Startup

Install dependencies:

```sh
pip install -r requirements.txt
```

Start the supervisor:

```sh
python run.py
```

The supervisor restarts the bot after unexpected exits. The owner-only `,reload` command requests a controlled GitHub pull, validates Python files, installs requirements and rolls back if validation fails.

## Commands

### System
- `,ping` / `,latency`
- `,about` / `,botinfo`
- `,help` / `,commands`

### Community
- `,userinfo [member]`
- `,serverinfo`
- `,avatar [member]`
- `,roleinfo <role>`
- `,poll <question>`
- `,purge <amount>` — requires Manage Messages

### Tools
- `,roll [sides]`
- `,coinflip`
- `,choose option one | option two`
- `,8ball <question>`

### Adventure
- `,characters` / `,roster`
- `,character <key>`
- `,races` and `,race <key>`
- `,clans`, `,clan`, `,clan roll` — view and reroll clan bonuses
- Owner-only: `,clan set <key>` (aliases: `choose`, `select`) — select any clan directly; use `,clan set off` to clear
- `,bosskey use <jjk|jojo|naruto>` — consume an anime key to summon a boss from that series
- `,craft item <key>` / `,craft i <key>` — craft boss keys and clan rerolls
- `,skills`, `,skilltree`, `,mastery` and `,unlock <skill>`
- `,recipes` and `,craft <key>` — forge permanent weapons from boss materials
- `,forge list` / `,forge craft <key>` — create permanent armor, relics and cores
- `,gear`, `,equipgear <key>`, `,unequipgear <slot>` — manage equipment
- `,tower start`, `,tower attack`, `,tower`, `,tower retreat` — challenge the ten-floor solo tower
- `,dimension list` and `,dimension enter <key>` — unlock and travel between worlds
- `,use <item>` — use raid potions, combat boosts, awakening crystals and Phoenix Feathers
- `,bosses`
- `,boss challenge <key>`
- `,boss summon <key> <count>` — owner only
- `,boss status`
- `,boss leave` / `,boss abandon`
- `,join`
- `,attack [ability]`
- `,inventory` / `,inv` / `,bag`
- `,eat <item>` — bloodline awakenings
- `,use phoenix_feather` — revive during a raid
- `,stats [member]` / `,me`
- `,leaderboard` / `,top`
- `,daily`, `,weekly`, `,quests`, `,claim <daily|weekly>`
- `,achievements`, `,titles`, `,title <key|off>`
- `,weapon list`, `,weapon equip <key>`, `,weapon unequip`

### Owner
- `,createweapon`
- `,setdamage <amount|googolplex|off>`
- `,giveitem <member> <item> [amount]`
- `,addxp <member> <amount>`
- `,addpoints <member> <amount>`
- `,setlevel <member> <level>`
- `,setcharacter <member> <character>`
- `,setrace <member> <race>`
- `,resetprofile <member>`
- `,gamedb`
- `,reload`

## Data

The game database is stored in `peak_game.json` inside `BOT_DATA_DIR`. Keep that directory on persistent storage when configuring the host. The bot writes updates atomically to reduce the chance of a partially written save and refreshes `peak_game.backup.json` from the last valid database before overwriting it.

Large player values are displayed in scientific notation. A googolplex swarm is represented exactly as 10^(10^100) and its damage, loot, victories, skill points and XP rewards are tracked symbolically. Symbolic XP is kept separate from ordinary level progression because the resulting level cannot be represented as a practical finite integer.


## Rift Expeditions update

- Four three-stage solo routes: Cursed Realm Descent, Shinobi Frontier, Grand Line Gauntlet, and Riftfall
- Saved expedition progress, enemy stages, player HP, route requirements, and route-clear rewards
- Five collectible companions with persistent ownership and equip slots
- Companion attack and defense bonuses apply to raids and expeditions
- Daily login streaks with XP, skill points, and a seven-day Mythic Token reward

Commands:
- `,expedition`, `,expedition start <route>`, `,expedition status`, `,expedition attack [ability]`, `,expedition retreat`
- `,pets`, `,pet equip <key>`, `,pet off`
- `,login`
