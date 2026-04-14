import discord
import traceback
from discord.ext import commands
from tournament_data import load_tournaments, save_tournaments
from cogs.tournament.formats.singles import single, double
from cogs.tournament.formats.teams import team_single, team_double
from cogs.tournament.team_utils import is_captain

class InteractionListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        print(f"Button clicked: custom_id={custom_id}")
        parts = custom_id.split("|")
        print(f"Parts: {parts} (count: {len(parts)})")

        try:
            # Team button: team|tournament_name|round_index|match_index|winner
            # Team double: team|tournament_name|bracket|round_index|match_index|winner
            if parts[0] == "team":
                await self._handle_team_interaction(interaction, parts)
                return

            # Solo interactions
            if len(parts) == 5:
                await self._handle_double_interaction(interaction, parts)
            elif len(parts) == 4:
                await self._handle_single_interaction(interaction, parts)
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

    async def _handle_team_interaction(self, interaction, parts):
        # parts[0] = "team"
        # Solo team: team|tournament_name|round_index|match_index|winner (5 parts)
        # Double team: team|tournament_name|bracket|round_index|match_index|winner (6 parts)

        tournaments = load_tournaments()

        if len(parts) == 5:
            _, tournament_name, round_index, match_index, winner = parts
            bracket = None
        elif len(parts) == 6:
            _, tournament_name, bracket, round_index, match_index, winner = parts
        else:
            await interaction.response.send_message("Invalid interaction data.", ephemeral=True)
            return

        round_index = int(round_index)
        match_index = int(match_index)
        winner = int(winner)

        tournament = tournaments.get(tournament_name)
        if not tournament:
            await interaction.response.send_message("Tournament not found.", ephemeral=True)
            return

        teams = tournament.get("teams", [])

        # Get the match to find team names
        if bracket and bracket not in ("grand_final", "grand_final_reset"):
            bracket_data = tournament.get(f"{bracket}_bracket", [])
            if round_index >= len(bracket_data) or match_index >= len(bracket_data[round_index]):
                await interaction.response.send_message("Match does not exist.", ephemeral=True)
                return
            match = bracket_data[round_index][match_index]
        elif bracket in ("grand_final", "grand_final_reset"):
            match = tournament.get(bracket, {})
        else:
            rounds = tournament.get("rounds", [])
            if round_index >= len(rounds) or match_index >= len(rounds[round_index]):
                await interaction.response.send_message("Match does not exist.", ephemeral=True)
                return
            match = rounds[round_index][match_index]

        if isinstance(match, (list, tuple)):
            t1, t2 = match
        elif isinstance(match, dict):
            if "winner" in match:
                await interaction.response.send_message("Winner already recorded for this match.", ephemeral=True)
                return
            t1 = match.get("player1")
            t2 = match.get("player2")
        else:
            await interaction.response.send_message("Invalid match data.", ephemeral=True)
            return

        winner_team = t1 if winner == 1 else t2
        loser_team = t2 if winner == 1 else t1

        # Captain check — only the captain of either team can report
        user_id = interaction.user.id
        if not (is_captain(user_id, t1, teams) or is_captain(user_id, t2, teams)):
            await interaction.response.send_message("Only the captain of one of the competing teams can report the result.", ephemeral=True)
            return

        # Record the result
        if bracket and bracket not in ("grand_final", "grand_final_reset"):
            bracket_data[round_index][match_index] = {"player1": t1, "player2": t2, "winner": winner_team, "loser": loser_team}
        elif bracket in ("grand_final", "grand_final_reset"):
            match["winner"] = winner_team
            match["loser"] = loser_team
        else:
            rounds[round_index][match_index] = {"player1": t1, "player2": t2, "winner": winner_team, "loser": loser_team}

        save_tournaments(tournaments)

        tournament_type = tournament.get("type", "single")

        if not bracket:
            # Solo team single elim
            rounds = tournament.get("rounds", [])
            all_finished = all(isinstance(m, dict) and "winner" in m for m in rounds[round_index])
            if not all_finished:
                await interaction.response.send_message(f"Match recorded: **{winner_team} wins!**")
            else:
                await team_single.advance(interaction, tournament, tournament_name, rounds, round_index, winner_team)
        else:
            # Team double elim
            await team_double.advance(interaction, tournament, tournament_name, bracket, round_index, winner_team, loser_team)

        save_tournaments(tournaments)

    async def _handle_double_interaction(self, interaction, parts):
        tournament_name, bracket, round_index, match_index, winner = parts
        round_index = int(round_index)
        match_index = int(match_index)
        winner = int(winner)

        tournaments = load_tournaments()
        tournament = tournaments.get(tournament_name)
        if not tournament:
            await interaction.response.send_message("Tournament not found.", ephemeral=True)
            return

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

        # Defer before advancing to avoid 3s timeout when posting multiple messages
        await interaction.response.defer()
        await double.advance(interaction, tournament, tournament_name, bracket, round_index, winner_name, loser_name)
        save_tournaments(tournaments)

    async def _handle_single_interaction(self, interaction, parts):
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


async def setup(bot):
    await bot.add_cog(InteractionListener(bot))