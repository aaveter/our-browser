from os.path import abspath, dirname, join
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(dirname(HERE))

sys.path.append(PROJ_PATH)

from our_browser.browser import main

main(html_path=join(PROJ_PATH, 'our_browser', 'noder', 'example', 'listview.html'))