from os.path import abspath, join, dirname
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(HERE)

sys.path.append(PROJ_PATH)

from our_browser.browser import main

main()
