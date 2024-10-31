# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from peewee import *
import datetime

db = SqliteDatabase('people.db')

class BaseModel(Model):
    class Meta:
        database = db

class Swing(BaseModel):
    name = CharField(default="none")
    sdate = DateField(default=datetime.datetime.now)
    screen = CharField(default="no Screen")
    leftVid = CharField(default="no leftVid")
    rightVid = CharField(default="no right vid")
    trc = CharField(default="no trc")
    trcVid = CharField(default="no trc vid")



class Session(BaseModel):
    sdate = DateField()
    name = CharField()
    swing = ForeignKeyField(Swing, backref='swings')


class Config(BaseModel):
    vidDir = CharField(default=r"c:\files\swingvids")
    screenDir = CharField(default="c:\files\swingscreens")
    ocrServer = CharField(default="not done yet")
    poseServer = CharField(default="http://localhost:5000/gettrc")
    enableScreen = BooleanField(default=True)
    enableTRC = BooleanField(default=True)
    enablePose = BooleanField(default=True)
    #enable
    #how do you do defaults?
