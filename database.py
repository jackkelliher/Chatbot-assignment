#Creates the database used for server.py
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import Table, Column, Integer, String, delete
import datetime

Base = declarative_base()

class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key = True)
    to = Column(String)
    from_user = Column(String)
    message = Column(String)
    sent = Column(String)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    username = Column(String)
    last_logged = Column(String)

class database():
    def start_engine(self):
        self._engine = create_engine('sqlite:///chat-client.db',
            future=True)
        self.session = Session(self._engine)

    def create_tables(self):
        message = Message()
        #message.__table__.drop(self._engine)
        Base.metadata.create_all(self._engine)

    def add_entry(self, table, to, from_user, message):
        time_now = str(datetime.datetime.utcnow())
        if(table == 'message'):
            nmessage = Message(to=to, from_user=from_user, message=message, sent=time_now)
        elif(table=='user'):
            nmessage = User(username= message, last_logged= time_now)
        self.session.add(nmessage)
        self.session.commit()

    def get_entry(self, table, attribute, value):
        if(table == 'message'):
            query = select(Message).where(getattr(Message, attribute) == value)
        elif(table == 'user'):
            query = select(User).where(User.username == value)
        cat = self.session.execute(query).scalars()
        return(cat)

if __name__ == '__main__':
    db = database()
    db.start_engine()
    db.create_tables()