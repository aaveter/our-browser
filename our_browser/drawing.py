from os.path import exists, abspath
from our_browser.listview import draw_listview
import cairo, math
import threading


check_is_drawable = lambda node: node.tag and node.tag.text not in ('style', 'script', 'head') and not node.tag.text.startswith('!')

DEFAULT_STYLES = {
    'html': {
        'width': 'auto',
        'height': 'auto'
    }
}


class InputControl:
    focus_into = None
    timer = None
    ending = False
    refresher = None

    def set_refresher(self, func):
        self.refresher = func

    def set_focus(self, elem):
        if not elem:
            if self.focus_into:
                self.focus_into.on_focus_lost()
            self.focus_into = None
        elif hasattr(elem, 'on_timer'):
            if self.focus_into == elem:
                return
            self.focus_into = elem

        if self.focus_into:
            self.focus_into.on_focus_got()
            self.ending = False
            self.start_timer()
        else:
            self.stop_timer()

    def start_timer(self):
        if self.ending:
            return
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(0.5, self.on_timer)
        self.timer.start()

    def stop_timer(self):
        if not self.timer:
            return
        print('[ TIMER ] stop')
        self.ending = True
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def on_timer(self):
        if self.focus_into:
            self.focus_into.on_timer()
            self.start_timer()


INPUT_CONTROL = InputControl()


def make_drawable_tree(parent, drawer=None, with_html=False):

    _drawer = None

    for node in parent.children:
        if not drawer and node.tag and ((with_html and node.tag.text == 'html') or node.tag.text == 'body'):
            drawer = make_drawer(parent, node)

        elif check_is_drawable(node):
            make_drawer(parent, node)

        _drawer = make_drawable_tree(node, drawer, with_html=with_html)

    if not drawer:
        drawer = _drawer

    return drawer


def make_drawer(parent, node):
    style = getattr(node, 'style', None)

    drawer = None
    if style:
        if style.get('display', None) == 'flex':
            drawer = DrawerFlex(node)

        elif style.get('flex', None) != None:
            drawer = DrawerFlexItem(node)

    if not drawer:
        drawer = DrawerBlock(node)

    if drawer:
        if node.tag and node.tag.text == 'input':
            AbilityInput(drawer)

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
    
    def calc_params(self, node, size, debug=False):
        background_color = color = border = border_radius = None
        border_left = border_right = border_top = border_bottom = None
        font_size = 11
        display = None
        flex = None
        flex_direction = None
        align_items = None
        if hasattr(node, 'style'):
            color = node.style.get('color', None)
            background_color = node.style.get('background-color', None)
            font_size = int(node.style.get('font-size', 11))
            
            border = node.style.get('border', None)
            border_left = node.style.get('border-left', None)
            border_right = node.style.get('border-right', None)
            border_top = node.style.get('border-top', None)
            border_bottom = node.style.get('border-bottom', None)

            border_radius = int(node.style.get('border-radius', 0))

            display = node.style.get('display', None)
            flex = node.style.get('flex', None)
            flex_direction = node.style.get('flex-direction', None)
            align_items = node.style.get('align-items', None)

        self.color = color
        self.background_color = background_color
        self.border_radius = border_radius
        self.font_size = font_size

        self.border = border
        self.border_left = border_left
        self.border_right = border_right
        self.border_top = border_top
        self.border_bottom = border_bottom
        
        self.display = display
        self.flex = flex
        self.flex_direction = flex_direction
        self.align_items = align_items

        self.padding = padding = get_size_prop_from_node(node, 'padding', None)
        padding_2 = padding * 2
        text_width = size[0] - padding_2

        tag = node.tag.text

        image = None
        if tag == 'image':
            image = self.calc_image(node)

        self.max_width = max_width = get_size_prop_from_node(node, 'max-width', None)

        if not hasattr(node, 'lines'):
            node.lines = None
        if node.text:
            if max_width and text_width > max_width:
                text_width = max_width
            self.calc_lines(node, font_size, text_width)
        else:
            if node.lines:
                node.lines = None

        if debug:
            print('^^^^^ lines count:', len(node.lines) if node.lines != None else '-')

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
        
        self._width = width = get_size_prop_from_node(node, 'width', size[0], -1)
        self._height = height = get_size_prop_from_node(node, 'height', size[1], -1) #height_default)
        
        if height < 0:
            height = height_default
        
        min_height = get_size_prop_from_node(node, 'min-height', None)
        max_height = get_size_prop_from_node(node, 'max-height', None)

        min_width = get_size_prop_from_node(node, 'min-width', None)

        if min_height > height:
            self._height = height = min_height

        # if max_width > 0 and (max_width < width or width <= 0):
        #     print("~~~~~~~~~~~~ max_width:", max_width, '<', width)
        #     self._width = width = max_width

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
            self.rect.width = (width if width >= 0 else size[0]) - (0 if node.drawer.check_parent_flex() else 2*margin)
            self.rect.height = height
        else:
            self.rect.width = width if width >= 0 else size[0]
            self.rect.height = height

        if self.max_width > 0 and self.rect.width > self.max_width:
            self.rect.width = self.max_width

        if not self.calced:
            self.calced = True


class DrawerBlock(DrawerNode):

    def __init__(self, node) -> None:
        super().__init__(node)
        self.ability = None
        self.calced = Calced()

    def check_parent_flex(self):
        parent = getattr(self.node.parent, 'drawer', None)
        if parent:
            parent_calced = getattr(parent, 'calced', None)
            if parent_calced and getattr(parent_calced, 'display', None) == 'flex':
                return parent

    def calc_size(self, size, pos, debug=False):

        self.calced.calc_params(self.node, size, debug=debug)

        tag = self.node.tag.text if self.node.tag else None
        
        pos_my = (pos[0] + self.calced.margin, pos[1] + self.calced.margin)
        size_my = (self.calced.rect.width, self.calced.rect.height)
   
        self.pos = pos_my
        self.size_my = size_my

        size_calced = self.calc_children(pos_my, size_my)

        parent = self.check_parent_flex()
        if parent:
            align_items = parent.calced.align_items
            if align_items == 'center':
                self.pos = (self.pos[0], parent.pos[1] + parent.size_my[1]/2 - size_calced[1]/2)
        
        self.size_calced = size_calced if size_calced != None else size_my

        # if tag == 'image':
        #     print('(image)', self.node.level, self.pos, self.size_calced, 'size_my:', size_my, self.node.style, self.calced.rect.width, self.calced.rect.height)

        return size_my

    def calc_children(self, pos_my, size_my):

        _ps = (pos_my[0], pos_my[1])
        size_calced = (size_my[0], size_my[1])

        _size_calced = size_calced
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            
            drawer = node.drawer

            _size_my = drawer.calc_size(size_my, (_ps[0], _ps[1]))

            _ps, _size_calced = self.add_subnode_pos_size(node, _ps, _size_calced, self.calced.margin)

        parent_drawer = getattr(self.node.parent, 'drawer', None)
        if parent_drawer and getattr(parent_drawer.calced, 'display', None) == 'flex':
            size_calced = size_calced
        else:
            size_calced = _size_calced

        h = _ps[1] - pos_my[1]
        if h > size_calced[1]:
            size_calced = (size_calced[0], h)

        return size_calced

    def add_subnode_pos_size(self, node, pos_my, size_calced, margin, vertical=True):
        pos = [pos_my[0], pos_my[1]]
        drawer = node.drawer
        wh = drawer.size_calced
        mg = drawer.calced.margin
        if mg:
            mg_2 = mg*2
            if vertical:
                wh = (wh[0], wh[1]+mg_2)
            else:
                wh = (wh[0]+mg_2, wh[1])

        if vertical:
            static_i, change_i = 0, 1
        else:
            static_i, change_i = 1, 0
            
        if vertical:
            if wh[1] > size_calced[1]:
                size_calced = (size_calced[0], wh[1])

            if wh[0] > size_calced[0]:
                size_calced = (wh[0], size_calced[1])

            if pos[0] + wh[0] - pos_my[0] > size_calced[0]:
                size_calced = (pos[0] + wh[0] - pos_my[0], size_calced[1])

        else:
            if wh[0] > size_calced[0]:
                size_calced = (wh[0], size_calced[1])

            if wh[1] > size_calced[1]:
                size_calced = (size_calced[0], wh[1])

            if pos[1] + wh[1] - pos_my[1] > size_calced[1]:
                size_calced = (size_calced[0], pos[1] + wh[1] - pos_my[1])
        
        pos[change_i] += wh[change_i] #+ mg #margin

        return pos, size_calced

    def draw(self, cr):

        ps, size_calced = self.pos, self.size_calced

        background_color = self.calced.background_color
        border_radius = self.calced.border_radius
        color = self.calced.color
        font_size = self.calced.font_size
        border = self.calced.border
        image = getattr(self.calced, 'image', None)

        rect = (ps[0], ps[1], size_calced[0], size_calced[1])

        if background_color:
            self.draw_background(cr, background_color, rect, radius=border_radius)

        if image:
            self.draw_image(cr, image, rect)

        if border:
            self.draw_border(cr, rect, 'full', border[0], border[1], border[2], radius=border_radius)
        for nm in ('left', 'right', 'top', 'bottom'):
            bd = getattr(self.calced, 'border_'+nm, None)
            if bd:
                self.draw_border(cr, rect, nm, bd[0], bd[1], bd[2])

        if color:
            cr.set_source_rgb(*hex2color(color))
        else:
            cr.set_source_rgb(0.1, 0.1, 0.1)
        padding = self.calced.padding
        self.draw_lines(cr, self.node.lines, (ps[0]+padding, ps[1]+padding), font_size)

        if self.ability:
            self.ability.draw(cr, rect)

        tag = self.node.tag.text if self.node.tag else None
        if tag == 'listview':
            listview = self.node.attrs.get('data_model', None)
            if listview and listview.template:
                draw_listview(self, listview, cr)
                return
        
        for node in self.node.children:
            
            if not hasattr(node, 'drawer'):
                continue

            node.drawer.draw(cr)

    def draw_background(self, cr, background_color, rect, radius=None):
        rect = (rect[0], rect[1], rect[2]+1, rect[3]+1)
        cr.set_source_rgb(*hex2color(background_color))
        if radius:
            roundrect(cr, rect[0], rect[1], rect[2], rect[3], radius)
        else:
            cr.rectangle(*rect)
        cr.fill()

    def draw_border(self, cr, rect, nm, border_width, border_type, border_color, radius=None):
        cr.set_source_rgb(*hex2color(border_color))
        cr.set_line_width(border_width)
        if nm == 'full':
            rect = (rect[0]+0.5, rect[1]+0.5, rect[2]-1+1, rect[3]-1+1)
            if radius:
                roundrect(cr, rect[0], rect[1], rect[2], rect[3], radius)
            else:
                cr.rectangle(*rect)    
        else:
            if nm == 'left':
                x1, y1, x2, y2 = rect[0], rect[1], rect[0], rect[1]+rect[3]
            elif nm == 'right':
                x1, y1, x2, y2 = rect[0]+rect[2]+0.5, rect[1], rect[0]+rect[2]+0.5, rect[1]+rect[3]
            elif nm == 'top':
                x1, y1, x2, y2 = rect[0], rect[1]+0.5, rect[0]+rect[2], rect[1]+0.5
            elif nm == 'bottom':
                x1, y1, x2, y2 = rect[0], rect[1]+rect[3], rect[0]+rect[2], rect[1]+rect[3]
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
        cr.stroke()

    def draw_lines(self, cr, lines, pos, font_size):
        if not lines:
            return

        cr.set_font_size(font_size)
        x, y = pos
        x += 0.5
        
        for line in lines:
            cr.move_to(x, y + font_size) #+5
            cr.show_text(line)
            y += font_size

    def draw_image(self, cr, image, rect):
        r = (rect[0], rect[1], rect[2], rect[3])
        img_w, img_h = image.get_width(), image.get_height()
        wk, hk = (
            1 if self.calced._width < 0 else rect[2]/img_w, 
            1 if self.calced._height < 0 else rect[3]/img_h
        )
        boo = wk != 1 or hk != 1
        if boo:
            r = (rect[0]/wk, rect[1]/hk, rect[2]/wk, rect[3]/hk)
            cr.scale(wk, hk)
        cr.set_source_surface(image, r[0], r[1])
        cr.paint()
        if boo:
            cr.scale(1/wk, 1/hk)

    def draw_scroll(self, cr, _ps, _sz):
        scroll_width = 20
        background_color = '#eeeeee'
        rect = (_ps[0]+_sz[0]-scroll_width, _ps[1], scroll_width, _sz[1])
        cr.set_source_rgb(*hex2color(background_color))
        cr.rectangle(*rect)
        cr.fill()

        scroll_width_p2 = scroll_width / 2

        cr.set_source_rgb(*hex2color('#777777'))
        cr.move_to(rect[0]+scroll_width_p2, rect[1]+5)
        cr.line_to(rect[0]+scroll_width_p2-5, rect[1]+10)
        cr.line_to(rect[0]+scroll_width_p2+5, rect[1]+10)
        cr.line_to(rect[0]+scroll_width_p2, rect[1]+5)
        cr.fill()

        bottom = _ps[1] + _sz[1]
        cr.move_to(rect[0]+scroll_width_p2, bottom-5)
        cr.line_to(rect[0]+scroll_width_p2-5, bottom-10)
        cr.line_to(rect[0]+scroll_width_p2+5, bottom-10)
        cr.line_to(rect[0]+scroll_width_p2, bottom-5)
        cr.fill()

        return (_sz[0]-scroll_width, _sz[1])

    def draw_scroll_pos(self, cr, _ps, _sz, scroll_pos, scroll_size):
        scroll_width = 20
        scroll_pan_height = 50
        
        min_y = _ps[1] + scroll_width
        max_y = _ps[1] + _sz[1] - scroll_width - scroll_pan_height

        y = min_y + scroll_pos
        if y > max_y:
            y = max_y
        if y < min_y:
            y = min_y

        rect = (_ps[0]+_sz[0], y, scroll_width, scroll_pan_height)
        cr.set_source_rgb(*hex2color('#cccccc'))
        cr.rectangle(*rect)
        cr.fill()

    def propagateEvent(self, pos, event_name):
        if not hasattr(self, 'pos'):
            return False
        if (
            self.pos[0] <= pos[0] < self.pos[0] + self.size_calced[0] and 
            self.pos[1] <= pos[1] < self.pos[1] + self.size_calced[1]
        ):
            if self.ability:
                if self.ability.propagateEvent(pos, event_name):
                    return True

            ev = self.node.attrs.get(event_name, None) if self.node.attrs else None
            if ev and ev():
                return True

            if self.node.tag and self.node.tag.text =='listview':
                listview = self.node.attrs['data_model']
                ret = listview.propagateEvent(pos, event_name)
                if ret:
                    return ret

            for ch in self.node.children:
                ret = _propagateEvent(ch, pos, event_name)
                if ret:
                    return ret

    def find_listview_by_pos(self, x, y):
        if self.node.tag and self.node.tag.text == 'listview':
            if (
                self.pos[0] <= x < self.pos[0] + self.size_calced[0] and
                self.pos[1] <= y < self.pos[1] + self.size_calced[1]
            ):
                return self
        
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            lv = node.drawer.find_listview_by_pos(x, y)
            if lv:
                return lv

        return None


def roundrect(context, x, y, width, height, r):
    context.new_sub_path()
    context.arc(x+r, y+r, r, math.pi, 3*math.pi/2)
    context.arc(x+width-r, y+r, r, 3*math.pi/2, 0)
    context.arc(x+width-r, y+height-r, r, 0, math.pi/2)
    context.arc(x+r, y+height-r, r, math.pi/2, math.pi)
    context.close_path()


class DrawerFlex(DrawerBlock):
    
    def calc_children(self, pos_my, size_my):
        flex_sum = 0
        static_sum = 0

        _ps = (pos_my[0], pos_my[1])
        size_calced = (size_my[0], size_my[1])

        self.flex_point = 0
        flex_vertical = self.calced.flex_direction == 'column'

        for node in self.node.children:
            if hasattr(node, 'drawer'):
                drawer = node.drawer
                drawer.calc_size(size_my, (_ps[0], _ps[1]))
                flex = drawer.calced.flex
                if flex:
                    flex_sum += flex
                else:
                    mg = drawer.calced.margin
                    static_sum += (drawer.calced.rect.height if flex_vertical else drawer.calced.rect.width) + mg*2

        self.flex_point = (size_my[1 if flex_vertical else 0]-static_sum) / flex_sum

        _size_calced = size_calced
        for node in self.node.children:
            if not hasattr(node, 'drawer'):
                continue
            
            drawer = node.drawer

            _size_my = drawer.calc_size(size_my, (_ps[0], _ps[1]))

            if hasattr(drawer, 'add_node_pos_size'):
                _ps, _size_calced = drawer.add_node_pos_size(_ps, _size_calced, self.flex_point, flex_vertical)
            else:
                _ps, _size_calced = self.add_subnode_pos_size(node, _ps, _size_calced, self.calced.margin, vertical=flex_vertical)

        return size_calced


class AbilityBase:

    def __init__(self, drawer) -> None:
        self.drawer = drawer
        drawer.ability = self

    def draw(self, cr, rect):
        pass

    def propagateEvent(self, pos, event_name):
        pass


class AbilityInput(AbilityBase):
    
    def __init__(self, drawer) -> None:
        super().__init__(drawer)
        self.cursor_visible = False

    def draw(self, cr, rect):
        if not self.cursor_visible:
            return
        padding = self.drawer.calced.padding
        cr.set_source_rgb(*hex2color('#000000'))
        cr.set_line_width(1)

        fascent, fdescent, fheight, fxadvance, fyadvance = cr.font_extents()
        print(fascent, fdescent, fheight, fxadvance, fyadvance)

        x0, y0 = rect[0]+padding, rect[1]+padding
        cursor_height = fheight #14 #20
        x1, y1, x2, y2 = x0, y0, x0, y0 + cursor_height

        lines = self.drawer.node.lines
        if lines:
            hi = len(lines)
            line = lines[-1]
            wi = len(line)

            hadd = (hi - 1) * (fheight*0.77)
            xoff, yoff, textWidth, textHeight = cr.text_extents(line)[:4]
            wadd = textWidth

            x1, y1, x2, y2 = x0+wadd, y0+hadd, x0+wadd, y0+hadd + cursor_height

        cr.move_to(x1+0.5, y1)
        cr.line_to(x2+0.5, y2)
        cr.stroke()

    def propagateEvent(self, pos, event_name):
        if event_name == 'onclick':
            print('@@@')
            INPUT_CONTROL.set_focus(self)
            return self

    def on_timer(self):
        self.toggle()

    def toggle(self):
        self.cursor_visible = not self.cursor_visible
        if INPUT_CONTROL.refresher:
            INPUT_CONTROL.refresher()

    def on_focus_got(self):
        self.cursor_visible = True

    def on_focus_lost(self):
        self.cursor_visible = False

    def addText(self, text):
        if not self.drawer.node.text:
            self.drawer.node.text = ""
        if text == None:
            self.drawer.node.text = self.drawer.node.text[:-1]
        else:
            self.drawer.node.text += text


class DrawerFlexItem(DrawerBlock):

    def calc_children(self, pos_my, size_my):
        try:
            flex_vertical = self.node.parent.drawer.calced.flex_direction == 'column'
        except:
            print('????', self.node.parent)
            raise

        if flex_vertical:
            size_my = (size_my[0], self.node.parent.drawer.flex_point * self.calced.flex)
        else:
            size_my = (self.node.parent.drawer.flex_point * self.calced.flex, size_my[1])

        size_calced = super().calc_children(pos_my, size_my)
        
        if flex_vertical:
            return (size_calced[0], self.node.parent.drawer.flex_point * self.calced.flex)
        else:
            return (self.node.parent.drawer.flex_point * self.calced.flex, size_calced[1])

    def add_node_pos_size(self, pos_my, size_calced, flex_point, flex_vertical):
        pos = (
            (pos_my[0], pos_my[1] + flex_point * self.calced.flex) 
            if flex_vertical else 
            (pos_my[0] + flex_point * self.calced.flex, pos_my[1])
        )
        wh = self.size_calced

        if flex_vertical:
            if wh[0] > size_calced[0]:
                size_calced = (wh[0], size_calced[1])
        else:
            if wh[1] > size_calced[1]:
                size_calced = (size_calced[0], wh[1])

        return pos, size_calced

             
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

