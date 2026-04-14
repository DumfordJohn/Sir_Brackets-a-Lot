import discord
from discord.ui import View, Button


class TeamMatchView(View):
    def __init__(self, tournament_name: str, round_index: int, match_index: int, team1: str, team2: str, captain1_id: int, captain2_id: int):
        super().__init__(timeout=None)
        self.tournament_name = tournament_name
        self.round_index = round_index
        self.match_index = match_index
        self.team1 = team1
        self.team2 = team2
        self.captain1_id = captain1_id
        self.captain2_id = captain2_id

        self.add_item(Button(
            label=team1,
            style=discord.ButtonStyle.success,
            custom_id=f"team|{tournament_name}|{round_index}|{match_index}|1"
        ))

        self.add_item(Button(
            label=team2,
            style=discord.ButtonStyle.success,
            custom_id=f"team|{tournament_name}|{round_index}|{match_index}|2"
        ))