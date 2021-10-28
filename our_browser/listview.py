

class ListviewControl:

    def __init__(self, listview) -> None:
        print('-----!!!!!!!!!! ListviewControl:', listview.tag)
        self.listview = listview
        self.template = None
        listview.attrs['data_model'] = self

    def getItemsCount(self):
        return 15

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
