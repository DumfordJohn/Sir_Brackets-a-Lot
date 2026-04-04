import discord
import random
from tournament_data import load_tournaments, save_tournaments
from cogs.tournament.match_view import MatchView


async def start(interaction: discord.Interaction, tournament_name: str, tournament: dict, players: list, thread):
    random.shuffle(players)
    matchups = []

    for i in range(0, len(players), 2):
        if i + 1 < len(players):
            matchups.append((players[i]["name"], players[i + 1]["name"]))
        else:
            matchups.append((players[i]["name"], "BYE"))

    for i, (p1, p2) in enumerate(matchups):
        p1_data = next((p for p in players if p["name"] == p1), None)
        p2_data = next((p for p in players if p["name"] == p2), None)

        p1_mention = f"<@{p1_data['id']}>" if p1_data else p1
        p2_mention = f"<@{p2_data['id']}>" if p2_data else p2

        embed = discord.Embed(
            title=f"Match {i + 1}: {p1} vs {p2}",
            description="Click a button below to report the winner.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Participants", value=f"{p1_mention} vs {p2_mention}", inline=False)

        view = MatchView(
            tournament_name=tournament_name,
            round_index=0,
            match_index=i,
            player1=p1,
            player2=p2
        )
        await thread.send(embed=embed, view=view)

    tournament["rounds"] = [matchups]


async def advance(interaction: discord.Interaction, tournament: dict, tournament_name: str, rounds: list, round_index: int, winner_name: str):
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
        for i, (p1, p2) in enumerate(next_round):
            embed = discord.Embed(
                title=f"Round {round_index + 2} - Match {i + 1}: {p1} vs {p2}",
                description="Click a button below to report the winner.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Participants", value=f"{p1} vs {p2}", inline=False)

            view = MatchView(
                tournament_name=tournament_name,
                round_index=new_round_index,
                match_index=i,
                player1=p1,
                player2=p2
            )
            await thread.send(embed=embed, view=view)

    await interaction.response.send_message(f"Match recorded: **{winner_name} wins!** Next round posted.")