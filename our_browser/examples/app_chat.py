from os.path import abspath, dirname, join
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))

sys.path.append(PROJ_PATH)

from our_browser.browser import BrowserApp
from our_browser.react import ReactDOM, React, EVENT


HTML_SRC = open(join(HERE, 'htmls', 'chat.html'), encoding='utf-8').read()
HTML_LST = HTML_SRC.split('<body')
HTML_START = HTML_LST[0]
HTML_END = "<body><div class='width-100p height-100p' id='root'></div></body></html>"
HTML_TEXT = HTML_START + HTML_END
HTML_INNER = '>'.join(HTML_LST[1].split('>')[1:]).split('</body')[0].strip()
# print(HTML_TEXT)
# raise Exception(1)


class App(React.Component):

    def __init__(self, props) -> None:
        super().__init__()

        self.state = {
            'count': props['count']
        }

    def onClick(self):
        print('>>>>>>>>> COMPONENT click:', id(self))
        self.setState({
            'count': int(self.state['count']) + 1
        })
    
    def render(self):
        count = self.state['count']
        print('count ----------', count)
        #return f'<div><p class="yellow">{count}</p><button class="red" onclick={EVENT(self.onClick)} /></div>'
        return HTML_SRC # FIXME want INNER


class ChatButton(React.Component):

    def __init__(self, props) -> None:
        super().__init__()

        self.state = {
            'count': 0 #props['count']
        }

    def onClick(self):
        print('>>>>>>>>> COMPONENT click:', id(self), "app.root:", self.node.app.ROOT_NODE)
        chats_listview = self.node.app.ROOT_NODE.getElementById("messages-listview")
        data_model = chats_listview.attrs['data_model']
        print('&& ??? data_model:', data_model)
        data_model.items_count = int(self.state['count']) + 1
        self.setState({
            'count': data_model.items_count
        })
    
    def render(self):
        count = self.state['count']
        print('count ----------', count)
        #return f'<div><p class="yellow">{count}</p><button class="red" onclick={EVENT(self.onClick)} /></div>'
        return f'<button class="flex-1 top-panel-content-font" onclick={EVENT(self.onClick)} >Chat App</button>'


def main():
    app = BrowserApp(html_text=HTML_TEXT)

    root = app.ROOT_NODE.getElementById("root")
    print('FOUND root:', root, id(root), 'styler:', root.root.styler)

    root.app = app

    ReactDOM.render("""
        <App count=2 />
    """, root)

    print('RENDERED root:', app.ROOT_NODE)
    
    app.run()


main()