from os.path import abspath, join, dirname
import sys

HERE = dirname(abspath(__file__))
DATA_PATH = join(HERE, 'data')
PROJ_PATH = dirname(HERE)
# NODER_PATH = abspath(join(PROJ_PATH, '..', 'noder'))

# sys.path.append(NODER_PATH)

# from noder import noder_parse_file, noder_parse_text
from our_browser.noder.noder import noder_parse_file, noder_parse_text
