import atexit
import os
import secrets
import threading
import time
from collections import deque
from urllib.parse import urlsplit

import chess
import chess.engine
import chess.pgn
from flask import Flask, abort, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from clocks import GameClock

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8192
HOST_CODE = os.environ.get('HOST_CODE', '')
if len(HOST_CODE) < 16:
    raise RuntimeError('Set HOST_CODE in Render Environment to a private value of at least 16 characters.')
CONTROLS = {'3+2': (180,2), '5+3': (300,3), '10+5': (600,5)}
rooms = {}
lock = threading.RLock()
engine_lock = threading.Lock()
creation_attempts = deque(maxlen=200)
engine = None
engine_ok = False
BOOT_ID = secrets.token_hex(8)
THINK_SECONDS = max(.1, min(15., float(os.environ.get('THINK_SECONDS','3'))))
ENGINE_HASH = max(16, min(128, int(os.environ.get('ENGINE_HASH_MB','32'))))

def boot_engine():
    global engine, engine_ok
    try:
        engine = chess.engine.SimpleEngine.popen_uci(os.environ.get('STOCKFISH_PATH','/usr/games/stockfish'))
        engine.configure({'UCI_LimitStrength': False, 'Skill Level': 20, 'Threads': 1, 'Hash': ENGINE_HASH})
        engine_ok = True
        app.logger.warning('Stockfish ready: unrestricted strength, one thread, %s MiB hash, %.1fs search target',ENGINE_HASH,THINK_SECONDS)
    except Exception:
        engine_ok = False
        app.logger.exception('Stockfish unavailable. Friend games remain available.')

def close_engine():
    if engine:
        try: engine.quit()
        except Exception: pass
atexit.register(close_engine)

@app.before_request
def guard():
    if request.method == 'POST':
        origin = request.headers.get('Origin')
        if origin and urlsplit(origin).netloc != request.host:
            abort(403, 'Cross-origin requests are not allowed.')
        if not request.is_json:
            abort(415, 'JSON required.')

@app.after_request
def headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.errorhandler(HTTPException)
def http_error(exc):
    if request.path.startswith('/api/'):
        return jsonify(error=exc.description), exc.code
    return exc

def data():
    d = request.get_json(silent=True)
    if not isinstance(d,dict): abort(400,'A JSON object is required.')
    return d

def player(g, token):
    if not isinstance(token,str) or not token: return 'spectator'
    if secrets.compare_digest(token,g['white_token']): return 'w'
    if g['black_token'] and secrets.compare_digest(token,g['black_token']): return 'b'
    return 'spectator'

def get_room(rid):
    g=rooms.get(rid)
    if g is None: abort(404,'Room is gone. The service may have restarted. Create a new game.')
    return g

def finish(g,result,message):
    g['phase']='ended';g['result']=result;g['message']=message;g['clock'].stop()

def flag_check(g):
    if g['phase']!='playing': return
    flagged=g['clock'].charge()
    if flagged:
        winner=chess.BLACK if flagged=='w' else chess.WHITE
        if g['board'].has_insufficient_material(winner):
            finish(g,'1/2-1/2','Time expired — draw under the material-based timeout rule.')
        else:
            finish(g,'0-1' if flagged=='w' else '1-0',('White' if flagged=='w' else 'Black')+' lost on time.')

def board_end(g):
    outcome=g['board'].outcome(claim_draw=False)
    if outcome:
        finish(g,outcome.result(),outcome.termination.name.replace('_',' ').title())
        return True
    return False

def payload(g, token=''):
    flag_check(g)
    return dict(fen=g['board'].fen(),white=g['clock'].remaining['w'],black=g['clock'].remaining['b'],
                phase=g['phase'],turn='w' if g['board'].turn else 'b',role=player(g,token),
                result=g['result'],message=g['message'],control=g['control'],mode=g['mode'],
                moves=g['moves'][:],engine_ready=engine_ok,revision=g['revision'],boot_id=BOOT_ID,
                think_seconds=THINK_SECONDS,is_host=player(g,token)==g.get('host_side','w'))

def commit_move(g,move):
    flag_check(g)
    if g['phase']!='playing':return False
    # Final clock check before crediting the increment or changing the board.
    if not g['clock'].complete_turn():
        flag_check(g);return False
    g['moves'].append(g['board'].san(move))
    g['board'].push(move);g['revision']+=1
    if not board_end(g):
        g['message']='White to move' if g['board'].turn else ('Stockfish thinking — Black clock running' if g['mode']=='ai' else 'Black to move')
    return True

@app.get('/')
@app.get('/room/<rid>')
def index(rid=None):return render_template('index.html')

@app.get('/healthz')
def health():return jsonify(status='ok',engine_ready=engine_ok)

@app.get('/api/status')
def status():return jsonify(engine_ready=engine_ok,think_seconds=THINK_SECONDS,public_friend_games=os.environ.get('ALLOW_PUBLIC_FRIEND_GAMES','false').lower()=='true')

@app.post('/api/new')
def new():
    d=data()
    with lock:
        now=time.monotonic()
        while creation_attempts and now-creation_attempts[0]>60:creation_attempts.popleft()
        if len(creation_attempts)>=30:abort(429,'Too many creation attempts. Wait one minute.')
        creation_attempts.append(now)
        public_friend = (
            os.environ.get('ALLOW_PUBLIC_FRIEND_GAMES', 'false').lower() == 'true'
            and d.get('mode') == 'friend'
        )
        supplied=d.get('host_code','')
        if not public_friend and (not isinstance(supplied,str) or not secrets.compare_digest(supplied,HOST_CODE)):
            abort(403,'Incorrect host code. Use the private HOST_CODE saved in Render Environment.')
        mode=d.get('mode');control=d.get('control')
        if mode not in ('friend','ai','selfplay') or control not in CONTROLS:abort(400,'Choose a valid mode and time control.')
        if len(rooms)>=40:abort(429,'Room limit reached. Use existing rooms or restart the service after games finish.')
        if mode in ('ai','selfplay'):
            if not engine_ok:abort(503,'Stockfish unavailable. Check Render logs or try a friend game.')
            for old in rooms.values():
                flag_check(old)
                if old['mode'] in ('ai','selfplay') and old['phase'] in ('waiting','playing'):
                    abort(409,'Only one active Stockfish or self-play game is allowed on this small service. Finish or cancel the earlier game.')
        color=d.get('color','random') if mode=='friend' else 'white'
        if color not in ('white','black','random'):abort(400,'Choose White, Black, or Random.')
        host_side=secrets.choice(('w','b')) if color=='random' else ('w' if color=='white' else 'b')
        rid=secrets.token_urlsafe(18);seconds,increment=CONTROLS[control]
        g=dict(board=chess.Board(),clock=GameClock(seconds,increment),mode=mode,control=control,
               phase='waiting',result='*',message='Waiting for invited player to join' if mode=='friend' else 'Click Start when ready',
               white_token=secrets.token_urlsafe(32),black_token=secrets.token_urlsafe(32) if mode=='friend' else '',
               moves=[],created=now,revision=0,ai_pending=False)
        g['host_side']=host_side
        g['guest_side']='b' if host_side=='w' else 'w'
        rooms[rid]=g
        host_token=g['white_token'] if host_side=='w' else g['black_token']
        guest_token=(g['black_token'] if host_side=='w' else g['white_token']) if mode=='friend' else ''
        return jsonify(room=rid,token=host_token,invite=guest_token)

@app.get('/api/room/<rid>')
def room_state(rid):
    with lock:return jsonify(payload(get_room(rid),request.headers.get('X-Player-Token','')))

@app.post('/api/room/<rid>/join')
def join(rid):
    d=data();token=d.get('token','')
    with lock:
        g=get_room(rid)
        if g['mode']!='friend' or player(g,token)!=g.get('guest_side','b'):abort(403,'Invalid opponent invitation.')
        if g['phase']=='waiting':
            g['phase']='playing';g['clock'].start();g['message']='White to move';g['revision']+=1
        return jsonify(payload(g,token))

@app.post('/api/room/<rid>/action')
def action(rid):
    d=data();token=request.headers.get('X-Player-Token','')
    with lock:
        g=get_room(rid);who=player(g,token);flag_check(g)
        if who not in ('w','b'):abort(403,'Spectators cannot play.')
        act=d.get('action')
        if g['mode']=='selfplay' and (who!='w' or act not in ('start','stop_selfplay','cancel')):
            abort(403,'Only the host can start or stop automatic self-play; manual moves are disabled.')
        if act=='start' and g['mode'] in ('ai','selfplay') and who=='w' and g['phase']=='waiting':
            g['phase']='playing';g['clock'].start();g['message']='White to move';g['revision']+=1
        elif act=='stop_selfplay' and g['mode']=='selfplay' and who=='w' and g['phase']=='playing':
            finish(g,'*','Automatic game stopped by host; not scored.')
        elif act=='resign' and g['phase']=='playing':
            finish(g,'0-1' if who=='w' else '1-0',('White' if who=='w' else 'Black')+' resigned.')
        elif act=='cancel' and who==g.get('host_side','w') and g['phase']=='waiting':
            finish(g,'*','Unstarted game canceled.')
        elif act=='claim_draw' and g['phase']=='playing' and who==('w' if g['board'].turn else 'b'):
            # Immediate claims only; intended-next-move claims require arbiter handling.
            if g['board'].is_repetition(3) or g['board'].is_fifty_moves():
                finish(g,'1/2-1/2','Draw claimed in the current position.')
            else:abort(400,'No current-position draw claim. Intended-next-move claims are not implemented.')
        elif act=='move':
            if g['phase']!='playing' or who!=('w' if g['board'].turn else 'b'):abort(409,'Not your turn or game ended.')
            if d.get('revision')!=g['revision']:abort(409,'Position changed. Wait for the board to refresh.')
            try:
                move=chess.Move.from_uci(str(d.get('move','')))
                if move not in g['board'].legal_moves:raise ValueError()
            except ValueError:abort(400,'Illegal move.')
            commit_move(g,move)
            if g['phase']=='playing' and g['mode']=='ai' and g['board'].turn==chess.BLACK and not g['ai_pending']:
                g['ai_pending']=True
                threading.Thread(target=computer_move,args=(rid,g),daemon=True).start()
        else:abort(409,'Action unavailable for this game.')
        return jsonify(payload(g,token))

def computer_move(rid,g):
    global engine_ok
    try:
        with engine_lock:
            with lock:
                if rooms.get(rid) is not g:return
                flag_check(g)
                if g['phase']!='playing':return
                board=g['board'].copy(stack=True)
                expected_revision=g['revision']
                side='w' if board.turn else 'b'
                budget=min(THINK_SECONDS,max(.01,g['clock'].remaining[side]-.15))
            result=engine.play(board,chess.engine.Limit(time=budget))
        with lock:
            if rooms.get(rid) is not g:return
            flag_check(g)
            if g['phase']!='playing':return
            if g['revision']!=expected_revision:return
            if result.move is None or result.move not in g['board'].legal_moves:
                raise RuntimeError('Engine returned no legal move')
            commit_move(g,result.move)
    except Exception:
        engine_ok=False
        app.logger.exception('Stockfish error')
        with lock:
            if rooms.get(rid) is g and g['phase']=='playing':finish(g,'*','Engine error — game stopped, not scored. Check Render logs.')
    finally:
        with lock:g['ai_pending']=False

@app.get('/api/room/<rid>/pgn')
def pgn(rid):
    with lock:
        g=get_room(rid);flag_check(g)
        game=chess.pgn.Game.from_board(g['board'])
        game.headers.update(Event='World Peace Chess — casual timed play',White='Stockfish' if g['mode']=='selfplay' else ('Host' if g.get('host_side','w')=='w' else 'Invited player'),
                            Black='Stockfish' if g['mode'] in ('ai','selfplay') else ('Invited player' if g.get('host_side','w')=='w' else 'Host'),Result=g['result'])
        seconds,inc=CONTROLS[g['control']];game.headers['TimeControl']=f'{seconds}+{inc}'
        response=app.response_class(str(game)+'\n',mimetype='application/x-chess-pgn')
        response.headers['Content-Disposition']='attachment; filename="world-peace-chess.pgn"'
        return response

def ticker():
    while True:
        time.sleep(.1)
        with lock:
            now=time.monotonic()
            for rid,g in list(rooms.items()):
                flag_check(g)
                if now-g['created']>86400:
                    rooms.pop(rid,None)
                    continue
                if g['mode']=='selfplay' and g['phase']=='playing' and not g['ai_pending']:
                    g['ai_pending']=True
                    threading.Thread(target=computer_move,args=(rid,g),daemon=True).start()

boot_engine()
threading.Thread(target=ticker,daemon=True).start()

# WPC_SELFPLAY_SOUND_V2

# WPC_COLORS_TEACHING_ZIP_V1
from teaching import register_lessons
register_lessons(app, lock, HOST_CODE, creation_attempts)
