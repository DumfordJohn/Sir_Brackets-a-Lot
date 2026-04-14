import discord
from discord.ext import commands
from discord import app_commands
from tournament_data import load_tournaments, save_tournaments
from permissions import is_tournament_admin
from cogs.tournament.team_utils import assign_teams
from cogs.tournament.formats.singles import single, double
from cogs.tournament.formats.teams import team_single, team_double

class TournamentStart(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="start_tournament", description="Start a tournament and create matches.")
    @app_commands.describe(name="The name of the tournament to start")
    async def start_tournament(self, interaction: discord.Interaction, name: str):
        print("Received start_tournament command")
        await interaction.response.defer()

        if not is_tournament_admin(interaction.user):
            await interaction.followup.send("You must be a tournament admin to start a tournament.", ephemeral=True)
            return

        tournaments = load_tournaments()

        if name not in tournaments:
            await interaction.followup.send(f"Tournament `{name}` does not exist.", ephemeral=True)
            return

        tournament = tournaments[name]
        players = tournament.get("players", [])
        mode = tournament.get("mode", "solo")
        tournament_type = tournament.get("type", "single")

        if len(players) < 2:
            await interaction.followup.send("Not enough players to start the tournament.", ephemeral=True)
            return

        # Team mode validation
        if mode == "team":
            teamsize = tournament.get("teamsize")
            if len(players) % teamsize != 0:
                await interaction.followup.send(
                    f"Player count ({len(players)}) is not divisible by team size ({teamsize}). "
                    f"You need a multiple of {teamsize} players to start.",
                    ephemeral=True
                )
                return

        channel = interaction.guild.get_channel(tournament["channel_id"])
        if not channel:
            await interaction.followup.send("Could not find the sign-ups channel.", ephemeral=True)
            return

        try:
            signup_message = await channel.fetch_message(tournament["message_id"])
        except Exception as e:
            print(f"Error fetching message: {e}")
            await interaction.followup.send("Could not fetch the original signup message.", ephemeral=True)
            return

        thread = await signup_message.create_thread(
            name=f"{name} Bracket",
            auto_archive_duration=60,
            reason="Tournament start"
        )

        if mode == "team":
            teamsize = tournament.get("teamsize")
            teams = assign_teams(players, teamsize)
            tournament["teams"] = teams

            # Post team assignments
            lines = []
            for team in teams:
                member_names = ", ".join(p["name"] for p in team["players"])
                lines.append(f"**{team['name']}** (Captain: {team['captain_name']}): {member_names}")
            await thread.send("**Team Assignments:**\n" + "\n".join(lines))

            if tournament_type == "single":
                await team_single.start(interaction, name, tournament, teams, thread)
            elif tournament_type == "double":
                await team_double.start(interaction, name, tournament, teams, thread)
        else:
            if tournament_type == "single":
                await single.start(interaction, name, tournament, players, thread)
            elif tournament_type == "double":
                await double.start(interaction, name, tournament, players, thread)

        save_tournaments(tournaments)
        await interaction.followup.send(f"Tournament `{name}` has started! Matches posted in {thread.mention}.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TournamentStart(bot))