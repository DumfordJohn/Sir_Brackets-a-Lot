import discord
import random
from cogs.tournament.match_view import MatchView


def make_matchups(players: list) -> list:
    matchups = []
    names = players[:]
    random.shuffle(names)
    for i in range(0, len(names), 2):
        if i + 1 < len(names):
            matchups.append({"player1": names[i], "player2": names[i + 1]})
        else:
            matchups.append({"player1": names[i], "player2": "BYE"})
    return matchups


def get_mention(name: str, players: list) -> str:
    if name == "BYE":
        return "BYE"
    player = next((p for p in players if p["name"] == name), None)
    return f"<@{player['id']}>" if player else name


async def send_match(thread, tournament_name: str, bracket: str, round_index: int, match_index: int, p1: str, p2: str, round_label: str, players: list):
    color = discord.Color.green() if bracket == "winners" else discord.Color.red() if bracket == "losers" else discord.Color.gold()

    p1_mention = get_mention(p1, players)
    p2_mention = get_mention(p2, players) if p2 != "BYE" else "BYE"

    embed = discord.Embed(
        title=f"{round_label} - Match {match_index + 1}: {p1} vs {p2}",
        description="Click a button below to report the winner.",
        color=color
    )
    embed.add_field(name="Bracket", value=bracket.title(), inline=True)
    embed.add_field(name="Participants", value=f"{p1_mention} vs {p2_mention}", inline=False)

    view = MatchView(
        tournament_name=f"{tournament_name}|{bracket}",
        round_index=round_index,
        match_index=match_index,
        player1=p1,
        player2=p2
    )
    await thread.send(f"{p1_mention} vs {p2_mention}", embed=embed, view=view)


async def start(interaction: discord.Interaction, tournament_name: str, tournament: dict, players: list, thread):
    names = [p["name"] for p in players]
    random.shuffle(names)
    matchups = make_matchups(names)

    tournament["winners_bracket"] = [matchups]
    tournament["losers_bracket"] = []
    tournament["grand_final"] = None
    tournament["grand_final_reset"] = None
    # losers_pool: players waiting to enter losers bracket from winners bracket
    tournament["losers_pool"] = []
    # losers_survivors: players who survived the last losers bracket round
    tournament["losers_survivors"] = []
    # track whether the next losers round should combine survivors + new dropdowns
    tournament["losers_awaiting_drop"] = False

    await thread.send("**Winners Bracket - Round 1**")
    for i, match in enumerate(matchups):
        await send_match(thread, tournament_name, "winners", 0, i, match["player1"], match["player2"], "Winners R1", players)


async def advance(interaction: discord.Interaction, tournament: dict, tournament_name: str, bracket: str, round_index: int, winner_name: str, loser_name: str):
    thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
    if not thread:
        await interaction.followup.send("Could not find tournament thread.", ephemeral=True)
        return

    players = tournament.get("players", [])

    if bracket == "winners":
        await _advance_winners(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread, players)
    elif bracket == "losers":
        await _advance_losers(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread, players)
    elif bracket == "grand_final":
        await _advance_grand_final(interaction, tournament, tournament_name, winner_name, loser_name, thread, players)
    elif bracket == "grand_final_reset":
        await _advance_grand_final_reset(interaction, tournament, tournament_name, winner_name, thread)


async def _advance_winners(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread, players):
    winners_bracket = tournament["winners_bracket"]
    current_round = winners_bracket[round_index]

    all_done = all("winner" in m for m in current_round)
    if not all_done:
        await interaction.followup.send(f"Match recorded: **{winner_name} wins!**")
        return

    winners = [m["winner"] for m in current_round]
    new_losers = [m["loser"] for m in current_round if m.get("loser") and m["loser"] != "BYE"]

    # Winners bracket is done — last player standing
    if len(winners) == 1:
        tournament["winners_champion"] = winners[0]
        await interaction.followup.send(f"Match recorded: **{winner_name} wins!**")
        await thread.send(f"**{winners[0]}** is the Winners Bracket Champion! Waiting for Losers Bracket Champion...")

        # Feed any remaining new losers into losers bracket before grand final
        if new_losers:
            tournament["losers_pool"].extend(new_losers)
            await _post_next_losers_round(tournament, tournament_name, thread, players)

        await _try_start_grand_final(interaction, tournament, tournament_name, thread, players)
        return

    # Advance winners bracket
    next_round_index = len(winners_bracket)
    next_matchups = make_matchups(winners)
    winners_bracket.append(next_matchups)

    # Add new losers to pool and start losers round
    tournament["losers_pool"].extend(new_losers)
    await _post_next_losers_round(tournament, tournament_name, thread, players)

    await thread.send(f"**Winners Bracket - Round {next_round_index + 1}**")
    for i, match in enumerate(next_matchups):
        await send_match(thread, tournament_name, "winners", next_round_index, i, match["player1"], match["player2"], f"Winners R{next_round_index + 1}", players)

    await interaction.followup.send(f"Match recorded: **{winner_name} wins!** Next round posted.")


async def _post_next_losers_round(tournament, tournament_name, thread, players):
    """Determine and post the next losers bracket round."""
    losers_pool = tournament.get("losers_pool", [])       # New dropdowns from winners
    losers_survivors = tournament.get("losers_survivors", [])  # Survived last losers round
    losers_bracket = tournament["losers_bracket"]
    round_index = len(losers_bracket)

    if losers_survivors and losers_pool:
        # Pair survivors with new dropdowns
        combined = list(zip(losers_survivors, losers_pool))
        leftover_survivors = losers_survivors[len(losers_pool):]
        leftover_pool = losers_pool[len(losers_survivors):]

        matchups = [{"player1": s, "player2": d} for s, d in combined]
        # Handle any leftovers
        for p in leftover_survivors + leftover_pool:
            matchups.append({"player1": p, "player2": "BYE"})

        tournament["losers_pool"] = []
        tournament["losers_survivors"] = []

    elif losers_pool and not losers_survivors:
        # First losers round — just pool new losers against each other
        if len(losers_pool) < 2:
            return
        matchups = make_matchups(losers_pool)
        tournament["losers_pool"] = []
        tournament["losers_survivors"] = []

    elif losers_survivors and not losers_pool:
        # Survivors play each other
        if len(losers_survivors) < 2:
            return
        matchups = make_matchups(losers_survivors)
        tournament["losers_survivors"] = []

    else:
        return

    losers_bracket.append(matchups)

    await thread.send(f"**Losers Bracket - Round {round_index + 1}**")
    for i, match in enumerate(matchups):
        await send_match(thread, tournament_name, "losers", round_index, i, match["player1"], match["player2"], f"Losers R{round_index + 1}", players)


async def _advance_losers(interaction, tournament, tournament_name, round_index, winner_name, loser_name, thread, players):
    losers_bracket = tournament["losers_bracket"]
    current_round = losers_bracket[round_index]

    all_done = all("winner" in m for m in current_round)
    if not all_done:
        await interaction.followup.send(f"Match recorded: **{winner_name} wins!**")
        return

    survivors = [m["winner"] for m in current_round if m["winner"] != "BYE"]

    if len(survivors) == 1:
        tournament["losers_champion"] = survivors[0]
        await interaction.followup.send(f"Match recorded: **{winner_name} wins!**")
        await thread.send(f"**{survivors[0]}** is the Losers Bracket Champion!")
        await _try_start_grand_final(interaction, tournament, tournament_name, thread, players)
        return

    # Store survivors and post next round
    tournament["losers_survivors"] = survivors
    await _post_next_losers_round(tournament, tournament_name, thread, players)

    await interaction.followup.send(f"Match recorded: **{winner_name} wins!** Next losers round posted.")


async def _try_start_grand_final(interaction, tournament, tournament_name, thread, players):
    winners_champ = tournament.get("winners_champion")
    losers_champ = tournament.get("losers_champion")

    if not winners_champ or not losers_champ:
        return

    w_mention = get_mention(winners_champ, players)
    l_mention = get_mention(losers_champ, players)

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
    embed.add_field(name="Participants", value=f"{w_mention} vs {l_mention}", inline=False)
    embed.add_field(name="Note", value=f"If {losers_champ} wins, a reset match will be played!", inline=False)
    await thread.send(f"**Grand Final: {winners_champ} vs {losers_champ}**\n_{winners_champ} comes from the Winners Bracket — {losers_champ} must win twice!_")
    await thread.send(f"{w_mention} vs {l_mention}", embed=embed, view=view)


async def _advance_grand_final(interaction, tournament, tournament_name, winner_name, loser_name, thread, players):
    winners_champ = tournament.get("winners_champion")

    if winner_name == winners_champ:
        tournament["grand_final"]["winner"] = winner_name
        winner_mention = get_mention(winner_name, players)
        await interaction.followup.send(f"**{winner_name}** wins the tournament!")
        await thread.send(f"{winner_mention} is the tournament champion!")
    else:
        tournament["grand_final"]["winner"] = winner_name
        tournament["grand_final_reset"] = {"player1": winners_champ, "player2": winner_name}

        w_mention = get_mention(winners_champ, players)
        l_mention = get_mention(winner_name, players)

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
        embed.add_field(name="Participants", value=f"{w_mention} vs {l_mention}", inline=False)
        await interaction.followup.send(f"Match recorded: **{winner_name} wins!** Grand Final Reset incoming!")
        await thread.send(f"**Grand Final Reset!** Both players are now 1-1. One final match!")
        await thread.send(f"{w_mention} vs {l_mention}", embed=embed, view=view)


async def _advance_grand_final_reset(interaction, tournament, tournament_name, winner_name, thread):
    players = tournament.get("players", [])
    tournament["grand_final_reset"]["winner"] = winner_name
    winner_mention = get_mention(winner_name, players)
    await interaction.followup.send(f"**{winner_name}** wins the tournament!")
    await thread.send(f"{winner_mention} is the tournament champion!")