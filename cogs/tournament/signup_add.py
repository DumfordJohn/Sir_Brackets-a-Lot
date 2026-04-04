# cogs/tournament/signup_add.py

import discord
from discord.ext import commands
from tournament_data import load_tournaments, save_tournaments

class SignupAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        tournaments = load_tournaments()

        for name, tournament in tournaments.items():
            if payload.message_id != tournament.get("message_id"):
                continue
        
            signup_emoji = tournament.get("emoji", "🎮")
            if str(payload.emoji) != signup_emoji:
                return

            guild = self.bot.get_guild(payload.guild_id)
            if not guild:
                return

            member = guild.get_member(payload.user_id)
            if not member:
                return

            if any(p["id"] == member.id for p in tournament["players"]):
                return  # Already signed up

            player_entry = {"name": member.display_name, "id": member.id}
            tournament["players"].append(player_entry)
            save_tournaments(tournaments)

            try:
                channel = guild.get_channel(tournament["channel_id"])
                message = await channel.fetch_message(tournament["message_id"])
                embed = message.embeds[0]

                player_names = "\n".join(p["name"] for p in tournament["players"])
                embed.description = f"React with {signup_emoji} to join!\n\n**Players Signed Up:**\n{player_names}"
                await message.edit(embed=embed)
            except Exception as e:
                print(f"Failed to update signup embed: {e}")

            break


async def setup(bot):
    await bot.add_cog(SignupAdd(bot))
