# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from peewee import *

db = SqliteDatabase('people.db')

class BaseModel(Model):
    class Meta:
        database = db

class Swing(BaseModel):
    name = CharField()
    sdate = DateField()



class Session(BaseModel):
    sdate = DateField()
    name = CharField()
    swing = ForeignKeyField(Swing, backref='swings')
