import secrets, time
import chess
from flask import request, jsonify, abort, render_template

def register_lessons(app, lock, host_code, attempts):
    lessons={}
    def body():
        d=request.get_json(silent=True)
        if not isinstance(d,dict):abort(400,'JSON object required.')
        return d
    def role(g,t):
        if not isinstance(t,str) or not t:return 'spectator'
        if secrets.compare_digest(t,g['teacher']):return 'teacher'
        if secrets.compare_digest(t,g['student']):return 'student'
        return 'spectator'
    def room(rid):
        g=lessons.get(rid)
        if g is None or time.monotonic()-g['created']>86400:
            lessons.pop(rid,None);abort(404,'Lesson expired or service restarted. Create a new lesson.')
        return g
    def state(g,t):
        who=role(g,t);outcome=g['board'].outcome(claim_draw=False)
        d=dict(fen=g['board'].fen(),role=who,revision=g['revision'],note=g['note'],moves=g['moves'][:],move_serial=g['serial'],message=outcome.termination.name.replace('_',' ').title() if outcome else ('White to move' if g['board'].turn else 'Black to move'))
        if who=='teacher':d['student_invite']=g['student']
        return d
    @app.get('/lesson')
    @app.get('/lesson/<rid>')
    def lesson_page(rid=None):return render_template('lesson.html')
    @app.post('/api/lesson/new')
    def lesson_new():
        d=body()
        with lock:
            now=time.monotonic()
            while attempts and now-attempts[0]>60:attempts.popleft()
            if len(attempts)>=30:abort(429,'Wait one minute before creating another room.')
            attempts.append(now)
            supplied=d.get('host_code','')
            if not isinstance(supplied,str) or not secrets.compare_digest(supplied,host_code):abort(403,'Incorrect host code.')
            for k,g in list(lessons.items()):
                if now-g['created']>86400:lessons.pop(k,None)
            if len(lessons)>=20:abort(429,'Close an old lesson first.')
            rid=secrets.token_urlsafe(18)
            g=dict(board=chess.Board(),teacher=secrets.token_urlsafe(32),student=secrets.token_urlsafe(32),created=now,revision=0,note='Welcome! Select a piece to see legal moves. Teacher and student can practice either side.',moves=[],serial=0)
            lessons[rid]=g
            return jsonify(room=rid,token=g['teacher'])
    @app.get('/api/lesson/<rid>')
    def lesson_state(rid):
        with lock:return jsonify(state(room(rid),request.headers.get('X-Player-Token','')))
    @app.post('/api/lesson/<rid>/action')
    def lesson_action(rid):
        d=body()
        with lock:
            g=room(rid);token=request.headers.get('X-Player-Token','');who=role(g,token)
            if who=='spectator':abort(403,'Spectators can only watch.')
            if d.get('revision')!=g['revision']:abort(409,'Position changed. Wait for refresh and retry.')
            act=d.get('action')
            if act=='move':
                if g['board'].is_game_over(claim_draw=False):abort(409,'Position ended. Ask teacher to undo or reset.')
                try:
                    move=chess.Move.from_uci(str(d.get('move','')))
                    if move not in g['board'].legal_moves:raise ValueError()
                except ValueError:abort(400,'Illegal move.')
                g['moves'].append(g['board'].san(move));g['board'].push(move);g['serial']+=1
            elif who!='teacher':abort(403,'Teacher-only control.')
            elif act=='note':
                note=d.get('note','')
                if not isinstance(note,str) or len(note)>2000:abort(400,'Use at most 2000 characters.')
                g['note']=note
            elif act=='undo':
                if not g['board'].move_stack:abort(409,'No move to undo.')
                g['board'].pop();g['moves'].pop()
            elif act=='reset':g['board']=chess.Board();g['moves']=[]
            elif act=='close':lessons.pop(rid);return jsonify(closed=True)
            else:abort(400,'Unknown action.')
            g['revision']+=1
            return jsonify(state(g,token))
