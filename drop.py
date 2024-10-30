from swingdb import Swing, Session, Config
from peewee import *

db = SqliteDatabase('people.db')

models = (Swing, Session, Config)

db.drop_tables(models)
db.create_tables(models)
