import sys

sys.path.append('../noder')

from noder import noder_parse_file, Node

EX_PATH = "../noder/example/tst.html"

ROOT_NODE = noder_parse_file(EX_PATH)

check_is_drawable = lambda node: node.tag and node.tag.text in ('div', 'h1', 'p', 'a', 'span', 'input/', 'h2')
        

def make_drawable_tree(parent, drawer=None):

    _drawer = None

    for node in parent.children:
        if not drawer and node.tag and node.tag.text == 'body':
            drawer = DrawerBlock(node)

        elif check_is_drawable(node):
            DrawerBlock(node)

        _drawer = make_drawable_tree(node, drawer)

    if not drawer:
        drawer = _drawer

    return drawer


class DrawerNode:

    def __init__(self, node) -> None:
        self.node = node
        node.drawer = self

    def __str__(self) -> str:
        return '_drawer_ ' + str(self.node)

    def __repr__(self) -> str:
        return self.__str__()


class DrawerBlock(DrawerNode):

    def __init__(self, node) -> None:
        super().__init__(node)

    def calc_size(self, size, pos, started=True):
        margin = 5
        height = 20

        size_my = [size[0] - 2*margin, height]
        size_calced = [size_my[0], size_my[1]]
        pos_my = [pos[0] + margin, pos[1] + margin]
        
        _ps = [pos_my[0], pos_my[1] + height]
        
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            
            drawer = node.drawer

            drawer.calc_size(size_my, _ps, started)
            wh = drawer.size_calced
            
            for i in (0, 1):
                if wh[i] > size_calced[i]:
                    size_calced[i] = wh[i]
            _ps[1] += wh[1] + margin

            if _ps[1] + wh[1] - pos_my[1] > size_calced[1]:
                size_calced[1] = _ps[1] + wh[1] - pos_my[1]

        self.size_calced = size_calced
        self.pos = pos_my

    def draw(self, cr, started=-0.2):
        started += 0.2

        ps, size_calced = self.pos, self.size_calced

        cr.set_source_rgb(0.2, 0.23 + started, 0.9)
        cr.rectangle(ps[0], ps[1], size_calced[0], size_calced[1])
        cr.fill()

        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.set_font_size(11)
        cr.move_to(ps[0]+5, ps[1]+14)
        #cr.show_text(str(self.node.tag))# + ' ' + self.text if self.text else '')
        cr.show_text(self.node.text if self.node.text else '')
        
        for node in self.node.children:
            
            if not hasattr(node, 'drawer'):
                continue

            node.drawer.draw(cr, started)


ROOT = make_drawable_tree(ROOT_NODE)
print(ROOT)
