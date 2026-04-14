import discord
import random
from cogs.tournament.team_match_view import TeamMatchView


def get_captain(team_name: str, teams: list) -> dict:
    for team in teams:
        if team["name"] == team_name:
            return {"id": team["captain_id"], "name": team["captain_name"]}
    return {}


async def send_match(thread, tournament_name: str, round_index: int, match_index: int, team1: str, team2: str, teams: list, round_label: str):
    cap1 = get_captain(team1, teams)
    cap2 = get_captain(team2, teams)

    cap1_mention = f"<@{cap1['id']}>" if cap1 else team1
    cap2_mention = f"<@{cap2['id']}>" if cap2 else team2

    embed = discord.Embed(
        title=f"{round_label} - Match {match_index + 1}: {team1} vs {team2}",
        description="Captains: click a button below to report the winner.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Captains", value=f"{cap1_mention} vs {cap2_mention}", inline=False)

    view = TeamMatchView(
        tournament_name=tournament_name,
        round_index=round_index,
        match_index=match_index,
        team1=team1,
        team2=team2,
        captain1_id=cap1.get("id"),
        captain2_id=cap2.get("id")
    )
    await thread.send(f"{cap1_mention} vs {cap2_mention}", embed=embed, view=view)


async def start(interaction: discord.Interaction, tournament_name: str, tournament: dict, teams: list, thread):
    team_names = [t["name"] for t in teams]
    random.shuffle(team_names)

    matchups = []
    for i in range(0, len(team_names), 2):
        if i + 1 < len(team_names):
            matchups.append((team_names[i], team_names[i + 1]))
        else:
            matchups.append((team_names[i], "BYE"))

    for i, (t1, t2) in enumerate(matchups):
        await send_match(thread, tournament_name, 0, i, t1, t2, teams, "Round 1")

    tournament["rounds"] = [matchups]


async def advance(interaction: discord.Interaction, tournament: dict, tournament_name: str, rounds: list, round_index: int, winner_name: str):
    teams = tournament.get("teams", [])
    winners = [m["winner"] for m in rounds[round_index]]

    if len(winners) == 1:
        await interaction.response.send_message(f"Tournament **{tournament_name}** is over! Winner: **{winners[0]}**")
        return

    random.shuffle(winners)
    next_round = [
        (winners[i], winners[i + 1]) if i + 1 < len(winners) else (winners[i], "BYE")
        for i in range(0, len(winners), 2)
    ]

    new_round_index = len(rounds)
    tournament["rounds"].append(next_round)

    thread = interaction.channel if isinstance(interaction.channel, discord.Thread) else None
    if thread:
        await thread.send(f"Round {round_index + 1} complete! Starting Round {round_index + 2}...")
        for i, (t1, t2) in enumerate(next_round):
            await send_match(thread, tournament_name, new_round_index, i, t1, t2, teams, f"Round {round_index + 2}")

    await interaction.response.send_message(f"Match recorded: **{winner_name} wins!** Next round posted.")