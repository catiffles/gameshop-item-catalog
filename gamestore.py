from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Console, Base, Game

app = Flask(__name__)
Bootstrap(app)

engine = create_engine('sqlite:///gamestore.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#API Endpoints (Get Request)
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
  game = session.query(Game).filter_by(console_id=console.id, id=game_id).one()
  return jsonify(Game=[game.serialize])

@app.route('/')
@app.route('/consoles/')
def index():
  consoles = session.query(Console).all()
  return render_template('consoles.html', consoles=consoles)

@app.route('/consoles/new/', methods=['GET', 'POST'])
def newConsole():
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
  if request.method == 'POST':
    if request.form['name']:
      editedConsole.name = request.form['name']
    session.add(editedConsole)
    session.commit()
    flash("Console Name Edited")
    return redirect(url_for('index'))
  else:
    return render_template('editConsole.html', console_id=console_id, console=editedConsole)

  return render_template('editConsole.html')

@app.route('/consoles/<int:console_id>/delete/', methods=['GET', 'POST'])
def deleteConsole(console_id):
  deletedConsole = session.query(Console).filter_by(id=console_id).one()
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
  return render_template('games.html', console=console, games=games)

@app.route('/consoles/<int:console_id>/games/new', methods=['GET', 'POST'])
def newGame(console_id):
  if request.method == 'POST':
    newGame = Game(name=request.form['name'], price=request.form['price'], description=request.form['description'], console_id=console_id)
    session.add(newGame)
    session.commit()
    flash("New Game Created!")
    return redirect(url_for('gamesForConsole', console_id=console_id))
  else:
    return render_template('newGame.html', console_id=console_id)

@app.route('/consoles/<int:console_id>/games/<int:game_id>/edit', methods=['GET', 'POST'])
def editGame(console_id, game_id):
  editedGame = session.query(Game).filter_by(id=game_id).one()
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
    return render_template('editGame.html', console_id=console_id, game_id=game_id, game=editedGame)

@app.route('/consoles/<int:console_id>/games/<int:game_id>/delete', methods=['GET', 'POST'])
def deleteGame(console_id, game_id):
  gameToDelete = session.query(Game).filter_by(id=game_id).one()
  if request.method == 'POST':
    session.delete(gameToDelete)
    session.commit()
    flash("Game deleted")
    return redirect(url_for('gamesForConsole', console_id=console_id))
  else:
    return render_template('deleteGame.html', game=gameToDelete)

if __name__ == '__main__':
  app.secret_key = 'cow'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
