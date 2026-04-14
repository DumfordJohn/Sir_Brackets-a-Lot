# Sir Brackets-a-Lot

A Discord bot for running single and double elimination tournaments — solo or team-based — with reaction signups and button-based match reporting.

---

## Setting Up Your Server

Once the bot is running, a server administrator needs to do a one-time setup before tournaments can be created.

**Step 1 — Run `/setup_bot`**
Pick the role you want to act as Tournament Admin and the channel where signup embeds will be posted. Anyone with the Tournament Admin role will be able to create and start tournaments.

**Step 2 — Create a tournament**
Run `/create_tournament` and fill in the name, type (single or double), mode (solo or team), and optionally a custom signup emoji. If you're running a team tournament, you'll also need to set a team size.

**Step 3 — Let players sign up**
The bot will post a signup embed in your configured channel. Players react with the signup emoji to join. Unreacting removes them from the list.

**Step 4 — Start the tournament**
Once everyone has signed up, run `/start_tournament`. The bot will create a thread off the signup message, post all the matchups, and ping each participant. If it's a team tournament, teams are randomly assigned first and captains are pinged for each match.

**Step 5 — Report match results**
Players (or team captains) click the winner button on their match embed. The bracket advances automatically after each round completes.

---

## Appendix — Command Reference

### Server Admin Only
These commands require the full **Administrator** permission in the server.

| Command | What it does |
|---|---|
| `/setup_bot role channel` | Sets the Tournament Admin role and the signup channel for the server. Must be run before tournaments can be created. |
| `/get_bot_setup` | Shows the currently configured Tournament Admin role and signup channel. |

---

### Tournament Admin
These commands can be used by anyone with the Tournament Admin role, or a server administrator.

| Command | What it does |
|---|---|
| `/create_tournament name type mode teamsize emoji` | Creates a new tournament and posts the signup embed. `type` is `single` or `double`. `mode` is `solo` or `team` (defaults to `solo`). `teamsize` is required if mode is `team`. `emoji` is optional and defaults to 🎮. |
| `/start_tournament name` | Starts the tournament, randomly assigns teams if applicable, and posts the bracket in a thread. For team tournaments, player count must be divisible by team size. |

---

### Players
These don't require any commands — players interact with the bot through reactions and buttons.

| Action | What it does |
|---|---|
| React with the signup emoji | Joins the tournament. |
| Remove the signup reaction | Leaves the tournament. |
| Click a winner button on a match embed | Reports the winner of that match. In team tournaments, only the captain of one of the two competing teams can do this. |

---

## Notes

- Tournaments are saved to `tournaments.json` so they persist across bot restarts.
- If the bot restarts mid-tournament, all active match buttons are automatically re-registered on startup.
- The `#sign-ups` channel name is used as a fallback if `/setup_bot` hasn't been run yet.
