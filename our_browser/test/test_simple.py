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

        self.assertFalse(hasattr(root, 'drawer'))
        self.assertIsNone(root.tag)

        html = root.children[0]
        self.check_node(html, tag='html')

        root_drawer.calc_size((969, 1282), (0, 0))
        #self.assertEqual(html.drawer.calced.rect.width, 969)

        body = html.children[0]
        self.check_node(body, tag='body')
        self.assertIs(body, root_drawer.node) # FIXME chromium thinks that "html" is root

        self.assertEqual(969, body.drawer.calced.rect.width)

        div = body.children[0]
        self.check_node(div, tag='div')
        self.assertEqual(969, div.drawer.calced.rect.width)
        self.assertEqual(0, div.drawer.calced.rect.height)

    def check_node(self, node, tag):
        self.assertIsNotNone(node.tag)
        self.assertEqual(tag, node.tag.text)


if __name__ == '__main__':
    unittest.main()