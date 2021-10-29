
from .ext_depends import noder_parse_text


class _ReactDOM:

    def __init__(self) -> None:
        self.react_classes = {}

    def render(self, html, node):
        d = self.react_classes = {}

        for cls in _ReactComponent.get_subclasses():
            print('***', cls, cls.__name__)
            d[cls.__name__] = cls

        root = noder_parse_text(html).children[0]
        print('ROOT:', root)

        root = self._find_and_render(root)
        print('>>', root)

        self._set_node(node, root)

    def _find_and_render(self, root):
        for cls_name in self.react_classes:
            if root.tag and root.tag.text == cls_name:
                root = self._render_node(root, self.react_classes[cls_name])
                return root

        for n in root.children:
            self._find_and_render(n)

        return root

    def _render_node(self, root, cls):
        print('[ _render_node ]', cls)
        component = cls(root.attrs)
        component.connect(root)
        node = noder_parse_text(component.render()).children[0]
        # if node.attrs:
        #     node.attrs.update(root.attrs)
        # else:
        #     node.attrs = root.attrs
        # root.set_node(node)
        self._set_node(root, node)
        return root

    def _set_node(self, dst, src):
        if src.attrs:
            src.attrs.update(dst.attrs)
        else:
            src.attrs = dst.attrs
        dst.set_node(src)


class _ReactComponent:

    def connect(self, node) -> None:
        self.node = node
        node.react_component = self
    
    @classmethod
    def get_subclasses(cls):
        return cls.__subclasses__()


class React:

    Component = _ReactComponent


def EVENT(method):
    print('[ METHOD ] {}'.format(method))
    return 'METHOD'


ReactDOM = _ReactDOM()
