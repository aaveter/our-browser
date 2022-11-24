
class PriorEventHandlers(list):
    pass

PRIOR_EVENT_HANDLERS = PriorEventHandlers()

class HoveredNodes(set):
    pass

HOVERED_NODES = HoveredNodes()


def cr_set_source_rgb_any_hex_or_simple(cr, color, simple):
    if color:
        cr_set_source_rgb_any_hex(cr, color)
    else:
        cr.set_source_rgb(*simple)

def cr_set_source_rgb_any_hex(cr, color):
    col = hex2color(color)
    if len(col) == 3:
        cr.set_source_rgb(*col)
    else:
        cr.set_source_rgba(*col)

def hex2color(color_hex):
    color_hex = color_hex.split('#')[1]
    if len(color_hex) >= 8:
        return (int(color_hex[:2], 16)/255.0, int(color_hex[2:4], 16)/255.0, int(color_hex[4:6], 16)/255.0,
            int(color_hex[6:8], 16)/255.0)
    else:
        return (int(color_hex[:2], 16)/255.0, int(color_hex[2:4], 16)/255.0, int(color_hex[4:6], 16)/255.0)


class Scrollable:

    def __init__(self) -> None:
        self.scroll_pos = 0
        self.scroll_pos_y = 0
        self.scroll_started = False
        self.height = 0
        self.max_scroll_y = 0
        self.scroll_pan_height = 50

    def draw_scroll(self, cr, _ps, _sz):
        scroll_width = 20
        background_color = '#eeeeee'
        self.height = height = _sz[1]
        area_width = _sz[0]-scroll_width
        x, y = _ps[0]+area_width, _ps[1]
        rect = (x, y, scroll_width, height)
        cr_set_source_rgb_any_hex(cr, background_color)
        cr.rectangle(*rect)
        cr.fill()

        scroll_width_p2 = scroll_width / 2

        cr.set_source_rgb(*hex2color('#777777'))
        cr.move_to(x+scroll_width_p2, y+5)
        cr.line_to(x+scroll_width_p2-5, y+10)
        cr.line_to(x+scroll_width_p2+5, y+10)
        cr.line_to(x+scroll_width_p2, y+5)
        cr.fill()

        bottom = y + height
        cr.move_to(x+scroll_width_p2, bottom-5)
        cr.line_to(x+scroll_width_p2-5, bottom-10)
        cr.line_to(x+scroll_width_p2+5, bottom-10)
        cr.line_to(x+scroll_width_p2, bottom-5)
        cr.fill()

        return (area_width, height)

    def draw_scroll_pos(self, cr, _ps, _sz):
        #scroll_area_height = items_count * self.mean_h

        #self.scroll_pos_y = scroll_area_height * self.scroll_pos / drawer.size_calced[1]

        scroll_width = 20
        # scroll_pan_height_d = (_sz[1] - scroll_size/2 - 50) if scroll_size <= _sz[1]*2 else (_sz[1] / scroll_size) #50
        # if scroll_pan_height_d < 5:
        #     scroll_pan_height_d = 10
        # scroll_pan_height = scroll_pan_height_d # _sz[1] - 
        
        min_y = _ps[1] + scroll_width
        max_y = _ps[1] + _sz[1] - scroll_width - self.scroll_pan_height

        y = min_y + self.scroll_pos
        if y > max_y:
            y = max_y
        if y < min_y:
            y = min_y

        rect = (_ps[0]+_sz[0], y, scroll_width, self.scroll_pan_height)
        cr.set_source_rgb(*hex2color('#cccccc'))
        cr.rectangle(*rect)
        cr.fill()

    def calc_scroll_area_height(self):
        return self.getItemsCount() * self.mean_h

    def on_wheel(self, event):
        d = event.GetWheelRotation()/4
        self.append_scroll(d)

    def append_scroll(self, d):
        drawer = self.getDrawer()
        _, self.height = getattr(drawer, 'size_calced', (0, 0))
        scroll_area_height = self.calc_scroll_area_height()

        scroll_height = self.height - 40 - self.scroll_pan_height

        dy = d * scroll_area_height / self.height
        
        scroll_pos_y = self.scroll_pos_y
        scroll_pos_y -= dy
        self.scroll_pos_y = int(scroll_pos_y)

        max_scroll_y = scroll_area_height - self.height
        if max_scroll_y < 0:
            max_scroll_y = 0
        self.max_scroll_y = max_scroll_y

        if self.scroll_pos_y > max_scroll_y:
            self.scroll_pos_y = max_scroll_y

        if self.scroll_pos_y < 0:
            self.scroll_pos_y = 0

        max_scroll_pos = scroll_height
        if max_scroll_pos < 0:
            max_scroll_pos = 0

        if max_scroll_y > 0:
            self.scroll_pos = self.scroll_pos_y * scroll_height / max_scroll_y
        else:
            self.scroll_pos = 0

        #self.scroll_pos -= ds
        if self.scroll_pos > max_scroll_pos:
            self.scroll_pos = max_scroll_pos
        if self.scroll_pos < 0:
            self.scroll_pos = 0

    def doEvent(self, pos, event_name):
        if event_name == 'ondown':
            if self.isIntoScroll(pos):
                self.scroll_started = pos
                PRIOR_EVENT_HANDLERS.insert(0, self)
                SELECT_CONTROL.started = False
                #SELECT_CONTROL.start = None

    def doEventPrior(self, pos, event_name):
        if event_name == 'onclick':
            self.scroll_started = False
            PRIOR_EVENT_HANDLERS.remove(self)
            return True
        elif event_name == 'onmoving':
            if self.scroll_started:
                d = (self.scroll_started[1] - pos[1]) #* 3
                self.scroll_started = pos
                self.append_scroll(d)
                return True

    def doEventOut(self, pos, event_name):
        pass #self.scroll_started = False

    def isIntoScroll(self, pos):
        drawer = self.getDrawer() #self.listview.drawer
        scroll_width = 20
        scroll_right = drawer.pos[0] + drawer.size_calced[0]
        scroll_left = scroll_right - scroll_width
        scroll_top = drawer.pos[1] + scroll_width
        scroll_bottom = drawer.pos[1] + drawer.size_calced[1] - scroll_width
        return scroll_left <= pos[0] < scroll_right and scroll_top <= pos[1] < scroll_bottom

    def getDrawer(self):
        return None


class SelectControl:

    def __init__(self) -> None:
        self.started = False
        self.start = None
        self.end = None
        self.listview = None

SELECT_CONTROL = SelectControl()
