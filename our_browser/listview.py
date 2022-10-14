import wx
import cairo
import statistics

#from our_browser.draw_commons import cr_set_source_rgb_any_hex, hex2color, PRIOR_EVENT_HANDLERS
from our_browser.draw_commons import Scrollable


class ItemBase:

    def __init__(self, text) -> None:
        self.text = text


class ListviewControl(Scrollable):

    def __init__(self, listview) -> None:
        super().__init__()
        self.listview = listview
        self.mean_h = 50
        self.template = None
        items_count = int(listview.attrs.get('items-count', 0))
        self.items = [self.generateItem(i) for i in range(items_count)]
        listview.attrs['data_model'] = self

    @property
    def items_count(self):
        return self.getItemsCount()

    @items_count.setter
    def items_count(self, val):
        ln = len(self.items)
        d = val - ln
        if d > 0:
            self.items += [self.generateItem(i) for i in range(ln, ln+d)]
        elif d < 0:
            self.items = self.items[:d]

    def getItemsCount(self):
        return len(self.items)

    def generateItem(self, i):
        return ItemBase('item-{}'.format(i))

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

    def getDrawer(self):
        return self.listview.drawer        


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
    try:
        _items_count = listview.getItemsCount()
        
        template = listview.template.children[0]
        t_drawer = template.drawer

        scroll_area_height = listview.calc_scroll_area_height()

        _ps = lv_pos = getattr(drawer, 'pos', (0, 0))
        _sz = lv_size = getattr(drawer, 'size_calced', (0, 0))

        need_scroll = scroll_area_height > _sz[1]
        if need_scroll:
            _sz = lv_size = listview.draw_scroll(cr, _ps, _sz)

        lv_top = lv_pos[1]
        lv_bottom = lv_pos[1] + lv_size[1]

        if not hasattr(listview, 'texts'):
            listview.texts = {}
            fill_template_texts(template, listview.texts)
        texts = listview.texts

        _ps = _ps0 = (_ps[0], _ps[1]-listview.scroll_pos_y)

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
            
            _sz = t_drawer.calc_size(_sz, (_ps[0], _ps[1]), _ps0)

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

        if need_scroll:
            listview.draw_scroll_pos(cr, lv_pos, lv_size, _items_count, drawer)
    except Exception as e:
        print(e)


