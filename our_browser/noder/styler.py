

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

            pos = j+1

    def parse_style(self, text):
        _style = {}

        lst = text.split(';')
        for a in lst:
            if ':' not in a:
                continue
            ll = a.split(':')
            key, value = ll[0].strip(), ll[1].strip()
            if key in ('width', 'height', 'min-height', 'max-height', 'min-width', 'max-width', 'margin', 'padding', 'border-radius', 'top', 'left'):
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
                        value = None

            elif key == 'flex':
                value = str2int(value)

            _style[key] = value

        return _style

    def connect_styles_to_node(self, node):
        tag = node.tag.text if node.tag else None
        classes = node.attrs.get('classList', None) if node.attrs else None

        style = {}
        if tag:
            if tag == 'h1':
                style['font-size'] = 32
            elif tag == 'h2':
                style['font-size'] = 24

        names = ([tag] if tag else []) + ([('.' + _cl) for _cl in classes] if classes else [])

        for j, add in enumerate((None, 'hover')):
            style_cur, style_name = ({}, add) if add else (style, 'simple')
            for n in names:
                nn = (n + ':' + add) if add else n
                _style = self.styles.get(nn, None)
                # if n.startswith('.width-'):
                #     print('!!!')
                if _style != None:
                    style_cur.update(_style)
                elif j==0 and nn.startswith('.'):
                    _style = try_style(nn[1:])
                    if _style:
                        style_cur.update(_style)

            setattr(node, 'style_'+style_name, style_cur)


_SMART_NUM_CLASSES = {
    'width-': 'width',
    'w-': 'width',
    'w': 'width',
    'height-': 'height',
    'h-': 'height',
    'h': 'height',
    'flex-': 'flex',
    'top-': 'top',
    'left-': 'left',
    'margin-': 'margin',
    'padding-': 'padding',
}

def try_style(name):
    # _is_debug = False #name.startswith('width-')
    # if _is_debug:
    #     print('TRY:', name)
    if len(name) == 0:
        return None
    #n = name[0]
    c = None
    for n in _SMART_NUM_CLASSES:
        if name.startswith(n):
            c = n
            break
    if c != None:
        part = name[len(c):]
        if len(part) > 0:
            _add = ''
            if part[-1] == 'p':
                part = part[:-1]
                _add = '%'
            if part.isnumeric():
                part = int(part)
                if _add:
                    part = (part, _add)
                ret = {_SMART_NUM_CLASSES[c]: part}
                return ret
    return None


def str2int(value):
    if value.isnumeric():
        return int(value)
    else:
        return 0
