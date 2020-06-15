from flask import (
    Flask,
    render_template,
    send_from_directory,
    redirect,
    request,
    session,
    flash,
    jsonify,
)

import logging
import os
import sys
import re
from functools import wraps
from requests_oauthlib import OAuth2Session

from db.interface import DisrapidDb
from db.guild import Guild, Role, Channel, Welcomemessage

import ptvsd

try:
    # check if we should run disrapid in debug mode
    if 'DEBUG' in os.environ:
        # listen for incoming debugger connection
        ptvsd.enable_attach(address=('0.0.0.0', 5051))
        # in debug mode we need to wait for debugger to connect
        ptvsd.wait_for_attach()
        logging.basicConfig(level=logging.DEBUG)
    else:
        # debug mode is not enabled, running in production mode...
        pass

except Exception:
    # any error will stop the container
    sys.exit(1)


app = Flask(__name__)

try:
    app.secret_key = os.environ["SECRET_KEY"]

    OAUTH2_CLIENT_ID = os.environ["DISCORD_OAUTH2_CLIENT_ID"]
    OAUTH2_CLIENT_SECRET = os.environ["DISCORD_OAUTH2_CLIENT_SECRET"]
    OAUTH2_REDIRECT_URI = os.environ["DISCORD_OAUTH2_REDIRECT_URI"]

    if 'http://' in OAUTH2_REDIRECT_URI:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'
    API_BASE_URL = 'https://discordapp.com/api'
    AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
    TOKEN_URL = API_BASE_URL + '/oauth2/token'

    LOGOUT_REDIRECT_URL = os.environ["LOGOUT_REDIRECT_URL"]

    db = DisrapidDb(host=os.environ["DB_HOST"],
                    user=os.environ["DB_USER"],
                    passwd=os.environ["DB_PASS"],
                    name=os.environ["DB_NAME"])

except Exception as e:
    logging.fatal(e)
    sys.exit(1)


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater
        )


def is_logged_in(f):
    # this represents the decorator to check whether a user has a valid
    # discord oauth token
    # ---
    #
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'oauth2_token' in session:
            # ADD IMPLEMENTATION:
            # check if token is still valid!!
            #
            # TMP
            return f(*args, **kwargs)
        else:
            # flash('Unauthorized, please login', 'danger')
            return redirect(url_for('view_login'))
    return wrap


def is_server_selected(f):
    # This is the decorator to check whether the user has selected a server
    # ---
    #
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'server_id' in session:
            return f(*args, **kwargs)
        else:
            flash('Select your server first!', 'info')
            return redirect(url_for('view_select_server'))
    return wrap


@app.route('/assets/<path:path>')
def view_assets(path):
    # Assets are visible without login
    # ---
    #
    return send_from_directory('assets', path)


@app.route('/login')
def view_login():
    # This represents the login function
    # ---
    #
    # Login function will create an oauth session and redirect to discord
    # authorization url
    # Discord client should send the user back to our callback url
    #
    try:
        scope = request.args.get(
            'scope',
            'identify email connections guilds guilds.join')
        discord = make_session(scope=scope.split(' '))
        authorization_url, state = \
            discord.authorization_url(AUTHORIZATION_BASE_URL)
        session['oauth2_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        logging.error(e)


@app.route('/logout')
def logout(): 
    # Log the user out and redirect to login-page
    # ---
    #
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('view_login'))


@app.route('/callback')
def callback():
    # This represents the callback function
    # ---
    #
    # when user is logged in via discord oauth we receive the callback function
    # once the user is logged in the token is valid and we can login the user
    #
    try:
        if request.values.get('error'):
            return request.values['error']
        discord = make_session(state=session.get('oauth2_state'))
        token = discord.fetch_token(
            TOKEN_URL,
            client_secret=OAUTH2_CLIENT_SECRET,
            authorization_response=request.url.replace('http', 'https'))
        session['oauth2_token'] = token
        session['logged_in'] = True
        logging.debug(f'user logged in with token: {token}')

        # get user data
        discord = make_session(token=session.get('oauth2_token'))

        session['guild_data'] = discord \
            .get(API_BASE_URL + '/users/@me/guilds') \
            .json()

        session['user_data'] = discord.get(API_BASE_URL + '/users/@me') \
            .json()

        logging.debug(session['user_data'])
        return redirect(url_for('view_select_server'))
    except Exception as e:
        logging.error(e)

# @app.route('/select_server')
# @is_logged_in
# def view_select_server():
#     # This represents the server selector function
#     # ---
#     # 
#     # Once the user is logged in we need him to select a server first
#     # We collect all servers the user has access to and show them all servers he is admin compared with our xbot database
#     # If the user has not invited xbot to this server, we will present him a link to do so
#     #
#     # Parameters
#     # ---
#     # server_id: :class: `string`
#     #   user has selected server with this id
#     # 
# 
#     # get parameters
#     server_id = request.args.get("server_id")
#     ip_addr = request.remote_addr
# 
#     if not server_id:
#         # user has not selected a server, show a list of all servers the user can select
# 
#         respond_servers = []
# 
#         for guild in session['guild_data']:
#             # check if user is admin on this server
#             logging.debug(f"guild: {guild}")
#             
#             # permission calculation
#             if guild['permissions'] & ADMINISTRATOR == ADMINISTRATOR:
#                 # user is admin on this server, check if xbot has joined this server
#                 newserver = xdb.get_server(guild['id'])
#                 if newserver != None:
#                     # xbot has joined this server before
#                     logging.debug(f"server: {newserver}")
#                     newserver["guild_avatar"] = guild["icon"]
#                     respond_servers.append(newserver)
#                 else:
#                     # xbot hasn't joined this server
#                     #
#                     # ADD IMPLEMENTATION
#                     # --
#                     # show this server as "new server", invite xbot to this server
#                     pass
#         
#         return render_template('select_server.html', servers=respond_servers)
#     else:
#         # user has selected server,
#         # check if user has access to server_id
#         if not only_number(server_id):
#             logging.warning(f'[RISK] from ip_addr-{ip_addr} user-{session["user_data"]["id"]} ({session["user_data"]["username"]}) has tried to modify server_id input!')
#             flash('Server_id violation!', 'danger')
#             return redirect(url_for('view_select_server'))
# 
#         for guild in session['guild_data']:
#             if server_id == guild['id']:
#                 session['server_id'] = server_id
#                 session['server_name'] = guild['name']
#                 break
#         
#         if 'server_id' not in session:
#             # user has no acces to this server!
#             # this shouldn`t happen in normal environment, alert admin with a risk log
#             logging.warning(f'[RISK] from ip_addr-{ip_addr} user-{session["user_data"]["id"]} ({session["user_data"]["username"]}) has tried to select server-{server_id} where he has no permissions!')
#             flash('You are not allowed to access this server!', 'danger')
#             return redirect(url_for('view_select_server'))
# 
#         return redirect(url_for('view_dashboard'))

# @app.route('/')
# @is_logged_in
# @is_server_selected
# def view_dashboard():
#     # get dashboard
#     server_info = xdb.get_server(session["server_id"])
#     # read server meta
#     meta_info = xdb.get_server_meta(session["server_id"])
#     return render_template('dashboard.html', meta=meta_info, server=server_info)


@app.route('/')
def view_dashboard():
    return render_template('dashboard.html')


if __name__ == "__main__":
    app.run()
