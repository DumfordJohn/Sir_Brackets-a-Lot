import discord
from discord.ui import View, Button

class MatchView(View):
    def __init__(self, tournament_name: str, round_index: int, match_index: int, player1: str, player2: str):
        super().__init__(timeout=None)
        self.tournament_name = tournament_name
        self.round_index = round_index
        self.match_index = match_index
        self.player1 = player1
        self.player2 = player2

        self.add_item(Button(
            label=self.player1,
            style=discord.ButtonStyle.success,
            custom_id=f"{self.tournament_name}|{self.round_index}|{self.match_index}|1"
        ))

        self.add_item(Button(
            label=self.player2,
            style=discord.ButtonStyle.success,
            custom_id=f"{self.tournament_name}|{self.round_index}|{self.match_index}|2"
        ))
