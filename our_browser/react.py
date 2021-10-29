
from .ext_depends import noder_parse_text


class _ReactDOM:

    def __init__(self) -> None:
        self.react_classes = {}
        self._methods_tmp = []

    def render(self, html, node):
        d = self.react_classes = {}

        for cls in _ReactComponent.get_subclasses():
            print('***', cls, cls.__name__)
            d[cls.__name__] = cls

        root = noder_parse_text(html).children[0]
        print('ROOT:', root, root.attrs)

        root = self._find_and_render(root, node)
        print('>>', root)

        self._set_node(node, root)

    def _find_and_render(self, root, node=None):
        if node == None:
            node = root
        else:
            self._set_node_attrs(node, root)

        for cls_name in self.react_classes:
            if root.tag and root.tag.text == cls_name:
                root = self._render_node(node, self.react_classes[cls_name])
                return root

        for n in root.children:
            self._find_and_render(n)

        return root

    def _render_node(self, root, cls):
        print('[ _render_node ]', cls)
        component = cls(root.attrs)
        component.connect(root)
        component._render(first_start=True)
        return root

    def _connect_methods(self, node, _methods):
        if node.attrs:
            for a, v in node.attrs.items():
                if type(v)==str and v.startswith('METHOD-'):
                    pos = int(v[7:])
                    print('COOOOOOOOONNECT method:', pos, id(_methods[pos]))
                    node.attrs[a] = _methods[pos]
        for ch in node.children:
            self._connect_methods(ch, _methods)

    def _set_node(self, dst, src):
        self._set_node_attrs(dst, src)
        dst.set_node(src)

    def _set_node_attrs(self, dst, src):
        if dst.attrs:
            if src.attrs:
                dst.attrs.update(src.attrs)
        else:
            dst.attrs = src.attrs


class _ReactComponent:

    def connect(self, node) -> None:
        self.node = node
        node.react_component = self
    
    @classmethod
    def get_subclasses(cls):
        return cls.__subclasses__()

    def setState(self, d):
        self.state.update(d)
        self._render()
        # print('CLEAR ({}):'.format(id(self.node)), self.node)
        # self.node.children.clear()
        # print('CLEARED:', self.node)

    def _render(self, first_start=False):
        ReactDOM._methods_tmp.clear()
        txt = self.render()
        print('GOT txt:', txt)
        _methods, ReactDOM._methods_tmp = ReactDOM._methods_tmp, []
        src_node = noder_parse_text(txt).children[0]
        ReactDOM._set_node(self.node, src_node)
        ReactDOM._connect_methods(self.node, _methods)
        if not first_start:
            self.node.app.update_drawers()
            self.node.app._connect_styles(self.node)


class React:

    Component = _ReactComponent


def EVENT(method):
    print('[ METHOD ] {} = {}'.format(method, id(method)))
    ln = len(ReactDOM._methods_tmp)
    ReactDOM._methods_tmp.append(method)
    return 'METHOD-{}'.format(ln)


ReactDOM = _ReactDOM()
