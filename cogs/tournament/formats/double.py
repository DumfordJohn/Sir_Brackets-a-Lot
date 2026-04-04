import discord
import random
from cogs.tournament.match_view import MatchView


def make_matchups(players: list) -> list:
    matchups = []
    for i in range(0, len(players), 2):
        if i + 1 < len(players):
            matchups.append({"player1": players[i], "player2": players[i + 1]})
        else:
            matchups.append({"player1": players[i], "player2": "BYE"})
    return matchups


async def send_match(thread, tournament_name: str, bracket: str, round_index: int, match_index: int, p1: str, p2: str, round_label: str):
    color = discord.Color.green() if bracket == "winners" else discord.Color.red() if bracket == "losers" else discord.Color.gold()
    embed = discord.Embed(
        title=f"{round_label} - Match {match_index + 1}: {p1} vs {p2}",
        description="Click a button below to report the winner.",
        color=color
    )
    embed.add_field(name="Bracket", value=bracket.title(), inline=True)
    embed.add_field(name="Participants", value=f"{p1} vs {p2}", inline=False)

    view = MatchView(
        tournament_name=f"{tournament_name}|{bracket}",
        round_index=round_index,
        match_index=match_index,
        player1=p1,
        player2=p2
    )
    await thread.send(embed=embed, view=view)


async def start(interaction: discord.Interaction, tournament_name: str, tournament: dict, players: list, thread):
    names = [p["name"] for p in players]
    random.shuffle(names)

    matchups = make_matchups(names)

    tournament["winners_bracket"] = [matchups]
    tournament["losers_bracket"] = []
    tournament["grand_final"] = None
    tournament["grand_final_reset"] = None
    tournament["losers_pool"] = []

    await thread.send("**Winners Bracket - Round 1**")
    for i, match in enumerate(matchups):
        await send_match(thread, tournament_name, "winners", 0, i, match["player1"], match["player2"], "Winners R1")


async def advance(interaction: discord.Interaction, tournament: dict, tournament_name: str, bracket: str, round_index: int, winner_name: str, loser_name: str):
    thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
    if not thread:
        await interaction.response.send_message("Could not find tournament thread.", ephemeral=True)
        return

    if bracket == "winners":
        await _advance_winners(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread)
    elif bracket == "losers":
        await _advance_losers(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread)
    elif bracket == "grand_final":
        await _advance_grand_final(interaction, tournament, tournament_name, winner_name, loser_name, thread)
    elif bracket == "grand_final_reset":
        await _advance_grand_final_reset(interaction, tournament, tournament_name, winner_name, thread)


async def _advance_winners(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread):
    winners_bracket = tournament["winners_bracket"]
    current_round = winners_bracket[round_index]

    all_done = all("winner" in m for m in current_round)
    if not all_done:
        await interaction.response.send_message(f"Match recorded: **{winner_name} wins!**")
        return

    winners = [m["winner"] for m in current_round]
    losers = [m["loser"] for m in current_round if m.get("loser") and m["loser"] != "BYE"]

    tournament["losers_pool"].extend(losers)

    if len(winners) == 1:
        tournament["winners_champion"] = winners[0]
        await interaction.response.send_message(f"Match recorded: **{winner_name} wins!**")
        await thread.send(f"**{winners[0]}** is the Winners Bracket Champion! Waiting for Losers Bracket Champion...")
        await _try_start_grand_final(interaction, tournament, tournament_name, thread)
        return

    next_round_index = len(winners_bracket)
    next_matchups = make_matchups(winners)
    winners_bracket.append(next_matchups)

    await _start_losers_round(tournament, tournament_name, thread)

    await thread.send(f"**Winners Bracket - Round {next_round_index + 1}**")
    for i, match in enumerate(next_matchups):
        await send_match(thread, tournament_name, "winners", next_round_index, i, match["player1"], match["player2"], f"Winners R{next_round_index + 1}")

    await interaction.response.send_message(f"Match recorded: **{winner_name} wins!** Next round posted.")


async def _start_losers_round(tournament, tournament_name, thread):
    losers_pool = tournament.get("losers_pool", [])
    if len(losers_pool) < 2:
        return

    losers_bracket = tournament["losers_bracket"]
    round_index = len(losers_bracket)
    matchups = make_matchups(losers_pool)
    losers_bracket.append(matchups)
    tournament["losers_pool"] = []

    await thread.send(f"**Losers Bracket - Round {round_index + 1}**")
    for i, match in enumerate(matchups):
        await send_match(thread, tournament_name, "losers", round_index, i, match["player1"], match["player2"], f"Losers R{round_index + 1}")


async def _advance_losers(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread):
    losers_bracket = tournament["losers_bracket"]
    current_round = losers_bracket[round_index]

    all_done = all("winner" in m for m in current_round)
    if not all_done:
        await interaction.response.send_message(f"Match recorded: **{winner_name} wins!**")
        return

    survivors = [m["winner"] for m in current_round]

    if len(survivors) == 1:
        tournament["losers_champion"] = survivors[0]
        await interaction.response.send_message(f"Match recorded: **{winner_name} wins!**")
        await thread.send(f"**{survivors[0]}** is the Losers Bracket Champion!")
        await _try_start_grand_final(interaction, tournament, tournament_name, thread)
        return

    next_round_index = len(losers_bracket)
    next_matchups = make_matchups(survivors)
    losers_bracket.append(next_matchups)

    await thread.send(f"**Losers Bracket - Round {next_round_index + 1}**")
    for i, match in enumerate(next_matchups):
        await send_match(thread, tournament_name, "losers", next_round_index, i, match["player1"], match["player2"], f"Losers R{next_round_index + 1}")

    await interaction.response.send_message(f"Match recorded: **{winner_name} wins!** Next round posted.")


async def _try_start_grand_final(interaction, tournament, tournament_name, thread):
    winners_champ = tournament.get("winners_champion")
    losers_champ = tournament.get("losers_champion")

    if not winners_champ or not losers_champ:
        return

    await thread.send(f"**Grand Final: {winners_champ} vs {losers_champ}**\n_{winners_champ} comes from the Winners Bracket — {losers_champ} must win twice!_")

    tournament["grand_final"] = {"player1": winners_champ, "player2": losers_champ}

    view = MatchView(
        tournament_name=f"{tournament_name}|grand_final",
        round_index=0,
        match_index=0,
        player1=winners_champ,
        player2=losers_champ
    )
    embed = discord.Embed(
        title=f"Grand Final: {winners_champ} vs {losers_champ}",
        description="Click a button below to report the winner.",
        color=discord.Color.gold()
    )
    embed.add_field(name="Note", value=f"If {losers_champ} wins, a reset match will be played!", inline=False)
    await thread.send(embed=embed, view=view)


async def _advance_grand_final(interaction, tournament, tournament_name, winner_name, loser_name, thread):
    winners_champ = tournament.get("winners_champion")

    if winner_name == winners_champ:
        tournament["grand_final"]["winner"] = winner_name
        await interaction.response.send_message(f"**{winner_name}** wins the tournament!")
        await thread.send(f"**{winner_name}** is the tournament champion!")
    else:
        tournament["grand_final"]["winner"] = winner_name
        tournament["grand_final_reset"] = {"player1": winners_champ, "player2": winner_name}

        await interaction.response.send_message(f"Match recorded: **{winner_name} wins!** Grand Final Reset incoming!")
        await thread.send(f"**Grand Final Reset!** Both players are now 1-1. One final match!")

        view = MatchView(
            tournament_name=f"{tournament_name}|grand_final_reset",
            round_index=0,
            match_index=0,
            player1=winners_champ,
            player2=winner_name
        )
        embed = discord.Embed(
            title=f"Grand Final Reset: {winners_champ} vs {winner_name}",
            description="Click a button below to report the winner.",
            color=discord.Color.gold()
        )
        await thread.send(embed=embed, view=view)


async def _advance_grand_final_reset(interaction, tournament, tournament_name, winner_name, thread):
    tournament["grand_final_reset"]["winner"] = winner_name
    await interaction.response.send_message(f"**{winner_name}** wins the tournament!")
    await thread.send(f"**{winner_name}** is the tournament champion!")