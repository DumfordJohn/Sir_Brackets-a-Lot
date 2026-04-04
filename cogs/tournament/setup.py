# cogs/tournament/setup.py

import discord
from discord.ext import commands
from discord import app_commands
from tournament_data import load_tournaments, save_tournaments

class TournamentSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_tournament", description="Create a new tournament.")
    @app_commands.describe(
        name="Name of the tournament",
        type="Tournament type (single, double, roundrobin)",
        emoji="Emoji players react with to sign up (default: 🎮)"
    )
    async def create_tournament(self, interaction: discord.Interaction, name: str, type: str, emoji: str = "🎮"):
        await interaction.response.defer(ephemeral=True)
        print(f"Received create_tournament: name={name}, type={type}, emoji={emoji}")

        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("You must be an admin to use this command.", ephemeral=True)
            return

        tournaments = load_tournaments()

        if name in tournaments:
            await interaction.followup.send(f"Tournament `{name}` already exists.", ephemeral=True)
            return

        if type not in ["single", "double", "roundrobin"]:
            await interaction.followup.send(
                "Invalid type. Use: `single`, `double`, or `roundrobin`.", ephemeral=True
            )
            return

        signup_channel = discord.utils.get(interaction.guild.text_channels, name="sign-ups")
        if not signup_channel:
            await interaction.followup.send("Could not find a #sign-ups channel.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{name} Tournament Sign-Up",
            description=f"React with {emoji} to join!",
            color=discord.Color.green()
        )

        try:
            signup_message = await signup_channel.send(embed=embed)
            await signup_message.add_reaction(emoji)
        except Exception as e:
            print(f"Failed to send or react to message: {e}")
            await interaction.followup.send("Failed to post sign-up message.", ephemeral=True)
            return

        tournaments[name] = {
            "type": type,
            "players": [],
            "emoji": emoji,
            "message_id": signup_message.id,
            "channel_id": signup_channel.id
        }

        try:
            save_tournaments(tournaments)
            print(f"Tournament saved: {name}")
        except Exception as e:
            print(f"Failed to save tournament: {e}")
            await interaction.followup.send("Failed to save tournament data.", ephemeral=True)
            return

        await interaction.followup.send(
            f"Tournament `{name}` created and posted in {signup_channel.mention}.", ephemeral=False
        )


async def setup(bot):
    await bot.add_cog(TournamentSetup(bot))
