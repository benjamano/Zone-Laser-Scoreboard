from flask_sqlalchemy import SQLAlchemy

from func.format import message

class context:
    def __init__(self):
        self.db = SQLAlchemy()
    
    def createDatabase(self, app):
        self.Gun = None
        self.Player = None
        self.Game = None
        self.Team = None
        self.GamePlayers = None

        self.db.init_app(app)
        self.db.create_all()
        self.__createModels()
        self.__seedDBData() 
        
    def __createModels(self):
        global Gun, Player, Game, Team, GamePlayers
        
        class Gun(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            defaultColor = self.db.Column(self.db.String(60), unique=False, nullable=False)
            
        class Player(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            kills = self.db.Column(self.db.Integer, nullable=False)
            deaths = self.db.Column(self.db.Integer, nullable=False)
            gamesWon = self.db.Column(self.db.Integer, nullable=False)
            gamesLost = self.db.Column(self.db.Integer, nullable=False)
            
        class Game(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            startTime = self.db.Column(self.db.DateTime, nullable=False)
            endTime = self.db.Column(self.db.DateTime, nullable=False)
            winningPlayer = self.db.Column(self.db.Integer, self.db.ForeignKey("player.id"), nullable=True)
            winningTeam = self.db.Column(self.db.Integer, self.db.ForeignKey("team.id"), nullable=True)
            loser = self.db.Column(self.db.String(60), nullable=True)
            
        class Team(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(60), unique=True, nullable=False)
            teamColour = self.db.Column(self.db.String(10), nullable=False)
            gamePlayers = self.db.relationship("GamePlayers", backref="team_ref", lazy=True)

        class GamePlayers(self.db.Model):
            id = self.db.Column(self.db.Integer, primary_key=True)
            gameID = self.db.Column(self.db.Integer, self.db.ForeignKey("game.id"), nullable=False)
            gunID = self.db.Column(self.db.Integer, self.db.ForeignKey("gun.id"), nullable=False)
            playerID = self.db.Column(self.db.Integer, self.db.ForeignKey("player.id"), nullable=False)
            playerWon = self.db.Column(self.db.Boolean, nullable=False)
            team = self.db.Column(self.db.Integer, self.db.ForeignKey("team.id"), nullable=True)
            
        self.Gun = Gun
        self.Player = Player
        self.Game = Game
        self.Team = Team
        self.GamePlayers = GamePlayers

        
    def __seedDBData(self):
        if not Gun.query.first() and not Player.query.first():
            message("Empty DB Found! Seeding Data....", type="warning")
 
            guns = [
                Gun(name="Alpha", defaultColor="Red"),
                Gun(name="Apollo", defaultColor="Red"),
                Gun(name="Chaos", defaultColor="Red"),
                Gun(name="Cipher", defaultColor="Red"),
                Gun(name="Cobra", defaultColor="Red"),
                Gun(name="Comet", defaultColor="Red"),
                Gun(name="Commander", defaultColor="Red"),
                Gun(name="Cyborg", defaultColor="Red"),
                Gun(name="Cyclone", defaultColor="Red"),
                Gun(name="Delta", defaultColor="Red"),
                Gun(name="Dodger", defaultColor="Green"),
                Gun(name="Dragon", defaultColor="Green"),
                Gun(name="Eagle", defaultColor="Green"),
                Gun(name="Eliminator", defaultColor="Green"),
                Gun(name="Elite", defaultColor="Green"),
                Gun(name="Falcon", defaultColor="Green"),
                Gun(name="Ghost", defaultColor="Green"),
                Gun(name="Gladiator", defaultColor="Green"),
                Gun(name="Hawk", defaultColor="Green"),
                Gun(name="Hyper", defaultColor="Green"),
                Gun(name="Inferno", defaultColor="Green")
            ]
            
            self.InsertMany(guns)
            self.SaveChanges()
            message("Data seeded successfully", type="success")
        else:
            message("Data already exists, skipping seeding.", type="info")
    
    def Insert(self, object):
        self.db.session.add(object)
        
    def InsertMany(self, objects):
        self.db.session.bulk_save_objects(objects)
        
    def SaveChanges(self):
        self.db.session.commit()
        
    
    