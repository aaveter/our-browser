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

        root_drawer.calc_size((969, 1282), (0, 0), (0, 0))
        #self.assertEqual(html.drawer.calced.rect.width, 969)

        body = html.children[0]
        self.check_node(body, tag='body')
        self.assertIs(body, root_drawer.node) # FIXME chromium thinks that "html" is root

        self.assertEqual(969, body.drawer.calced.rect.width)

        div = body.children[0]
        self.check_node(div, tag='div')
        self.assertEqual(969, div.drawer.calced.rect.width)
        self.assertEqual(0, div.drawer.calced.rect.height)

    def test_page_sizes(self):
        root = noder_parse_text('<html><body><span></span></body></html>')
        body = root.children[0].children[0]
        body.innerHTML = '<style>div {height:500px;}</style><div></div>'
        html = body.parent

        root_drawer = make_drawable_tree(root, with_html=True)
        root_drawer.calc_size((300, 300), (0, 0), (0, 0))

        div = body.children[1]
        self.assertEqual(500, div.drawer.calced.rect.height)
        self.assertEqual(500, body.drawer.size_calced[1])

    def check_node(self, node, tag):
        self.assertIsNotNone(node.tag)
        self.assertEqual(tag, node.tag.text)

    def test_react(self):
        from our_browser.browser import BrowserApp, document
        from our_browser.react import ReactDOM, React, obj, react
        from our_browser.listview import ItemBase

        class App(React.Component):

            def render(self):
                return '''<div class="flex-horizontal height-100p" id="main">
                    <div class="flex-1 _border height-100p green" id="left-flex-1">
                        <div class="height-100p flex-vertical" id="left-flex">
                            <LeftTopPanel />
                            <FilterButtons />
                            <div class="flex-1 _white _border-right common-padding_ common-font">
                                <listview class="page green common-padding" id="chats-listview" items-count="1000">
                                    <template>
                                        <ChatItem />
                                    </template>
                                    <items />
                                </listview>
                            </div>
                        </div>
                    </div>
                    <HorSplitter />
                    <div class="flex-3 flex-vertical_ green_ height-100p" id="right-flex-3">
                        <RightPanel />
                    </div>
                    <SettingsPanel />
                </div>'''

        app = BrowserApp(html_text='''<html>
        <style>
        </style>
        <body>
            <div id='root'></div>
        </body>
        </html>''')

        root = document.getElementById("root")
        root.app = app

        ReactDOM.render("""
            <App count=2 />
        """, root)

        app.prepare_run()

        chats_listview = document.getElementById("chats-listview")
        #chats_listview.attrs['data_model'].items = CHATS


if __name__ == '__main__':
    unittest.main()