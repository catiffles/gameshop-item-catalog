#gameshop-item-catalog

###Summary
This application shows a list of game consoles and games associated with each console. A user must be logged in to add, edit and delete consoles and games.

###Files
- gamestore.py: main python file for flask application
- database_setup.py: python file for sqlalchemy database setup
- templates/consoles.html: template for index/all consoles
- templates/deleteConsole.html: template for deleting consoles
- templates/deleteGame.html: template for deleting games
- templates/editConsole.html: template for editing consoles
- templates/editGame.html: template for editing games
- templates/games.html: template for viewing all games
- templates/layout.html: template for general layout used on all pages
- templates/login.html: template for login page
- templates/newConsole.html: template for creating new consoles
- templates/newGame.html: template for creating new games

###Requirements
- python
- flask
- sqlalchemy
- bootstrap
- G+ or Facebook account to log in

###How to run
- Clone this repo
- Navigate to the repo in terminal
- Run python gamestore.py to start the server.
- Go to any browser and navigate to localhost:5000
