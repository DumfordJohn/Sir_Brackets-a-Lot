import random

def assign_teams(players: list, teamsize: int) -> list:
    """Randomly shuffle players and assign them into teams.
    Returns a list of teams, each team is a dict with name, captain, and players.
    First player on each team is the captain."""
    shuffled = players[:]
    random.shuffle(shuffled)

    teams = []
    for i in range(0, len(shuffled), teamsize):
        members = shuffled[i:i + teamsize]
        team = {
            "name": f"Team {len(teams) + 1}",
            "captain_id": members[0]["id"],
            "captain_name": members[0]["name"],
            "players": members
        }
        teams.append(team)

    return teams


def is_captain(user_id: int, team_name: str, teams: list) -> bool:
    """Check if a user is the captain of a given team."""
    for team in teams:
        if team["name"] == team_name:
            return team["captain_id"] == user_id
    return False