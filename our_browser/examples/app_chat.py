from os.path import abspath, dirname, join
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))

sys.path.append(PROJ_PATH)

from our_browser.browser import BrowserApp
from our_browser.react import ReactDOM, React, EVENT
from our_browser.listview import ItemBase


HTML_SRC = open(join(HERE, 'htmls', 'chat.html'), encoding='utf-8').read()
HTML_LST = HTML_SRC.split('<body')
HTML_START = HTML_LST[0]
HTML_END = "<body class='width-100p height-100p flex-horizontal'><div class='width-100p height-100p flex-horizontal' id='root' id2='111'></div></body></html>"
HTML_TEXT = HTML_START + HTML_END
HTML_INNER = '>'.join(HTML_LST[1].split('>')[1:]).split('</body')[0].strip()
# print(HTML_TEXT)
# raise Exception(1)

MESSAGES = [
    {
        'sender': 'Sam', 'time': '12:00',
        'text': "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    }, {
        'sender': 'Neo', 'time': '12:05',
        'text': "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur?",
    }, {
        'sender': 'Griffin', 'time': '14:20',
        'text': "But I must explain to you how all this mistaken idea of denouncing pleasure and praising pain was born and I will give you a complete account of the system, and expound the actual teachings of the great explorer of the truth, the master-builder of human happiness. No one rejects, dislikes, or avoids pleasure itself, because it is pleasure, but because those who do not know how to pursue pleasure rationally encounter consequences that are extremely painful. Nor again is there anyone who loves or pursues or desires to obtain pain of itself, because it is pain, but because occasionally circumstances occur in which toil and pain can procure him some great pleasure. To take a trivial example, which of us ever undertakes laborious physical exercise, except to obtain some advantage from it? But who has any right to find fault with a man who chooses to enjoy a pleasure that has no annoying consequences, or one who avoids a pain that produces no resultant pleasure?",
    },
]

class Message(ItemBase):

    def __init__(self, text, sender, time) -> None:
        super().__init__(text)
        self.sender = sender
        self.time = time

MESSAGES = [ Message(a['text'], a['sender'], a['time']) for a in MESSAGES ]


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
        return HTML_INNER


class LeftTopPanel(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.state = {
            'search': False
        }

    def onSettingsClick(self):
        settings_panel_node = self.node.app.ROOT_NODE.getElementById("settings-panel")
        settings_panel_node.react_component.setState({"show": True})

    def onSearchClick(self):
        print('click', self)
        self.setState({
            'search': not self.state['search']
        })

    def render(self):
        if self.state['search']:
            inner =  f'''
                <input class="flex-1 common-padding common-font height-100p white" />
                <div class="width-50 height-100p white">
                    <ImageButton src="our_browser/examples/htmls/cancel.png" onClick={EVENT(self.onSearchClick)} />
                </div>
            '''
        else:
            inner = f'''
                <ImageButton src="our_browser/examples/htmls/settings.png" onClick={EVENT(self.onSettingsClick)}  />
                <ChatButton class="flex-1 top-panel-content-font">Chat App</ChatButton>
                <SearchButton src="our_browser/examples/htmls/search.png" onClick={EVENT(self.onSearchClick)} />
            '''
        return f'''<div class="top-panel-height orange flex-horizontal border flex-align-center" id="left-top-flex">
            {inner}
        </div>
        '''


class ChatButton(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.state = {
            'count': None
        }

    def onClick(self):
        chats_listview = self.node.app.ROOT_NODE.getElementById("chats-listview")
        data_model = chats_listview.attrs['data_model']
        print('&& ??? data_model:', data_model)
        data_model.items_count += 1
        self.setState({
            'count': data_model.items_count
        })
    
    def render(self):
        count = self.state['count']
        print('count ----------', count)
        return f'<button class="flex-1 top-panel-content-font" onclick={EVENT(self.onClick)} >Chat App</button>'


class SendButton(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.mes_k = 0
        self.state = {
            'messages': None
        }

    def onClick(self):
        self.setState({
            'messages': self.appendMessage()
        })

    def appendMessage(self):
        chats_listview = self.node.app.ROOT_NODE.getElementById("messages-listview")
        data_model = chats_listview.attrs['data_model']
        print('&& ??? data_model:', data_model)
        self.mes_k += 1
        if self.mes_k > 2:
            self.mes_k = 0
        messages = data_model.items
        messages.append(MESSAGES[self.mes_k])
        data_model.items = messages
        return messages

    def render(self):
        # if self.state['messages'] == None:
        #     self.state['messages'] = self.appendMessage()
        return f'''
            <div class="image-button button" onclick={EVENT(self.onClick)} >
                <image class="image-26 image-button-content" src="our_browser/examples/htmls/send.png" />
            </div>
        '''

class ImageButton(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.src = props['src']
        self._onClickHandler = props.get('onClick', None)
        self.className = props.get('className', 'image-button button')

    def render(self, inner=''):
        add = ''
        onClickHandler = self._onClickHandler or getattr(self, 'onClickHandler', None)
        if onClickHandler:
            add = f'onclick={EVENT(onClickHandler)}'
        return f'''
            <div class="{self.className}" {add}>
                <image class="image-26 image-button-content" src="{self.src}" />
                {inner}
            </div>
        '''


class ChatMenuButton(ImageButton):

    def __init__(self, props=None) -> None:
        props = {'src': "our_browser/examples/htmls/three_dots.png"}
        super().__init__(props)
        self.state = {
            'activated': False
        }

    def onClickHandler(self):
        self.setState({'activated': not self.state['activated']})

    def render(self):
        inner = ''
        if self.state['activated']:
            inner = f'''
            <div class="absolute top-100 left-0 width-50 height-50 white">
            '''
        return super().render(inner)


class SearchButton(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.src = props['src']
        self.onClickHandler = props['onClick']

    def render(self):
        return f'''
            <div class="image-button button" onclick={EVENT(self.onClickHandler)} >
                <image class="image-26 image-button-content" src="{self.src}" />
            </div>
        '''

class SettingsPanel(React.Component):

    def __init__(self, props) -> None:
        super().__init__()
        self.state = {
            'show': False
        }

    def onCloseClick(self):
        self.setState({'show': False})

    def render(self):
        inner = ''
        if self.state['show']:
            inner = f'''<div class="height-100p width-100p white">
                <ImageButton src="our_browser/examples/htmls/cancel.png" onClick={EVENT(self.onCloseClick)} />
            </div>'''
        return f'''
            <div class="height-100p width-100p absolute left-top-0" id="settings-panel">
                {inner}
            </div>
        '''


def main():
    app = BrowserApp(html_text=HTML_TEXT)

    root = app.ROOT_NODE.getElementById("root")

    root.app = app

    ReactDOM.render("""
        <App count=2 />
    """, root)
    
    app.run()


main()