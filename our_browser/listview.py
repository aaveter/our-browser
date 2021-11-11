

class ListviewControl:

    def __init__(self, listview) -> None:
        print('-----!!!!!!!!!! ListviewControl:', listview.tag)
        self.listview = listview
        self.template = None
        self.scroll_pos = 0
        listview.attrs['data_model'] = self

    def getItemsCount(self):
        return 10000

    def format_template(self, text, i):
        return text.replace('{{ counter }}', str(i))

    def on_wheel(self, event):
        d = event.GetWheelRotation()/4
        self.scroll_pos += d


def connect_listview(node, listview_cls=ListviewControl):
    if not node:
        return
    for n in node.children:
        if n.tag:
            if n.tag.text == 'listview':
                listview_cls(n)
            elif n.tag.text == 'template':
                if node.tag and node.tag.text =='listview':
                    print('-----!!!!!!!!!! template:', n.tag)
                    node.attrs['data_model'].template = n

        connect_listview(n)


def draw_listview(drawer, listview, cr):
    _items_count = listview.getItemsCount()
    
    template = listview.template.children[0]
    t_drawer = template.drawer
    scroll_pos = listview.scroll_pos

    _ps = lv_pos = getattr(drawer, 'pos', (0, 0))
    _sz = getattr(drawer, 'size_calced', (0, 0))

    _sz = lv_size = drawer.draw_scroll(cr, _ps, _sz)

    lv_bottom = lv_pos[1] + lv_size[1]
    
    if not hasattr(t_drawer, 'text'):
        t_drawer.text = template.text

    _ps = (_ps[0], _ps[1]+scroll_pos)

    #t_drawer.calc_size(_sz, [_ps[0], _ps[1]]) - works into calc_size tree
    
    for i in range(_items_count):
        if _ps[1] < lv_pos[1]:
            _ps, _sz = t_drawer.add_subnode_pos_size(template, _ps, _sz, margin=t_drawer.calced.margin)
            continue
        
        template.text = listview.format_template(t_drawer.text, i)
        
        _sz = t_drawer.calc_size(_sz, (_ps[0], _ps[1]))

        bottom = _ps[1] + _sz[1]
        
        if bottom > lv_bottom:
            break

        _ps, _sz = t_drawer.add_subnode_pos_size(template, _ps, _sz, margin=t_drawer.calced.margin)
        t_drawer.draw(cr)
        