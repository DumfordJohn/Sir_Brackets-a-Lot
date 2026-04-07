import discord
from bot_config import get_guild_config

def is_tournament_admin(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    
    guild_config = get_guild_config(member.guild.id)
    tournament_role_id = guild_config.get("tournament_role_id")

    if tournament_role_id:
        return any(role.id == tournament_role_id for role in member.roles)
    
    return False