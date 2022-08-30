

class Styler:

    def __init__(self) -> None:
        self.styles = {}

    def add_by_text(self, text):
        pos = 0
        while True:
            i = text.find('{', pos)
            if i < 0:
                break
            j = text.find('}', i)
            if j < 0:
                break

            names = text[pos:i].strip()
            inside = text[i+1:j].strip()

            _style = self.parse_style(inside)

            for name in names.split(','):
                name = name.strip()
                if name not in self.styles:
                    self.styles[name] = {}
                name_d = self.styles[name]
                name_d.update(_style)

                print('''    {} -> {}'''.format(name, _style))

            pos = j+1

    def parse_style(self, text):
        _style = {}
        
        lst = text.split(';')
        for a in lst:
            if ':' not in a:
                continue
            ll = a.split(':')
            key, value = ll[0].strip(), ll[1].strip()
            if key in ('width', 'height', 'min-height', 'max-height', 'min-width', 'max-width', 'margin', 'padding', 'border-radius'):
                if value.endswith('%'):
                    value = (int(value[:-1]), '%')
                else:
                    if value.endswith('px'):
                        value = value[:-2]
                    value = str2int(value)

            elif key in ('border', 'border-right', 'border-left', 'border-top', 'border-bottom'):
                _lst = value.split(' ')
                if len(_lst) != 3:
                    value = None
                else: 
                    if _lst[0].endswith('px'):
                        _lst[0] = _lst[0][:-2]
                    if _lst[0].isnumeric():
                        value = (int(_lst[0]), _lst[1], _lst[2])
                    else:
                        print('!!!', _lst)
                        value = None

            elif key == 'flex':
                value = str2int(value)

            _style[key] = value

        return _style

    def connect_styles_to_node(self, node):
        tag = node.tag.text if node.tag else None
        classes = node.attrs.get('classList', None) if node.attrs else None
        if classes:
            print('>>> classes', classes)

        style = {}
        if tag:
            if tag == 'h1':
                style['font-size'] = 32
            elif tag == 'h2':
                style['font-size'] = 24

        names = ([tag] if tag else []) + ([('.' + _cl) for _cl in classes] if classes else [])
        for n in names:
            _style = self.styles.get(n, None)
            if _style:
                style.update(_style)

        node.style = style
        if style:
            print(':::', node, style)


def str2int(value):
    if value.isnumeric():
        return int(value)
    else:
        print('!!!', value)
        return 0
