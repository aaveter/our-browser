from os.path import abspath, dirname, join
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))

sys.path.append(PROJ_PATH)

from our_browser.our_browser import BrowserApp
from our_browser.react import ReactDOM, React, EVENT


HTML_TEXT = """<html>
<style>
    .block {border-color: #cccccc;}
    div {min-height: 20; margin: 5;}
    h1 {height: 30; margin: 10;}
    h2 {height: 25; margin: 8;}
    p {height: 15; margin: 5;}
    a {height: 15; margin: 3;}
    button {height: 30; margin: 10;}
    .red {background-color:#ff5555; color: #ffffff;}
    .blue {background-color: #5555ff;}
    .green {background-color: #55cc55;}
    .yellow {background-color: #ffe4c4;}

    html, body {
        height: 100%; margin: 0; padding: 0;
    }
    .page {
        height: 50%;
    }
    .page-content {
        margin: 10px;
        border: 1px solid #cccccc;
    }
</style>
<body><div id='root' class='red'></div></body></html>"""


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
        return f'<div><p class="yellow">{count}</p><button class="red" onclick={EVENT(self.onClick)} /></div>'



def main():
    app = BrowserApp(html_text=HTML_TEXT)

    root = app.ROOT_NODE.getElementById("root")
    print('FOUND root:', root, id(root))

    ReactDOM.render("""
        <App count=2 />
    """, root)

    print('RENDERED root:', app.ROOT_NODE)

    root.app = app
    
    app.run()


main()
