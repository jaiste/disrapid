from flask import (
    Flask,
    render_template,
    send_from_directory,
    redirect,
    url_for,
    request,
    session,
    flash,
    abort,
)
# from flask_wtf import FlaskForm
# from wtforms import StringField, TextField, SubmitField
# from wtforms.validators import DataRequired, Length

import logging
import os
import sys
from functools import wraps
from requests_oauthlib import OAuth2Session
import re

from db.interface import DisrapidDb
from db.guild import Guild
from sqlalchemy import exists

# from db.guild import Guild, Role, Channel, Welcomemessage

import ptvsd

try:
    # check if we should run disrapid in debug mode
    if 'DEBUG' in os.environ:
        # listen for incoming debugger connection
        ptvsd.enable_attach(address=('0.0.0.0', 5051))
        # in debug mode we need to wait for debugger to connect
        ptvsd.wait_for_attach()
        logging.basicConfig(level=logging.DEBUG)
        debug = True
    else:
        # debug mode is not enabled, running in production mode...
        debug = False

except Exception:
    # any error will stop the container
    sys.exit(1)


ADMINISTRATOR = 0x00000008

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


def is_number(inputstring):
    return bool(re.match("^[0-9]*$", inputstring))


def token_updater(token):
    session['oauth2_token'] = token


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


def logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'oauth2_token' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('view_login'))
    return wrap


def guild_selected(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'guild_id' in session:
            return f(*args, **kwargs)
        else:
            flash('Select your server first!', 'info')
            return redirect(url_for('view_guilds'))
    return wrap


def value_exists_in(in_list, key, value):
    for item in in_list:
        if value == item[key]:
            return True
            break
    return False


@app.route('/assets/<path:path>')
def view_assets(path):
    # Assets are visible without login
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
    return redirect(LOGOUT_REDIRECT_URL)


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

        # get user data
        discord = make_session(token=session.get('oauth2_token'))

        session['guild_data'] = discord \
            .get(API_BASE_URL + '/users/@me/guilds') \
            .json()

        session['user_data'] = discord.get(API_BASE_URL + '/users/@me') \
            .json()

        return redirect(url_for('view_guilds'))
    except Exception as e:
        logging.error(e)


@app.route('/guilds', methods=['GET'])
@logged_in
def view_guilds():
    # this represents the guilds view
    # when a user has logged in we need to let him select the guild
    # we query all guilds where the user has administrator rights and
    # check whether disrapid has joined this guild
    # --
    #
    respond_servers = []

    s = db.Session()

    for guild in session['guild_data']:
        if guild['permissions'] & ADMINISTRATOR == ADMINISTRATOR:
            # user is admin on this server, check if disrapid has joined
            if s.query(exists().where(Guild.id == guild["id"])).scalar():
                respond_servers.append(
                    {
                        "id": guild["id"],
                        "icon": guild["icon"],
                        "name": guild["name"],
                    }
                )

    s.close()

    return render_template('guilds.html', servers=respond_servers)


@app.route('/select_guild', methods=['GET'])
@logged_in
def select_guild():
    # this represents the guild selector function
    # once a user has trasmitted a guild id we need to validate the data first
    # and save the guild identifier in the session variables
    # --
    #
    if "guild_id" in request.args:
        guild_id = request.args.get("guild_id")
    else:
        abort(400)

    # validate guild_id
    if not is_number(guild_id) or \
            value_exists_in(session["guild_data"], "id", guild_id) is False:
        abort(403)

    s = db.Session()

    # check if guild_id is in db
    if not s.query(exists().where(Guild.id == guild_id)).scalar():
        abort(403)

    session['guild_id'] = guild_id

    s.close()

    return render_template('dashboard.html')


@app.route('/')
@logged_in
@guild_selected
def view_dashboard():
    return render_template('dashboard.html')


if __name__ == "__main__":
    app.run(debug=debug)
