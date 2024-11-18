# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

import unittest
from util import find_swing,gen_screenshot,proc_screenshot,testdb,test_fetch_trc,fFUCKYOU,get_pairs,move_files
from swingdb import Swing, Session,Config,LMData
import logging
import sys
from peewee import *
import shutil
import os

models = [Swing,Config,Session,LMData]
testdb = SqliteDatabase('test.db')


class TestFindSwing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        testdb.create_tables(models)  # Create tables if they don't exist
    
    def setUp(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        streamHandler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(streamHandler)
        self.db = testdb
        #self.db.create_tables(models)  # Create tables if they don't exist

        self.config = Config.create()
        self.assertIsNotNone(self.db)
        self.assertIsNotNone(self.config)
        self.logger.debug(f"config: {self.config.vidDir}")

    def tearDown(self):
        # Clean up the database and close the connection
        #self.db.drop_tables(models)
        #self.db.close()
        None
    
    @classmethod
    def tearDownClass(cls):
        print("tearDownClass: Running after all tests")
        #del cls.shared_resource
        testdb.drop_tables(models)

    def test_f(self):
        f = find_swing("./test_data/swings","mp4")
        self.assertIsNotNone(f)
        self.assertEqual(len(f), 2)  # Assuming there's only one swing file in the directory

    def test_move_swings(self):
        self.logger.debug("moving swings")
        swings = find_swing(self.config.kinoveaDir,"mp4")
        kva = find_swing(self.config.kinoveaDir,"kva")  
        swings_kva = swings + kva
        self.assertEqual(len(swings_kva), 4)  # Assuming there's only one swing file in the directory
        self.logger.debug(f"target dir {self.config.vidDir}")
        new_folder = move_files(swings_kva,self.config.vidDir)
        self.logger.debug(f"new folder: {new_folder}")

        #move the files back
        for f in os.listdir(new_folder):
            shutil.move(os.path.join(new_folder,f),self.config.kinoveaDir)
        
    

if __name__ == '__main__':
    unittest.main()
