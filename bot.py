import asyncio
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tournament_data import load_tournaments
from cogs.tournament.match_view import MatchView

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix=None, intents=intents)

@bot.event
async def on_ready():
    tournaments = load_tournaments()
    for name, tournament in tournaments.items():
        rounds = tournament.get("rounds", [])
        for round_index, round_matches in enumerate(rounds):
            for match_index, match in enumerate(round_matches):
                if isinstance(match, (list, tuple)):
                    p1, p2 = match
                elif isinstance(match, dict):
                    if "winner" in match:
                        continue
                    p1 = match.get("player1")
                    p2 = match.get("player2")
                else:
                    continue

                view = MatchView(
                    tournament_name=name,
                    round_index=round_index,
                    match_index=match_index,
                    player1=p1,
                    player2=p2
                )
                bot.add_view(view)

    guild = discord.Object(id=GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    print(f"Synced {len(synced)} commands to guild {GUILD_ID}")
    print("Commands registered:")
    for command in synced:
        print(f" - /{command.name}: {command.description}")
    print(f"Logged in as {bot.user}")

async def load_all_cogs():
    for root, _, files in os.walk("cogs"):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("_") and filename != "match_view.py":
                module = os.path.join(root, filename)[:-3].replace(os.sep, ".")
                try:
                    await bot.load_extension(module)
                    print(f"Loaded cog: {module}")
                except Exception as e:
                    print(f"Failed to load cog: {module}: {e}")

async def main():
    async with bot:
        await load_all_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())