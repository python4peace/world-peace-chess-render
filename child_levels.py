import os
import secrets
import chess.engine
from flask import abort, request
from access_pass import authorize, complete

LEVELS = {
    'first_steps': ('First Steps', 0, 75, .12),
    'beginner': ('Beginner', 0, 45, .20),
    'improving': ('Improving', 3, 20, .35),
    'intermediate': ('Intermediate', 7, 0, .60),
    'strong': ('Original Strong', 20, 0, None),
}
CHILD_COOKIE = 'wpc_child_play_v1'
_child_grants = {}

def authorize_game(app, supplied, host_code, public=False, mode=None, difficulty='strong'):
    # Child grants never enter the host/teacher grant dictionary.
    if mode == 'ai':
        child_code = os.environ.get('CHILD_PLAY_CODE', '')
        configured = 8 <= len(child_code) <= 64 and child_code != host_code
        key = request.cookies.get(CHILD_COOKIE, '')
        grant = _child_grants.get(key)
        # A changed child code invalidates previously issued child grants.
        valid_grant = (configured and grant and grant['left'] > 0
                       and secrets.compare_digest(grant['code'], child_code))
        child_supplied = (configured and isinstance(supplied, str)
                          and secrets.compare_digest(supplied, child_code))
        host_supplied = isinstance(supplied, str) and secrets.compare_digest(supplied, host_code)
        if not host_supplied and (valid_grant or child_supplied):
            if not isinstance(difficulty, str) or difficulty not in LEVELS or difficulty == 'strong':
                abort(403, 'The child play code allows the four easier computer levels only.')
            left = grant['left'] if valid_grant else 4
            return ('child', (key, left, not valid_grant, child_code))
    return ('host', authorize(app, supplied, host_code, public=public))

def complete_game(app, authorization, response):
    kind, details = authorization
    if kind == 'host':
        return complete(app, details, response)
    key, left, renew, code = details
    if renew:
        _child_grants.pop(key, None)
        key = secrets.token_urlsafe(32)
    left -= 1
    _child_grants[key] = {'left': left, 'code': code}
    response.set_cookie(CHILD_COOKIE, key, secure=True, httponly=True, samesite='Lax', path='/')
    response.headers['X-WPC-Access-Remaining'] = str(left)
    return response

def choose_move(engine, board, budget, difficulty):
    _, skill, random_percent, cap = LEVELS[difficulty]
    # Called while the application's engine_lock is held.
    # Reset on EVERY search so a previous easy game cannot weaken strong mode.
    engine.configure({'UCI_LimitStrength': False, 'Skill Level': skill})
    if random_percent and secrets.randbelow(100) < random_percent:
        return chess.engine.PlayResult(secrets.choice(list(board.legal_moves)), None)
    return engine.play(board, chess.engine.Limit(time=budget if cap is None else min(budget, cap)))
