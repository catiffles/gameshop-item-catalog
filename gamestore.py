from flask import Flask, render_template, request, redirect, url_for
from flask import make_response, jsonify, flash
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import User, Console, Base, Game
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
Bootstrap(app)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "GameShop Application"

# Connect to database and create database session
engine = create_engine('sqlite:///gamestore.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}

    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't, create user locally
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session.get('credentials')
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "Access token received %s" % access_token

    # Exchange client token for long-lived server-side token with
    # GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-lived-token}
    app_id = json.loads(open(
        'fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.2/me"
    # Strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.2/me?%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # print "url sent for API access:%s" % url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Token must be stored in login_session in order to properly logout
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.2/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px; height: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border radius: 150px; "> '
    flash('Now logged in as %s' % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['user_id']
    del login_session['facebook_id']
    return "You have been logged out"


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showConsoles'))
    else:
        flash("You were not logged in to begin with!")
        return redirect(url_for('showConsoles'))


# API Endpoints (Get Request)
@app.route('/json/consoles/')
def consolesJSON():
    consoles = session.query(Console).all()
    return jsonify(Consoles=[console.serialize for console in consoles])


@app.route('/json/consoles/<int:console_id>/games/')
def gamesJSON(console_id):
    console = session.query(Console).filter_by(id=console_id).one()
    games = session.query(Game).filter_by(console_id=console.id).all()
    return jsonify(Games=[game.serialize for game in games])


@app.route('/json/consoles/<int:console_id>/games/<int:game_id>/')
def gameJSON(console_id, game_id):
    console = session.query(Console).filter_by(id=console_id).one()
    game = session.query(Game).filter_by(
        console_id=console.id,
        id=game_id).one()
    return jsonify(Game=[game.serialize])


@app.route('/')
@app.route('/consoles/')
def index():
    consoles = session.query(Console).all()
    return render_template('consoles.html', consoles=consoles)


# Create a new console
@app.route('/consoles/new/', methods=['GET', 'POST'])
def newConsole():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newConsole = Console(name=request.form['name'])
        session.add(newConsole)
        session.commit()
        flash("New Console Created!")
        return redirect(url_for('index'))
    else:
        return render_template('newConsole.html')


@app.route('/consoles/<int:console_id>/edit/', methods=['GET', 'POST'])
def editConsole(console_id):
    editedConsole = session.query(Console).filter_by(id=console_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name']:
            editedConsole.name = request.form['name']
        session.add(editedConsole)
        session.commit()
        flash("Console Name Edited")
        return redirect(url_for('index'))
    else:
        return render_template(
            'editConsole.html',
            console_id=console_id,
            console=editedConsole)

    return render_template('editConsole.html')


@app.route('/consoles/<int:console_id>/delete/', methods=['GET', 'POST'])
def deleteConsole(console_id):
    deletedConsole = session.query(Console).filter_by(id=console_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        session.delete(deletedConsole)
        session.commit()
        flash("Console has been deleted")
        return redirect(url_for('index'))
    else:
        return render_template('deleteConsole.html', console=deletedConsole)


@app.route('/consoles/<int:console_id>/')
@app.route('/consoles/<int:console_id>/games')
def gamesForConsole(console_id):
    console = session.query(Console).filter_by(id=console_id).one()
    games = session.query(Game).filter_by(console_id=console.id)
    if 'username' not in login_session:
        return render_template('games.html', console=console, games=games)


# Create a new game
@app.route('/consoles/<int:console_id>/games/new', methods=['GET', 'POST'])
def newGame(console_id):
    if 'username' not in login_session:
        return redirect('/login')
    console = session.query(Console).filter_by(id=console_id).one()
    if request.method == 'POST':
        newGame = Game(
            name=request.form['name'],
            price=request.form['price'],
            description=request.form['description'],
            console_id=console_id)
        session.add(newGame)
        session.commit()
        flash("New Game Created!")
        return redirect(url_for('gamesForConsole', console_id=console_id))
    else:
        return render_template('newGame.html', console_id=console_id)


# Edit a game
@app.route('/consoles/<int:console_id>/games/<int:game_id>/edit', methods=['GET', 'POST'])
def editGame(console_id, game_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedGame = session.query(Game).filter_by(id=game_id).one()
    console = session.query(Console).filter_by(id=console_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedGame.name = request.form['name']
        if request.form['price']:
            editedGame.price = request.form['price']
        if request.form['description']:
            editedGame.description = request.form['description']
        session.add(editedGame)
        session.commit()
        flash("Game Edited")
        return redirect(url_for('gamesForConsole', console_id=console_id))
    else:
        return render_template(
            'editGame.html',
            console_id=console_id,
            game_id=game_id,
            game=editedGame)


@app.route('/consoles/<int:console_id>/games/<int:game_id>/delete', methods=['GET', 'POST'])
def deleteGame(console_id, game_id):
    if 'username' not in login_session:
        return redirect('/login')
    console = session.query(Console).filter_by(id=console_id).one()
    gameToDelete = session.query(Game).filter_by(id=game_id).one()
    if request.method == 'POST':
        session.delete(gameToDelete)
        session.commit()
        flash("Game deleted")
        return redirect(url_for('gamesForConsole', console_id=console_id))
    else:
        return render_template('deleteGame.html', game=gameToDelete)


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(id=user_id).one()
    user.session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'cow'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
