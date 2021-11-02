

class ListviewControl:

    def __init__(self, listview) -> None:
        print('-----!!!!!!!!!! ListviewControl:', listview.tag)
        self.listview = listview
        self.template = None
        listview.attrs['data_model'] = self

    def getItemsCount(self):
        return 55

    def format_template(self, text, i):
        return text.replace('{{ counter }}', str(i))


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
    _ps, _sz = getattr(drawer, 'pos', (0, 0)), getattr(drawer, 'size_calced', (0, 0))
    t_drawer = template.drawer
    if not hasattr(t_drawer, 'text'):
        t_drawer.text = template.text
    for i in range(_items_count):
        print('PRINT listview', i, _sz, _ps)
        _sz = t_drawer.calc_size(_sz, [_ps[0], _ps[1]])
        print('  ->', t_drawer.size_calced, t_drawer.pos)
        template.text = listview.format_template(t_drawer.text, i)
        _ps, _sz = t_drawer.add_subnode_pos_size(template, _ps, _sz, margin=t_drawer.calced.margin)
        t_drawer.draw(cr)
        