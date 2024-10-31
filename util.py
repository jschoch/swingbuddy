# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

#  doing stuff
import os
import datetime
import sys
import glob
from peewee import *
from swingdb import Swing, Session,Config

db = SqliteDatabase('test.db')

def get_files_with_extension(directory, extension):
    return [os.path.join(directory, f) for f in os.listdir(directory) if
            (os.path.isfile(os.path.join(directory, f)) and
             os.path.splitext(f)[1].lower() == f'.{extension.lower()}' and
             os.path.getsize(os.path.join(directory, f)) > 0)]


def sort_by_creation_time(files):
    #sorted_files = sorted(files, key=lambda x: datetime.fromtimestamp(os.path.getctime(x)))
    sorted_files = sorted(files, key=lambda x: os.path.getctime(x))
    return sorted_files


def find_swing(directory_path,extension):
    print(f"finding swing videos from {directory_path}")
    # how do i use logger from here?

    print(f"directory path {directory_path}")
    #extension = 'trc'  # Change this to your desired extension
    files = get_files_with_extension(directory_path, extension)
    print(f" files: {files}")
    sorted_files = sort_by_creation_time(files)
    if(len(sorted_files) > 0):
        print(sorted_files[-1])
        return(sorted_files[-1])

    #return vid

def gen_trc():
    print('gen trc')

def gen_screenshot():
    print('gen screen')
    # spin up thread and timer to grab the screenshot

def proc_screenshot(fname):
    print(f"processing screenshot: {fname}")

def ocr_screen():
    print('ocr')

def testdb():
    print("setting up test db")
    db.drop_tables([Swing,Config,Session])
    db.create_tables([Swing,Config,Session])
    Config.get_or_create(id=1, vidDir="./test_data/swings")
    return db

def test_fetch_trc(config):
    import requests
    url = config.poseServer + "?path="+ requests.utils.quote('c:/Files/test_small.mp4')
    print(f" url: {url}")
    contents = requests.get(url)
    return contents


