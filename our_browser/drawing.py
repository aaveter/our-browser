from os.path import exists, abspath
from our_browser.listview import draw_listview
import cairo


check_is_drawable = lambda node: node.tag and node.tag.text not in ('style', 'script', 'head') and not node.tag.text.startswith('!')
#node.tag.text in ('div', 'h1', 'p', 'a', 'span', 'input/', 'h2')

DEFAULT_STYLES = {
    'html': {
        'width': 'auto',
        'height': 'auto'
    }
}


def make_drawable_tree(parent, drawer=None, with_html=False):

    _drawer = None

    for node in parent.children:
        if not drawer and node.tag and ((with_html and node.tag.text == 'html') or node.tag.text == 'body'):
            drawer = DrawerBlock(node)

        elif check_is_drawable(node):
            DrawerBlock(node)

        _drawer = make_drawable_tree(node, drawer, with_html=with_html)

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


class Rect:

    def __init__(self) -> None:
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        

def get_size_prop_from_node(node, name, parent_prop, default=0):
    if not hasattr(node, 'style'):
        return 0
    prop = node.style.get(name, default)
    if type(prop) == tuple:
        hproc = prop[0]
        if parent_prop == None:
            return default
        prop = hproc * parent_prop / 100.0
    elif type(prop) == str:
        if parent_prop == None:
            return default
        if prop == 'auto':
            prop = parent_prop
        else:
            prop = default
    return prop


def fix_lines_line_for_ln(lines, i, width_ln):
    line = lines[i]
    if len(line) > width_ln:
        ix = line[:width_ln].rfind(' ')
        if ix < 0:
            return -1
        line_add = line[ix+1:]
        line = line[:ix]
        lines[i] = line
        add_i = i+1
        lines.insert(add_i, line_add)
        return add_i
    return -1

class Calced:

    def __init__(self) -> None:
        self.rect = Rect()
        self.calced = False
        self.last_size_0 = -1
    
    def calc_params(self, node, size):
        background_color = color = border = None
        font_size = 11
        display = None
        if hasattr(node, 'style'):
            color = node.style.get('color', None)
            background_color = node.style.get('background-color', None)
            font_size = node.style.get('font-size', 11)
            border = node.style.get('border', None)
            display = node.style.get('display', None)

        self.color = color
        self.background_color = background_color
        self.font_size = font_size
        self.border = border
        self.display = display

        self.padding = padding = get_size_prop_from_node(node, 'padding', None)
        padding_2 = padding * 2
        text_width = size[0] - padding_2

        tag = node.tag.text

        image = None
        if tag == 'image':
            image = self.calc_image(tag, node)

        if not hasattr(node, 'lines'):
            node.lines = None
        if node.text:
            self.calc_lines(node, font_size, text_width)

        self.last_size_0 = text_width

        self.margin = margin = get_size_prop_from_node(node, 'margin', None)

        width, height = self.calc_width_height(node, size, margin, padding_2, font_size, image)
        
        self.calc_rect(node, size, width, height, margin)

    def calc_width_height(self, node, size, margin, padding_2, font_size, image):
        height_default = 0
        if node.lines:
            height_default = font_size * len(node.lines) + margin + padding_2
        if image:
            image_height = image.get_height()
            if image_height > height_default:
                height_default = image_height + padding_2
        
        width = get_size_prop_from_node(node, 'width', size[0], -1)
        height = get_size_prop_from_node(node, 'height', size[1], height_default)
        min_height = get_size_prop_from_node(node, 'min-height', None)

        if min_height > height:
            height = min_height

        if size[1] < height:
            size = (size[0], height)

        self.min_height = min_height

        return width, height

    def calc_lines(self, node, font_size, text_width):
        if node.lines == None or self.last_size_0 < text_width or True: # FIXME
            node.lines = node.text.split('\n')
        lines = node.lines
        font_size_w = font_size * 0.46 #/2
        if text_width > font_size_w:
            width_ln = int(text_width / font_size_w)
            i = len(lines) - 1
            while i >= 0:
                add_i = i
                while add_i >= 0:
                    add_i = fix_lines_line_for_ln(lines, add_i, width_ln)
                i -= 1

    def calc_image(self, node):
        image = None
        self.image = None
        self.image_src = None
        if node.attrs:
            self.image_src = image_src = node.attrs.get('src', None)
            if image_src:
                image_src = abspath(image_src)
            if image_src and exists(image_src):
                image = self.image = cairo.ImageSurface.create_from_png(image_src)
        return image

    def calc_rect(self, node, size, width, height, margin):
        if hasattr(node, 'drawer') and node.level > 2:
            self.rect.width = size[0] - 2*margin
            self.rect.height = height
        else:
            self.rect.width = width if width >= 0 else size[0]
            self.rect.height = height

        if not self.calced:
            self.calced = True


class DrawerBlock(DrawerNode):

    def __init__(self, node) -> None:
        super().__init__(node)
        self.calced = Calced()

    def calc_size(self, size, pos, started=True):
        calced = self.calced.calced

        self.calced.calc_params(self.node, size)
        size_my = self.calced.rect.width, self.calced.rect.height

        tag = self.node.tag.text if self.node.tag else None
        
        size_calced = (size_my[0], size_my[1])
        pos_my = [pos[0] + self.calced.margin, pos[1] + self.calced.margin]
        _ps = [pos_my[0], pos_my[1]]
        
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            
            drawer = node.drawer

            _size_my = drawer.calc_size(size_my, (_ps[0], _ps[1]), started)

            _ps, size_calced = self.add_subnode_pos_size(node, _ps, size_calced, self.calced.margin)

        h = _ps[1] - pos_my[1]
        if h > size_calced[1]:
            size_calced = (size_calced[0], h)

        self.size_calced = size_calced
        self.pos = pos_my

        if not calced:
            print('>>>', '  '*self.node.level, self.node.tag, pos, size, '->', size_calced)

        if tag == 'button':
            print('(button)', self.node.level, self.pos, self.size_calced, size_my, self.node.style)

        return size_my

    def add_subnode_pos_size(self, node, pos_my, size_calced, margin):
        pos = [pos_my[0], pos_my[1]]
        drawer = node.drawer
        wh = drawer.size_calced
            
        if wh[0] > size_calced[0]:
            size_calced = (wh[0], size_calced[1])

        if wh[1] > size_calced[1]:
            size_calced = (size_calced[0], wh[1])

        if pos[1] + wh[1] - pos_my[1] > size_calced[1]:
            size_calced = (size_calced[0], pos[1] + wh[1] - pos_my[1])

        pos[1] += wh[1] + margin
        return pos, size_calced

    def draw(self, cr, started=-0.2):
        started += 0.2

        ps, size_calced = self.pos, self.size_calced

        background_color = self.calced.background_color
        color = self.calced.color
        font_size = self.calced.font_size
        border = self.calced.border
        image = getattr(self.calced, 'image', None)

        rect = (ps[0], ps[1], size_calced[0], size_calced[1])

        if background_color:
            self.draw_background(cr, background_color, rect)

        if image:
            self.draw_image(cr, image, rect)

        if border:
            self.draw_border(cr, rect, border[0], border[1], border[2])

        if color:
            cr.set_source_rgb(*hex2color(color))
        else:
            cr.set_source_rgb(0.1, 0.1, 0.1)
        padding = self.calced.padding
        self.draw_lines(cr, self.node.lines, (ps[0]+padding, ps[1]+padding), font_size)

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

    def draw_background(self, cr, background_color, rect):
        cr.set_source_rgb(*hex2color(background_color))
        cr.rectangle(*rect)
        cr.fill()

    def draw_border(self, cr, rect, border_width, border_type, border_color):
        rect = (rect[0]+0.5, rect[1]+0.5, rect[2]-1, rect[3]-1)
        cr.rectangle(*rect)
        cr.set_source_rgb(*hex2color(border_color))
        cr.set_line_width(border_width)
        cr.stroke()

    def draw_lines(self, cr, lines, pos, font_size):
        if not lines:
            return

        cr.set_font_size(font_size)
        x, y = pos
        
        for line in lines:
            cr.move_to(x, y + font_size) #+5
            cr.show_text(line)
            y += font_size

    def draw_image(self, cr, image, rect):
        cr.set_source_surface(image, rect[0], rect[1])
        cr.paint()

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


