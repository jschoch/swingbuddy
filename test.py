# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

import unittest
from util import find_swing,gen_screenshot,proc_screenshot,testdb,test_fetch_trc,fFUCKYOU,get_pairs
from swingdb import Swing, Session,Config


class TestFindSwing(unittest.TestCase):
    db = None
    config = None
    def test_create_db(self):
        global db,config
        db = testdb()
        config = Config.get_by_id(1)
        self.assertIsNotNone(db)
        self.assertIsNotNone(config)
        print(f"config: {config.vidDir}")

    def test_f(self):
        f = find_swing("./test_data/swings","mp4")
        self.assertIsNotNone(f)

    def test_proc_screenshot(self):
        fname = "./test_data/test.png"
        r = proc_screenshot(fname)
        self.assertIsNotNone(r)
    def test_fetch_trc(self):
        global db,config
        contents = test_fetch_trc(config)
        print(f"contents: {contents}")
        self.assertIsNotNone(contents)
        self.assertEqual(contents.status_code, 200)
        self.assertNotEqual(contents.text,"ERROR")
        self.assertNotEqual(contents.text,"Bad file path")
        print(contents.text)
        #print(contents.json())
    def test_fu(self):
        #fFUCKYOU()
        get_pairs("c:/Files/test_swings")


if __name__ == '__main__':
    unittest.main()
