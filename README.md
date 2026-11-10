# Discord Bot

A lightweight, prefix-based Discord bot with community utilities and a persistent anime RPG. Built with Python and discord.py for hosts such as Wispbyte.

## Features

- Consistent Discord-native embeds, interactive command menus, owner-locked pagination and a Pillow-rendered inventory
- Community tools, polls, moderation utilities and random tools
- Anime character roster inspired by Jujutsu Kaisen, One Piece, Naruto, Bleach, Dragon Ball and more
- Character-specific signature abilities, a material-and-level gated universal skill tree, race passives, clan-based melee/sword/magic bonuses and character mastery\n- Tactical raid combat with separate melee, sword and magic loadouts; each turn requires selecting a weapon type and an equipped skill
- Three craftable anime boss keys for JJK, JoJo and Naruto boss pools, plus clan rerolls and expanded bloodlines
- Five craftable weapons with distinct damage ranges and signature abilities
- Anime-specific dimensions with their own boss rosters, level/material gates and scaling up to billions of HP
- Anime boss rosters across Jujutsu Kaisen, JoJo's Bizarre Adventure, Naruto, One Piece, Bleach, Demon Slayer, My Hero Academia, Dragon Ball, Hunter x Hunter, Fairy Tail, Black Clover, Attack on Titan, Slime and Gurren Lagann
- Nine forgeable signature weapons and ten universal combat skills
- Eight permanent relic pieces across armor, relic and core slots, with attack and defense bonuses
- An endless solo Rift Tower with escalating bosses, floor rewards and saved best records
- Five global chest tiers (Common, Rare, Diamond, Ruby, Mythic) with difficulty-scaled drop rates, tiered loot, exclusive boss drops, Gold and Gems
- Cooperative turn-based boss raids with party turns, escalating boss phases, retaliation and rewards
- Party scaling, a six-player raid limit, raid exit/abandon controls and Phoenix Feather revives
- Custom weapon builder and owner-only damage controls
- Persistent JSON player profiles, inventories, weapons and active raids
- Ascension progression with up to 25 permanent damage upgrades; no level or inventory reset
- Global cooperative world bosses with contribution rankings, one-time rewards and three difficulty tiers
- Endless Rift Tower floors with rotating bosses and scaling rewards
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
- `,guild create <name>` / `,guild join <name>` / `,guild leave` / `,guild info` / `,guild members` / `,guild transfer @member` / `,guild kick @member` / `,guild top` / `,guild donate <gold>` — server guilds with rate-limited message activity XP, donations, leveling and member-slot unlocks
- `,trade offer @member <item|gold> <amount>` / `,trade pending` / `,trade accept <id>` / `,trade cancel <id>` — direct 24-hour offers for items or Gold
- `,market browse` / `,market my` / `,market list <item> <amount> <price>` / `,market buy <id>` / `,market cancel <id>` — server-scoped player market
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
- `,tower start`, `,tower`, `,tower retreat` — challenge the endless solo tower; use `,attack` for combat
- `,dimension list` and `,dimension enter <key>` — unlock anime worlds and inspect their boss rosters
- `,chest` / `,chest open <common|rare|diamond|ruby|mythic>` — view and open the five global chest rarities
- `,wallet` / `,shop` / `,buy <item> [amount]` — earn and spend Gold and Gems
- `,use <item>` — use raid potions, combat boosts, awakening crystals and Phoenix Feathers
- `,bosses`
- `,boss challenge <key>`
- `,boss summon <key> <count>` — owner only
- `,boss status`
- `,boss leave` / `,boss abandon`
- `,join`
- `,attack` — universal combat command; automatically attacks your current raid, tower, expedition or joined global world boss. Select Melee, Sword or Magic, then choose an equipped skill\n- `,equipskill <melee|sword|magic> <skill>` / `,unequipskill <type> <skill>` — manage up to three equipped skills per category\n- `,skillloadout` — inspect equipped combat skills
- `,inventory` / `,inv` / `,bag` — icon-based inventory with Gold and Gems
- `,eat <item>` — bloodline awakenings
- `,use phoenix_feather` — revive during a raid
- `,profile` / `,stats [member]` / `,me`
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

The player database is stored in `peak_game.json` inside `BOT_DATA_DIR`. The filename is retained for compatibility with existing player data. Keep that directory on persistent storage when configuring the host. The bot writes updates atomically and keeps a last-known-good `peak_game.backup.json` recovery snapshot. If the main database is damaged, startup attempts to restore that snapshot; if no valid recovery copy exists, startup stops rather than silently creating an empty database.

Large player values are displayed in scientific notation. A googolplex swarm is represented exactly as 10^(10^100) and its damage, loot, victories, skill points and XP rewards are tracked symbolically. Symbolic XP is kept separate from ordinary level progression because the resulting level cannot be represented as a practical finite integer.


## Rift Expeditions update

- Four three-stage solo routes: Cursed Realm Descent, Shinobi Frontier, Grand Line Gauntlet, and Riftfall
- Saved expedition progress, enemy stages, player HP, route requirements, and route-clear rewards
- Five collectible companions with persistent ownership and equip slots
- Companion attack and defense bonuses apply to raids and expeditions
- Daily login streaks with XP, skill points, and a seven-day Mythic Token reward

Commands:
- `,expedition`, `,expedition start <route>`, `,expedition status`, `,expedition retreat` — use `,attack` during the run
- `,pets`, `,pet equip <key>`, `,pet off`
- `,login`

## Final endgame update

- `,ascension` shows requirements and permanent bonus; `,ascend` consumes Rift Crystals, Mythic Tokens and Time Rift Fragments for a permanent +2% damage bonus per rank, up to 25 ranks. Ascension never resets level, XP, inventory, equipment, weapons or skills.
- `,worldboss` shows the global event; `,worldboss join` joins; `,attack` opens the normal category-first skill picker during the event; `,worldboss leaderboard` ranks contributions; `,worldboss claim` grants one reward after victory.
- Owner-only event controls: `,worldboss summon <world_eater|celestial_dragon|void_emperor>` and `,worldboss close`. World boss state is shared across servers and saved in the game database.
- Ascension bonuses apply to raids, expeditions, Rift Tower and world boss damage.
- Rift Tower continues indefinitely after floor 10 with rotating bosses, increasing health and damage, and scaled material rewards.


## Universal combat command

- `,attack` automatically routes to the encounter you most recently entered: raid, Rift Tower, expedition or joined global world boss. It opens the shared category-first skill picker and uses the same equipped loadout across modes.
- Entering or joining an encounter sets it as your active attack target. If an older profile has multiple active encounters but no saved target, the router uses a safe fallback order: Rift Tower, expedition, world boss, then raid.
- The older nested attack commands remain available for compatibility, but are no longer required.


## Social systems

- `,guild create <name>` creates a server-scoped guild for 10,000 Gold.
- `,guild join <name>`, `,guild leave`, `,guild info`, `,guild members`, and `,guild transfer @member` manage guild membership.
- `,trade offer @member <item> <amount>` creates a 24-hour direct item offer; `,trade accept <id>` and `,trade cancel <id>` resolve it.
- `,market list <item> <amount> <price>` escrows an item stack for sale. `,market browse`, `,market buy <id>`, and `,market cancel <id>` manage listings.
- Guilds gain 5 XP from eligible member messages, at most once per member per minute, or from Gold donations. Guild levels unlock member slots up to 20.
- Guilds, trades and listings are scoped to the Discord server. Player profiles remain shared by Discord user ID. Symbolic reward balances are intentionally non-transferable.
