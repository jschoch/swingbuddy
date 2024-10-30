# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass

import unittest
from util import find_swing,gen_screenshot,proc_screenshot,testdb
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

if __name__ == '__main__':
    unittest.main()
