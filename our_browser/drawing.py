import sys
from .listview import draw_listview


check_is_drawable = lambda node: node.tag and node.tag.text not in ('style', 'script', 'head') and not node.tag.text.startswith('!')
#node.tag.text in ('div', 'h1', 'p', 'a', 'span', 'input/', 'h2')
        

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


class Calced:
    
    def calc_params(self, node, size):
        self.margin = 0
        self.height = 0
        self.min_height = 0
        
        if hasattr(node, 'style'):
            self.margin = node.style.get('margin', 0) 
            self.height = node.style.get('height', 0)
            self.min_height = int(node.style.get('min-height', 0))

        if type(self.height) == tuple:
            hproc = self.height[0]
            self.height = hproc * size[1] / 100.0

        if self.min_height > self.height:
            self.height = self.min_height

        if size[1] < self.height:
            size[1] = self.height


class DrawerBlock(DrawerNode):

    def __init__(self, node) -> None:
        super().__init__(node)
        self.calced = Calced()

    def calc_size(self, size, pos, started=True):
        self.calced.calc_params(self.node, size)

        tag = self.node.tag.text if self.node.tag else None
        if hasattr(self.node, 'drawer') and self.node.level > 2: #tag not in ('body', 'html'):
            size_my = [size[0] - 2*self.calced.margin, self.calced.height]
        else:
            size_my = [size[0], size[1]]
        
        size_calced = [size_my[0], size_my[1]]
        pos_my = [pos[0] + self.calced.margin, pos[1] + self.calced.margin]
        _ps = [pos_my[0], pos_my[1]]
        
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            
            drawer = node.drawer

            drawer.calc_size(size_my, [_ps[0], _ps[1]], started)

            _ps = self.add_subnode_pos_size(node, pos_my, size_calced, self.calced.margin)

        self.size_calced = size_calced
        self.pos = pos_my

        if tag == 'button':
            print('(button)', self.node.level, self.pos, self.size_calced, size_my, self.node.style)

    def add_subnode_pos_size(self, node, pos_my, size_calced, margin):
        pos = [pos_my[0], pos_my[1]]
        drawer = node.drawer
        wh = drawer.size_calced
            
        for i in (0, 1):
            if wh[i] > size_calced[i]:
                size_calced[i] = wh[i]
        pos[1] += wh[1] + margin

        if pos[1] + wh[1] - pos_my[1] > size_calced[1]:
            size_calced[1] = pos[1] + wh[1] - pos_my[1]

        return pos

    def draw(self, cr, started=-0.2):
        started += 0.2

        ps, size_calced = self.pos, self.size_calced

        background_color = color = None
        font_size = 11
        if hasattr(self.node, 'style'):
            color = self.node.style.get('color', None)
            background_color = self.node.style.get('background-color', None)
            font_size = self.node.style.get('font-size', 11)

        if background_color:
            cr.set_source_rgb(*hex2color(background_color))
            cr.rectangle(ps[0], ps[1], size_calced[0], size_calced[1])
            cr.fill()
        # else:
        #     cr.set_source_rgb(1.0, 1.0, 1.0)
        #     #cr.set_source_rgb(0.2, 0.23 + started, 0.9)
        # cr.rectangle(ps[0], ps[1], size_calced[0], size_calced[1])
        # cr.fill()

        if color:
            cr.set_source_rgb(*hex2color(color))
        else:
            cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.set_font_size(font_size)
        cr.move_to(ps[0]+5, ps[1]+14)
        cr.show_text(self.node.text if self.node.text else '')

        tag = self.node.tag.text if self.node.tag else None
        if tag == 'listview':
            listview = self.node.attrs.get('data_model', None)
            if listview and listview.template:
                draw_listview(self, listview, cr)
                return
        
        for node in self.node.children:
            
            if not hasattr(node, 'drawer'):
                continue

            node.drawer.draw(cr, started)

    def propagateEvent(self, pos, event_name):
        if (
            self.pos[0] <= pos[0] < self.pos[0] + self.size_calced[0] and 
            self.pos[1] <= pos[1] < self.pos[1] + self.size_calced[1]
        ):
            ev = self.node.attrs.get(event_name, None) if self.node.attrs else None
            if ev and ev():
                return

            for ch in self.node.children:
                ret = _propagateEvent(ch, pos, event_name)
                if ret:
                    return ret

             
def _propagateEvent(node, pos, event_name):
    drawer = getattr(node, 'drawer', None)
    if drawer:
        return drawer.propagateEvent(pos, event_name)
    
    for ch in node.children:
        ret = _propagateEvent(ch, pos, event_name)
        if ret:
            return ret


def hex2color(color_hex):
    color_hex = color_hex.split('#')[1]
    return (int(color_hex[:2], 16)/255.0, int(color_hex[2:4], 16)/255.0, int(color_hex[4:6], 16)/255.0)


