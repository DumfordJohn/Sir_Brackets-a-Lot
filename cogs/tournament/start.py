import discord
import random
from discord.ext import commands
from discord import app_commands
from tournament_data import load_tournaments, save_tournaments
from .match_view import MatchView

class TournamentStart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tournaments = load_tournaments()

    @app_commands.command(name="start_tournament", description="Start a tournament and create matches.")
    @app_commands.describe(name="The name of the tournament to start")
    async def start_tournament(self, interaction: discord.Interaction, name: str):
        print("Received start_tournament command")
        await interaction.response.defer()

        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("\u274c You must be an admin to start a tournament.", ephemeral=True)
            return

        if name not in self.tournaments:
            await interaction.followup.send(f"\u274c Tournament `{name}` does not exist.", ephemeral=True)
            return

        tournament = self.tournaments[name]
        players = tournament.get("players", [])

        if len(players) < 2:
            await interaction.followup.send("\u274c Not enough players to start the tournament.", ephemeral=True)
            return

        random.shuffle(players)
        matchups = []

        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                matchups.append((players[i]["name"], players[i + 1]["name"]))
            else:
                matchups.append((players[i]["name"], "BYE"))

        channel = interaction.guild.get_channel(tournament["channel_id"])
        if not channel:
            await interaction.followup.send("Could not find the sign-ups channel.", ephemeral=True)
            return

        try:
            signup_message = await channel.fetch_message(tournament["message_id"])
        except Exception as e:
            print(f"\u274c Error fetching message: {e}")
            await interaction.followup.send("\u274c Could not fetch the original signup message.", ephemeral=True)
            return

        thread = await signup_message.create_thread(
            name=f"{name} Bracket",
            auto_archive_duration=60,
            reason="Tournament start"
        )

        for i, (p1, p2) in enumerate(matchups):
            p1_data = next((p for p in players if p["name"] == p1), None)
            p2_data = next((p for p in players if p["name"] == p2), None)

            p1_mention = f"<@{p1_data['id']}>" if p1_data else p1
            p2_mention = f"<@{p2_data['id']}>" if p2_data else p2

            embed = discord.Embed(
                title=f"Match {i + 1}: {p1} vs {p2}",
                description="Click a button below to report the winner.",
                color=discord.Color.green()
            )
            embed.add_field(name="Participants", value=f"{p1_mention} vs {p2_mention}", inline=False)

            view = MatchView(
                tournament_name=name,
                round_index=0,
                match_index=i,
                player1=p1,
                player2=p2
            )

            await thread.send(embed=embed, view=view)

        tournament["rounds"] = [matchups]
        save_tournaments(self.tournaments)

        await interaction.followup.send(f"\u2705 Tournament `{name}` has started! Matches posted in {thread.mention}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TournamentStart(bot))
