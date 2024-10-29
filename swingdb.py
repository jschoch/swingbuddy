# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from peewee import *

db = SqliteDatabase('people.db')

class Swing(Model):
    name = CharField()
    sdate = DateField()

    class Meta:
        database = db # This model uses the "people.db" database.
