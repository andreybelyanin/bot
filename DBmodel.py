import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///clients.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)


class Clients(Base):
    __tablename__ = 'clients'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(80), nullable=False)
    description = sa.Column(sa.String(80))
    created = sa.Column(sa.DateTime)


class Appointment(Base):
    __tablename__ = 'appointment'
    id = sa.Column(sa.Integer, primary_key=True)
    appointment_date = sa.Column(sa.String(20))
    description = sa.Column(sa.String(80))
    price = sa.Column(sa.Integer)
    client_id = sa.Column(sa.Integer, sa.ForeignKey('clients.id'))


class Notes(Base):
    __tablename__ = 'notes'
    note_date = sa.Column(sa.String(20), primary_key=True)
    note = sa.Column(sa.Text)


class GPIO(Base):
    __tablename__ = 'gpio'
    id = sa.Column(sa.Integer, primary_key=True)
    comand = sa.Column(sa.Integer)
    status = sa.Column(sa.Integer)


Base.metadata.create_all(engine)
