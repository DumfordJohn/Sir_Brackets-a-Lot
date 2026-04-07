import discord
from discord.ext import commands
from discord import Interaction, app_commands
from bot_config import get_guild_config, set_guild_config

class SetupBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_bot", description="Setup the bot for your server")
    @app_commands.describe(role="The role that will have tournament admin permissions", channel="The channel where tournament sign-up messages will be posted.")
    async def setup_bot(self, interaction: discord.Interaction, role: discord.Role, channel: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be a server admin to run this command.", emphemeral=True)
            return
        
        guild_config = get_guild_config(interaction.guild.id)
        guild_config["tournament_admin_role_id"] = role.id
        guild_config["signup_channel_id"] = channel.id
        set_guild_config(interaction.guild.id, guild_config)
    
        await interaction.response.send_message(f"Bot Configured!\n"
                                                f"Tournament Admin Role: **{role.name}**\n"
                                                f"Sign-Up Channel: {channel.mention}",
                                                ephemeral=True)

    @app_commands.command(name="get_bot_setup", description="Get the current bot configuration for your server.")
    async def get_bot_setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be a server admin to run this command.", emphemeral=True)
            return
        
        guild_config = get_guild_config(interaction.guild.id)
        role_id = guild_config.get("tournament_admin_role_id")
        channel_id = guild_config.get("signup_channel_id")

        lines = []
        
        if role_id:
            role = interaction.guild.get_role(role_id)
            lines.append(f"- Tournament admin role: **{role.name}**" if role else "- Tournament admin role: *role no longer exists, please reconfigure*")
        else:
            lines.append("- Tournament admin role: *not set*")
        
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            lines.append(f"- Sign-up channel: {channel.mention}" if channel else "- Sign-up channel: *channel no longer exists, please reconfigure*")
        else:
            lines.append("- Sign-up channel: *not set, defaulting to #sign-ups*")
        
        await interaction.response.send_message("\n".join(lines), ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetupBot(bot))