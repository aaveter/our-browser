
from our_browser.ext_depends import noder_parse_text
from our_browser.drawing import make_drawable_tree


class _ReactDOM:

    def __init__(self) -> None:
        self.react_classes = {}
        self._methods_tmp = []

    def render(self, html, dst_node):
        d = self.react_classes = {}

        for cls in _ReactComponent.get_subclasses():
            d[cls.__name__] = cls
            for cls2 in cls.get_subclasses():
                d[cls2.__name__] = cls2

        root_0 = noder_parse_text(html)
        root_src = root_0.children[0]

        root_src = self._find_and_render(root_src, dst_node, main_render=True, attrs_smart_update=True)

        #self._set_node(dst_node, root_src, attrs_smart_update=True)

    def _find_and_render(self, root, dst_node=None, main_render=False, attrs_smart_update=False):
        if dst_node == None:
            dst_node = root
        else:
            self._set_node_attrs(dst_node, root)

        for cls_name in self.react_classes:
            if root.tag and root.tag.text == cls_name:
                root = self._render_node(dst_node, self.react_classes[cls_name], attrs_smart_update=attrs_smart_update)
                root.app = dst_node.app if dst_node else root.app
                if main_render:
                    break

        for n in root.children:
            n.app = root.app
            n.parent = dst_node
            self._find_and_render(n)

        if main_render:
            return root

    def _render_node(self, root, cls, attrs_smart_update=False):
        component = cls(root.attrs)
        component.connect(root)
        component._render(#first_start=True,
            attrs_smart_update=attrs_smart_update)
        #self._find_and_render(root)
        return root

    def _connect_methods(self, node, _methods):
        if node.attrs:
            for a, v in node.attrs.items():
                if type(v)==str and v.startswith('METHOD-'):
                    pos = int(v[7:])
                    node.attrs[a] = _methods[pos]
        for ch in node.children:
            self._connect_methods(ch, _methods)

    def _set_node(self, dst, src, attrs_smart_update=False):
        self._set_node_attrs(dst, src, attrs_smart_update=attrs_smart_update)
        dst.set_node(src, attrs_smart_update=attrs_smart_update)

    def _set_node_attrs(self, dst, src, attrs_smart_update=False):
        if dst.attrs != None and src.attrs != None and attrs_smart_update:
            dst.attrs.update(src.attrs)
        else:
            dst.attrs = src.attrs


class _ReactComponent:

    def __init__(self, props=None) -> None:
        self.props = props
        self.item = None

    def connect(self, node) -> None:
        self.node = node
        node.react_component = self

    @classmethod
    def get_subclasses(cls):
        return cls.__subclasses__()

    def setState(self, d):
        self.state.update(d)
        self._render()

    def _render(self, first_start=False, attrs_smart_update=False):
        ReactDOM._methods_tmp.clear()
        txt = self.render()
        _methods, ReactDOM._methods_tmp = ReactDOM._methods_tmp, []
        src_node = noder_parse_text(txt).children[0]
        for ch in src_node.children:
            ch.app = self.node.app
            ReactDOM._find_and_render(ch)
        ReactDOM._set_node(self.node, src_node, attrs_smart_update=attrs_smart_update)
        ReactDOM._connect_methods(self.node, _methods)
        if not first_start:
            self.node.app._connect_styles(self.node)
            #self.node.app.update_drawers()
            make_drawable_tree(self.node)

    def render(self):
        pass


class React:

    Component = _ReactComponent


def EVENT(method):
    ln = len(ReactDOM._methods_tmp)
    ReactDOM._methods_tmp.append(method)
    return 'METHOD-{}'.format(ln)


ReactDOM = _ReactDOM()
