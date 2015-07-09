#configuration
import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import create_engine

Base = declarative_base()

#class

class Console(Base):
  __tablename__ = 'console'
  name = Column(String(80), nullable = False)
  id = Column(Integer, primary_key = True)

  @property
  def serialize(self):
      return {
        'name': self.name,
        'id': self.id
      }

class Game(Base):
  __tablename__ = 'game'
  name = Column(String(80), nullable = False)
  id = Column(Integer, primary_key = True)
  price = Column(String(8))
  description = Column(String(250))

  console_id = Column(Integer, ForeignKey('console.id'))
  console = relationship(Console)

  @property
  def serialize(self):
  #Returns object data in easily serializable format
    return {
      'name': self.name,
      'id': self.id,
      'price': self.price,
      'description': self.description
    }

if __name__ == '__main__':
  # engine = create_engine(os.environ['DATABASE_URL'])
  engine = create_engine('sqlite:///gamestore.db')
  Base.metadata.create_all(engine)
