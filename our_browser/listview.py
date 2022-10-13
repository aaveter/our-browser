import wx
import cairo
import statistics

from our_browser.draw_commons import cr_set_source_rgb_any_hex, hex2color, PRIOR_EVENT_HANDLERS


class ItemBase:

    def __init__(self, text) -> None:
        self.text = text


class Scrollable:

    def __init__(self) -> None:
        self.scroll_pos = 0
        self.scroll_pos_y = 0
        self.scroll_started = False
        self.height = 0
        self.max_scroll_y = 0

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

    def draw_scroll_pos(self, cr, _ps, _sz, items_count, drawer):
        #scroll_area_height = items_count * self.mean_h

        #self.scroll_pos_y = scroll_area_height * self.scroll_pos / drawer.size_calced[1]

        scroll_width = 20
        # scroll_pan_height_d = (_sz[1] - scroll_size/2 - 50) if scroll_size <= _sz[1]*2 else (_sz[1] / scroll_size) #50
        # if scroll_pan_height_d < 5:
        #     scroll_pan_height_d = 10
        # scroll_pan_height = scroll_pan_height_d # _sz[1] - 
        self.scroll_pan_height = scroll_pan_height = 50
        
        min_y = _ps[1] + scroll_width
        max_y = _ps[1] + _sz[1] - scroll_width - scroll_pan_height

        y = min_y + self.scroll_pos
        if y > max_y:
            y = max_y
        if y < min_y:
            y = min_y

        rect = (_ps[0]+_sz[0], y, scroll_width, scroll_pan_height)
        cr.set_source_rgb(*hex2color('#cccccc'))
        cr.rectangle(*rect)
        cr.fill()

    def on_wheel(self, event):
        d = event.GetWheelRotation()/4
        self.append_scroll(d)

    def append_scroll(self, d):
        scroll_area_height = self.getItemsCount() * self.mean_h

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
        drawer = self.listview.drawer
        scroll_width = 20
        scroll_right = drawer.pos[0] + drawer.size_calced[0]
        scroll_left = scroll_right - scroll_width
        scroll_top = drawer.pos[1] + scroll_width
        scroll_bottom = drawer.pos[1] + drawer.size_calced[1] - scroll_width
        return scroll_left <= pos[0] < scroll_right and scroll_top <= pos[1] < scroll_bottom


class ListviewControl(Scrollable):

    def __init__(self, listview) -> None:
        super().__init__()
        self.listview = listview
        self.mean_h = 50
        self.template = None
        items_count = int(listview.attrs.get('items-count', 0))
        self.items = [ItemBase('item-{}'.format(i)) for i in range(items_count)]
        listview.attrs['data_model'] = self

    def getItemsCount(self):
        return len(self.items)

    def format_template(self, i, template, texts, item=None):
        if item == None:
            item = self.items[i] if i>=0 and i<len(self.items) else False
        #template.text = listview.format_template(t_drawer.text, i)
        #t_drawer = template.drawer
        text = texts['text']
        counter = str(i)

        if text:
            lst = text.split('{{')
            if len(lst) > 1:
                for i, part in enumerate(lst):
                    if i == 0:
                        continue
                    a, b = part.split('}}')
                    a = a.strip()
                    if a == 'counter':
                        a = counter
                    elif a.startswith('item.'):
                        a = getattr(item, a[5:], 'None')
                    lst[i] = a + b
                text = ''.join(lst)
        else:
            text = ''

        template.text = text #text.replace('{{ counter }}', counter) if text else text
        children_texts = texts['children']
        for j, ch_template in enumerate(template.children):
            ch_texts = children_texts[j]
            self.format_template(i, ch_template, ch_texts, item)
        


def connect_listview(node, listview_cls=ListviewControl):
    if not node:
        return
    for n in node.children:
        if n.tag:
            if n.tag.text == 'listview':
                listview_cls(n)
            elif n.tag.text == 'template':
                if node.tag and node.tag.text =='listview':
                    node.attrs['data_model'].template = n
        connect_listview(n)


def fill_template_texts(template, texts):
    texts['text'] = template.text
    children = texts['children'] = []
    for ch_template in template.children:
        child_texts = {}
        fill_template_texts(ch_template, child_texts)
        children.append(child_texts)


def draw_listview(drawer, listview, cr):
    _items_count = listview.getItemsCount()
    
    template = listview.template.children[0]
    t_drawer = template.drawer

    _ps = lv_pos = getattr(drawer, 'pos', (0, 0))
    _sz = getattr(drawer, 'size_calced', (0, 0))

    _sz = lv_size = listview.draw_scroll(cr, _ps, _sz)

    lv_top = lv_pos[1]
    lv_bottom = lv_pos[1] + lv_size[1]

    if not hasattr(listview, 'texts'):
        listview.texts = {}
        fill_template_texts(template, listview.texts)
    texts = listview.texts

    _ps = (_ps[0], _ps[1]-listview.scroll_pos_y)

    #t_drawer.calc_size(_sz, [_ps[0], _ps[1]]) - works into calc_size tree

    w, h = int(lv_pos[0] + lv_size[0] + 10), int(lv_pos[1] + lv_size[1] + 10)
    temp_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    temp_cr = cairo.Context(temp_surface)
    
    hh = []
    item_w = _sz[0]
    for i in range(_items_count):
        _sz = (item_w, _sz[1])

        bottom = _ps[1] + _sz[1]
        if bottom < lv_top:
            _ps, _sz = t_drawer.add_subnode_pos_size(template, _ps, _sz, margin=t_drawer.calced.margin)
            #hh.append(_sz[1])
            continue
        
        listview.format_template(i, template, texts)
        
        _sz = t_drawer.calc_size(_sz, (_ps[0], _ps[1]), debug=False)

        _ps, _sz = t_drawer.add_subnode_pos_size(template, _ps, _sz, margin=t_drawer.calced.margin)
        hh.append(_sz[1])

        t_drawer.draw(temp_cr)

        if _ps[1] > lv_bottom:
            break

    listview.mean_h = statistics.mean(hh) if len(hh) else listview.mean_h
    #print('[ mean_h ] {}'.format(listview.mean_h))

    cr.set_source_surface(temp_surface, 0, 0) #, lv_pos[0], lv_pos[1])
    cr.rectangle(lv_pos[0], lv_pos[1], lv_size[0], lv_size[1])
    cr.fill()

    listview.draw_scroll_pos(cr, lv_pos, lv_size, _items_count, drawer)

