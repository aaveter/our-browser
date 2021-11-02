import unittest
from os.path import join, abspath, dirname
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))
print(PROJ_PATH)

sys.path.append(PROJ_PATH)


from our_browser.drawing import make_drawable_tree
from our_browser.browser import noder_parse_text


class TestSimples(unittest.TestCase):

    def test_make_drawable_tree(self):
        root = noder_parse_text('<html><body><div></div></body></html>')
        self.assertIsNotNone(root)

        root_drawer = make_drawable_tree(root)
        self.assertIsNotNone(root_drawer)


if __name__ == '__main__':
    unittest.main()