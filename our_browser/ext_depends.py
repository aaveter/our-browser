from os.path import abspath, join, dirname
import sys

HERE = dirname(abspath(__file__))
DATA_PATH = join(HERE, 'data')

sys.path.append('../noder')

from noder import noder_parse_file, noder_parse_text
