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

class LMData(BaseModel):
    carry = FloatField(null=True)
    total = FloatField(null=True)
    roll = FloatField(null=True)
    v_launch = FloatField(null=True)
    height = FloatField(null=True)
    descent = FloatField(null=True)
    h_launch = FloatField(null=True)
    lateral = FloatField(null=True)
    spin = FloatField(null=True)
    spin_axis = FloatField(null=True)
    club_path = FloatField(null=True)
    # the raw string from the LLM
    raw= TextField(default="none")

class Swing(BaseModel):
    name = CharField(default="none")
    sdate = DateField(default=datetime.datetime.now)
    screen = CharField(default="no Screen")
    dtlVid = CharField(default="no vid")
    faceVid = CharField(default="no vid")
    dtlTrc = TextField(default="no trc")
    faceTrc = TextField(default = "no trc")
    trcVid = CharField(default="no trc vid")
    club = CharField(default="na")
    comment = TextField(default="none")
    session = ForeignKeyField(Session, backref="swings")
    lmdata = ForeignKeyField(LMData, backref='swings')
    class Meta:
        indexes = (
            (('dtlVid',),True),
            (('faceVid',),True)
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
