from os.path import abspath, join, dirname, exists
import sys

HERE = dirname(abspath(__file__))
PROJ_PATH = dirname(HERE)

sys.path.append(PROJ_PATH)

from argparse import ArgumentParser

args = ArgumentParser()
args.add_argument('-html', action='store', default=None)
args.add_argument('-example', action='store', default=None)
args = args.parse_args()

if args.html:
    from our_browser.browser import main
    main(html_path=args.html)

elif args.example:
    EXAMPLES_PATH = join(HERE, 'examples')
    if args.example.startswith('app_'):
        full = join(EXAMPLES_PATH, args.example+".py")
        if exists(full):
            print(full)
            import importlib
            p = importlib.import_module('our_browser.examples.'+args.example)
            p.main()