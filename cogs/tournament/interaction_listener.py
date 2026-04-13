# cogs/tournament/interaction_listener.py

import discord
import traceback
from discord.ext import commands
from tournament_data import load_tournaments, save_tournaments
from cogs.tournament.formats import single, double

class InteractionListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        parts = custom_id.split("|")

        try:
            if len(parts) == 5:
                tournament_name, bracket, round_index, match_index, winner = parts
                round_index = int(round_index)
                match_index = int(match_index)
                winner = int(winner)

                tournaments = load_tournaments()
                tournament = tournaments.get(tournament_name)
                if not tournament:
                    await interaction.response.send_message("Tournament not found.", ephemeral=True)
                    return

                if bracket == "rr":
                    matches = tournament.get("rr_matches", [])
                    if match_index >= len(matches):
                        await interaction.response.send_message("Match does not exist.", ephemeral=True)
                        return

                    match = matches[match_index]
                    if "winner" in match:
                        await interaction.response.send_message("Winner already recorded for this match.", ephemeral=True)
                        return

                    p1 = match["player1"]
                    p2 = match["player2"]
                    winner_name = p1 if winner == 1 else p2
                    loser_name = p2 if winner == 1 else p1

                    match["winner"] = winner_name
                    match["loser"] = loser_name
                    save_tournaments(tournaments)

                    await roundrobin.advance(interaction, tournament, tournament_name, match_index, winner_name, loser_name)
                    save_tournaments(tournaments)
                    return

                if bracket in ("winners", "losers", "grand_final", "grand_final_reset"):
                    if bracket == "winners":
                        bracket_data = tournament.get("winners_bracket", [])
                    elif bracket == "losers":
                        bracket_data = tournament.get("losers_bracket", [])
                    elif bracket in ("grand_final", "grand_final_reset"):
                        bracket_data = [[tournament.get(bracket, {})]]
                        round_index = 0
                        match_index = 0
                    else:
                        await interaction.response.send_message("Unknown bracket type.", ephemeral=True)
                        return

                    if bracket not in ("grand_final", "grand_final_reset"):
                        if round_index >= len(bracket_data) or match_index >= len(bracket_data[round_index]):
                            await interaction.response.send_message("Match does not exist.", ephemeral=True)
                            return
                        match = bracket_data[round_index][match_index]
                    else:
                        match = tournament.get(bracket, {})

                    if "winner" in match:
                        await interaction.response.send_message("Winner already recorded for this match.", ephemeral=True)
                        return

                    p1 = match["player1"]
                    p2 = match["player2"]
                    winner_name = p1 if winner == 1 else p2
                    loser_name = p2 if winner == 1 else p1

                    match["winner"] = winner_name
                    match["loser"] = loser_name
                    save_tournaments(tournaments)

                    await double.advance(interaction, tournament, tournament_name, bracket, round_index, winner_name, loser_name)
                    save_tournaments(tournaments)
                    return

            elif len(parts) == 4:
                tournament_name, round_index, match_index, winner = parts
                round_index = int(round_index)
                match_index = int(match_index)
                winner = int(winner)

                tournaments = load_tournaments()
                tournament = tournaments.get(tournament_name)
                if not tournament:
                    await interaction.response.send_message("Tournament not found.", ephemeral=True)
                    return

                rounds = tournament.get("rounds", [])
                if round_index >= len(rounds) or match_index >= len(rounds[round_index]):
                    await interaction.response.send_message("Match does not exist.", ephemeral=True)
                    return

                match = rounds[round_index][match_index]

                if isinstance(match, (list, tuple)):
                    p1, p2 = match
                elif isinstance(match, dict):
                    if "winner" in match:
                        await interaction.response.send_message("Winner already chosen for this match.", ephemeral=True)
                        return
                    p1 = match.get("player1")
                    p2 = match.get("player2")
                else:
                    await interaction.response.send_message("Invalid match data.", ephemeral=True)
                    return

                winner_name = p1 if winner == 1 else p2
                rounds[round_index][match_index] = {"player1": p1, "player2": p2, "winner": winner_name}
                save_tournaments(tournaments)

                all_finished = all(isinstance(m, dict) and "winner" in m for m in rounds[round_index])
                if not all_finished:
                    await interaction.response.send_message(f"Match recorded: **{winner_name} wins!**")
                    return

                await single.advance(interaction, tournament, tournament_name, rounds, round_index, winner_name)
                save_tournaments(tournaments)

            else:
                print(f"Unexpected number of parts: {len(parts)}")
                return

        except Exception as e:
            print(f"Error handling interaction: {e}")
            traceback.print_exc()
            try:
                await interaction.response.send_message("An error occurred processing this interaction.", ephemeral=True)
            except:
                pass


async def setup(bot):
    await bot.add_cog(InteractionListener(bot))