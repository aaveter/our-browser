from os.path import abspath, dirname, join
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))

sys.path.append(PROJ_PATH)

from our_browser.our_browser import BrowserApp
from our_browser.react import ReactDOM, React


class App(React.Component):

    def __init__(self, props) -> None:
        super().__init__()

        self.state = {
            'count': props['count']
        }

    def onClick(self):
        self.setState({
            'count': self.state['count'] + 1
        })
    
    def render(self):
        count = self.state['count']
        return f'<div><p>{count}</p><button onclick={self.onClick}/></div>'


def main():
    app = BrowserApp(html_text="""<html><body><div id='root'></div></body></html>""")

    root = app.ROOT_NODE.getElementById("root")
    print('FOUND root:', root)
    
    ReactDOM.render("""
        <App count=2 />
    """, root)
    
    app.run()


main()
