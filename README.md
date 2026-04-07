# Sir Brackets-a-Lot

A Discord bot for running single and double elimination tournaments using reaction-based signups.

---

## Features

- Create tournaments with a custom signup emoji
- Players sign up by reacting to the signup message
- Single elimination and double elimination brackets
- Match results reported via buttons
- Bracket auto-advances after each round
- Double elimination includes grand final and grand final reset

---

## Setup

### 1. Clone the repo
```
git clone https://github.com/DumfordJohn/Sir_Brackets-a-Lot.git
cd Sir_Brackets-a-Lot
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Create a Discord bot
- Go to https://discord.com/developers/applications
- Create a new application and add a bot
- Under **Bot**, enable all three Privileged Gateway Intents:
  - Presence Intent
  - Server Members Intent
  - Message Content Intent
- Under **OAuth2**, generate an invite URL with the `bot` and `applications.commands` scopes and invite it to your server

### 4. Create a .env file
In the root of the project create a file named `.env`:
```
DISCORD_TOKEN=your_bot_token_here
```

### 5. Set up your server
Make sure your server has a channel named exactly `sign-ups` — this is where tournament signup embeds will be posted.

### 6. Run the bot
```
python bot.py
```

---

## Commands

| Command | Description |
|---|---|
| `/create_tournament name type emoji` | Create a new tournament. Type is `single` or `double`. Emoji is optional (defaults to 🎮) |
| `/start_tournament name` | Start a tournament and post the bracket. Must be an admin. |
