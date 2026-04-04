import discord
from discord.ext import commands
from tournament_data import load_tournaments, save_tournaments

class SignupRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        tournaments = load_tournaments()

        for name, tournament in tournaments.items():
            if payload.message_id == tournament.get("message_id"):
                signup_emoji = tournament.get("emoji", "🎮")
                if str(payload.emoji) != signup_emoji:
                    return
                
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                if not member:
                    return

                original_count = len(tournament["players"])
                tournament["players"] = [
                    p for p in tournament["players"] if p["id"] != member.id
                ]

                if len(tournament["players"]) == original_count:
                    return  # User wasn't signed up anyway

                save_tournaments(tournaments)

                # Update the embed
                channel = guild.get_channel(tournament["channel_id"])
                message = await channel.fetch_message(tournament["message_id"])
                embed = message.embeds[0]

                if tournament["players"]:
                    names = "\n".join([p["name"] for p in tournament["players"]])
                    embed.description = f"React with {signup_emoji} to join!\n\n**Players Signed Up:**\n{names}"
                else:
                    embed.description = f"React with {signup_emoji} to join!\n\n**No players signed up yet.**"

                await message.edit(embed=embed)
                break


async def setup(bot):
    await bot.add_cog(SignupRemove(bot))
