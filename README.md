# World Peace Chess — Render edition

A separate complete project. Use this ZIP instead of mixing files from older editions.
Prepared for Docker on Render Free. Not a hosted deployment and not tournament certified.
Python syntax and standalone clock tests are checked by the generator. The Docker build,
Flask routes, real engine searches, browser interaction and deployment require live testing.

## Features
- Friend invitations: host White, invited opponent Black.
- Full-strength server-side Stockfish: 1 thread, 32 MiB hash, 3-second search target.
- 3+2, 5+3 or 10+5 clocks with server-determined time forfeits and increment.
- Legal move highlighting, promotions, resignation, cancel unstarted game.
- Current-position draw claims, PGN download and read-only spectator view.
- Host-code protection for creating new games; invitees do not need the host code.
- Polling HTTP API: no Socket.IO setup, WebSocket configuration or Redis required.
- Render Dockerfile, Blueprint, health check, Gunicorn start command, basic clock tests.

## Step 1 — GitHub
Extract ZIP. Create a NEW EMPTY repository named world-peace-chess-render.
Upload the CONTENTS of the extracted folder: app.py, clocks.py, Dockerfile,
render.yaml, requirements.txt, start.sh, README.md and the templates/static/tests
folders must be at the repository ROOT, not inside an extra parent folder.
The easiest desktop method is GitHub Add file > Upload files and drag the extracted
contents, including folders. Commit the upload. A public repository is fine if you
keep all secrets out; Render also supports linked private repositories.
Do not upload the ZIP itself, an old app, venv, .env or a private host code.
Check the actual default branch. It is normally main, but do not assume master.

## Step 2 — Choose ONE Render deployment method
### Method A: manual Web Service (recommended for first setup)
1. In Render, New > Web Service; connect your new GitHub repository.
2. Name: world-peace-chess (if taken, choose another unique name).
3. Language/runtime: Docker — NOT Python 3 and NOT Static Site.
4. Region: Oregon or your preferred region near players.
5. Branch: your actual uploaded branch, usually main.
6. Root Directory: leave empty if Dockerfile is at the repo root.
7. Dockerfile Path: ./Dockerfile (default).
8. Instance Type/Compute Plan: Free. Verify the selection before deploying.
9. Advanced > Environment variables:
   HOST_CODE       = your own private random string at least 16 characters long
   STOCKFISH_PATH  = /usr/games/stockfish
   THINK_SECONDS   = 3
   ENGINE_HASH_MB  = 32
10. Health Check Path: /healthz
11. Docker Command: leave blank; Dockerfile CMD runs start.sh.
12. No separate Python build/start command is needed. Docker installs everything.
13. Turn Auto-Deploy off to avoid replacing active games with each GitHub push.
14. Click Deploy Web Service/Create Web Service (button wording may vary).

Generate a host code on your computer if desired:
    python3 -c "import secrets; print(secrets.token_urlsafe(24))"
Save it privately and enter it ONLY in Render Environment and the app's host field.
Do not paste it into GitHub, your stream, a screenshot, or a public chat.

### Method B: Blueprint (alternative, NOT an additional service)
Render New > Blueprint; connect this repository and uploaded branch.
Render reads render.yaml. It asks for HOST_CODE: enter your private random string.
Review that exactly ONE Free web service and NO database are being created.
Click Deploy/Apply. The Blueprint disables auto-deploys; use Manual Deploy later.
Use either Method A or B, not both, or you will create duplicate services.

## Step 3 — Open your real URL and invite a friend
After successful deployment, use the onrender.com address SHOWN BY RENDER.
It is not known until you create the service. There is no Cloudflare tunnel needed.
1. Open your hosted app, enter HOST_CODE, select Play a friend and a time control.
2. Click Create new game. Save/bookmark your room address on this browser.
3. Copy Private opponent invitation; send PRIVATELY to one person.
4. Friend opens invite and clicks Join as Black — start clocks. Be ready: White starts.
5. Public spectator link is for viewers; it cannot play moves.
Anyone holding the private invitation can control Black. It is a bearer credential,
not a one-time invitation or an account. Host seat is stored in localStorage under
the exact website origin. Use the same browser/origin to reconnect. Do not clear
storage or switch to a custom domain midgame. HTTP requests do not log token values
in URL paths. Tokens travel in headers or JSON; invitation tokens use URL fragments.

## Stockfish
Select Full-strength Stockfish, create game, then Start clock. No quiet fallback
exists. If engine fails, the game is stopped without scoring and logs show why.
The engine runs unhandicapped but CPU limits determine achieved strength.
Free CPU cannot be promised to provide desktop-level Stockfish performance.
Only ONE unfinished AI room is allowed. Cancel a waiting one or finish/resign an
active one before creating another. Search target is 3 seconds, not a browser
response deadline. ENGINE_HASH_MB 32 is chosen to save memory; keep Threads at 1.

## Clocks and rules
- No undo/pause. Both players' transport delay counts; no lag compensation.
- Browser clocks are estimates corrected by polling; only server decides flag fall.
- Checkmate, stalemate, automatic repetition/75-move and other terminal outcomes
  follow python-chess. Claim Draw supports CURRENT-position repetition/50-move
  claims only. Intended-next-move claims and draw offers are NOT implemented.
- Timeout draw uses has_insufficient_material(winner), not a full FIDE
  'any possible series of legal moves' solver. Casual play, not official arbitration.
- No accounts, ratings, anti-cheat, matchmaking, chat or TikTok voting.
- PGN saves moves and final result, not a per-move clock history.

## Render Free limits — read before live play
Official docs: https://render.com/docs/free
Free services sleep after 15 idle minutes and may restart at any time. Wake-up
can take about a minute. Active-page polling supplies traffic but is not an uptime
strategy or guarantee. Do not create bots to keep the service awake.
ALL rooms are in memory: sleep, restart, redeploy, or worker replacement deletes
them. No database is included. Rooms also expire after 24 hours; max 40 rooms.
A free Render Postgres database expires after 30 days, so it is NOT a permanent
free persistence solution. Paid hosting alone does not persist this app's rooms.
This app must stay at ONE Gunicorn worker and ONE instance. Do not use --preload,
multiple workers, autoscaling or a reloader; state and engine live in one process.
For a professional service, redesign shared state/persistent clocks using a
reliable database, add accounts/abuse controls, monitoring and backup/recovery.
Render workspace free hours, bandwidth and build minutes have limits. Review
billing, especially if you attach a payment method. Deployment creates a Free
service only; it does not guarantee unlimited free usage or permanent uptime.

## TikTok LIVE
Open Clean spectator view. Capture that browser window in OBS (or the capture
method your streaming software provides). Show board and both clocks; hide your
private invitation and host code. The spectator page contains no playing token.
For direct OBS RTMP streaming your TikTok account must have its own server URL
and stream key. Add them privately in OBS Settings > Stream > Custom. The game
cannot unlock LIVE access or generate streaming credentials. No automatic stream
start or viewer moves are included. Start the broadcast manually after previewing.
For Ubuntu OBS installation: sudo apt install obs-studio

## Local testing (optional)
Install Docker, then from the project folder:
    docker build -t world-peace-chess .
    docker run --rm -p 10000:10000 -e HOST_CODE='YOUR-OWN-PRIVATE-LONG-CODE' world-peace-chess
Open http://localhost:10000. Do not copy a real code into a public terminal recording.
Clock tests without third-party Python packages:
    python3 -m unittest discover -s tests -v

## Acceptance checklist BEFORE sharing widely or streaming
1. Open /healthz: status ok. Verify engine_ready true for AI play.
2. Create a friend room. Use a different browser profile/private window for Black.
3. Join; verify White clock starts, then moves switch clocks with increments.
4. Attempt wrong-turn moves; verify they are rejected.
5. Leave White idle until flag: result must appear and further moves must fail.
6. Resign another game; save PGN and verify the result.
7. Refresh White room in same browser; verify seat resumes while clocks continue.
8. Open spectator URL; verify it cannot move or reveal a private invite.
9. Separately test one Stockfish game; verify Black responds and clocks switch.
10. Restart/redeploy in a TEST session; verify missing-room message and create anew.

## Troubleshooting
HOST_CODE error: set at least 16 characters in Render Environment and redeploy.
Dockerfile not found: upload contents to repo root, or fix Root Directory setting.
No open ports: select Docker and leave Docker Command blank. start.sh binds
0.0.0.0:${PORT:-10000}; don't replace it with localhost.
Library failed to load: browser requires chess.js CDN; allow it and refresh.
Stockfish unavailable: check Render logs. Dockerfile installs /usr/games/stockfish.
Killed/out of memory: keep hash 32 and one AI game; free capacity may be insufficient.
Room disappeared: expected after restart/sleep/deploy. Use a new room.
Wrong code: enter exact private HOST_CODE; friend does not need it.
Deploy stuck/fails: send the error lines with codes/invites/keys removed.

## Included third-party software
Flask, Gunicorn, python-chess, Stockfish, and chess.js have their own licenses.
chess.js is loaded from cdnjs version 0.10.3. Stockfish is installed from Debian;
Debian package licensing is in /usr/share/doc/stockfish/copyright inside the image.
Stockfish source: https://github.com/official-stockfish/Stockfish
python-chess source: https://github.com/niklasf/python-chess
chess.js source: https://github.com/jhlywa/chess.js
Keep applicable licenses/source obligations in mind if redistributing binaries.
