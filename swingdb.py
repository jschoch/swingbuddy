# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from peewee import *
import datetime

db = SqliteDatabase('swingbuddy.db')

class BaseModel(Model):
    class Meta:
        database = db

class Session(BaseModel):
    sdate = DateField(default=datetime.datetime.now)
    name = CharField()
    comment = TextField(default="none")
    #swing = ForeignKeyField(Swing, backref='swings')

class Swing(BaseModel):
    name = CharField(default="none")
    sdate = DateField(default=datetime.datetime.now)
    screen = CharField(default="no Screen")
    leftVid = CharField(default="no leftVid")
    rightVid = CharField(default="no right vid")
    trc = TextField(default="no trc")
    trcVid = CharField(default="no trc vid")
    club = CharField(default="na")
    comment = TextField(default="none")
    session = ForeignKeyField(Session, backref="swings")
    class Meta:
        indexes = (
            (('leftVid',),True),
            (('rightVid',),True)
        )






class Config(BaseModel):
    vidDir = CharField(default=r"c:/files/test_swings")
    screenDir = CharField(default="c:/files/test_swings")
    ocrServer = CharField(default="not done yet")
    poseServer = CharField(default="http://localhost:5000/gettrc")
    enableScreen = BooleanField(default=True)
    enableTRC = BooleanField(default=True)
    enablePose = BooleanField(default=True)
    autoplay = BooleanField(default=True)
    screen_timeout = IntegerField(default=15)
    screen_coords = CharField(default = "0,0,600,600") # will be split into (a,b,c,d)

    #enable
    #how do you do defaults?
