import secrets
from flask import abort, request

COOKIE = 'wpc_game_access_v1'
USES = 4

def initialize(app):
    app.extensions['wpc_four_use_access'] = {}

def authorize(app, supplied, host_code, public=False):
    if public:
        return None
    grants = app.extensions['wpc_four_use_access']
    key = request.cookies.get(COOKIE, '')
    left = grants.get(key, 0)
    if left > 0:
        return key, left, False
    if not isinstance(supplied, str) or not secrets.compare_digest(supplied, host_code):
        abort(403, 'Enter the private host code to unlock four game or teaching-session creations.')
    return key, USES, True

def complete(app, authorization, response):
    if authorization is None:
        return response
    key, left, renew = authorization
    grants = app.extensions['wpc_four_use_access']
    if renew:
        grants.pop(key, None)
        key = secrets.token_urlsafe(32)
    left -= 1
    grants[key] = left
    response.set_cookie(COOKIE, key, secure=True, httponly=True, samesite='Lax', path='/')
    response.headers['X-WPC-Access-Remaining'] = str(left)
    return response
