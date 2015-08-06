# configuration
import os
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

DATABASE_URL = (os.environ['DATABASE_URL'] if 'DATABASE_URL' in os.environ else 'postgresql:///gameshop')
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# class


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))
    access_token = Column(String(200))

    def __init__(self, access_token):
        self.access_token = access_token

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture
        }


class Console(Base):
    __tablename__ = 'console'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        return {
          'name': self.name,
          'id': self.id
        }


class Game(Base):
    __tablename__ = 'game'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    price = Column(String(8))
    description = Column(String(250))

    console_id = Column(Integer, ForeignKey('console.id'))
    console = relationship(Console)

    @property
    def serialize(self):
        # Returns object data in easily serializable format
        return {
            'name': self.name,
            'id': self.id,
            'price': self.price,
            'description': self.description
        }

engine = create_engine('sqlite:///gamestore.db')
Base.metadata.create_all(engine)
