#
import wx
from wx.core import SB_VERTICAL
import wx.lib.wxcairo
#import cairo
from os.path import abspath, join, dirname
#import sys
from inspect import ismethod
from datetime import datetime

from our_browser.ext_depends import noder_parse_file, noder_parse_text, DATA_PATH
from our_browser.drawing import make_drawable_tree, INPUT_CONTROL, _propagateEvent, Calced, SELECT_CONTROL
from our_browser.draw_commons import PRIOR_EVENT_HANDLERS, Scrollable
from our_browser.listview import ListviewControl, connect_listview
#from our_browser.os_help import fix_key_by_mode


def main(listview_cls=ListviewControl, html_path=None):
    # if html_path == None:
    #     html_path = sys.argv[1].replace('\\', '/')

    app = BrowserApp(listview_cls=listview_cls, html_path=html_path)
    app.run()


class _ObjectHandler:

    def __init__(self) -> None:
        self._object = None

    def set_object(self, document):
        self._object = document

    def __getattr__(self, name):
        return getattr(self._object, name)


app = _ObjectHandler()
document = _ObjectHandler()


class BrowserApp:

    def __init__(self, html_path=None, html_text='', listview_cls=ListviewControl) -> None:

        self.listview_cls = listview_cls
        self.ROOT_NODE = noder_parse_file(html_path) if html_path else noder_parse_text(html_text)

        self.app = wx.App()
        self.frame = Frame(None)
        self.mainPanel = self.frame.mainPanel

        app.set_object(self)
        document.set_object(self.ROOT_NODE)

    def update_drawers(self):
        self.frame.mainPanel.ROOT = make_drawable_tree(self.ROOT_NODE)
        self.frame.mainPanel.ROOT.ROOT_NODE = self.ROOT_NODE

    def run(self, with_prepare=True, onCloseCallback=None):
        if with_prepare:
            self.prepare_run()

        INPUT_CONTROL.set_refresher(self.frame.mainPanel.Refresh)
        INPUT_CONTROL.set_text_syncer(self.frame.mainPanel.text_syncer)

        self.frame.Show(True)
        self.app.MainLoop()

        INPUT_CONTROL.stop_timer()

        if onCloseCallback:
            onCloseCallback()

    def prepare_run(self):
        connect_listview(self.ROOT_NODE, listview_cls=self.listview_cls)

        self.update_drawers()
        self._connect_styles(self.ROOT_NODE)

    def _connect_styles(self, node):
        styler = self.ROOT_NODE.styler
        styler.connect_styles_to_node(node)
        for n in node.children:
            self._connect_styles(n)


class Frame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Frame, self).__init__(*args, **kwargs)

        self.InitUI()

    def InitUI(self):
        self.SetIcon(wx.Icon(join(DATA_PATH, "our_browser.ico")))

        panel = wx.Panel(self)
        self.vbox = vbox = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(vbox)

        self.mainPanel = mainPanel = DrawingArea(panel)
        mainPanel.mainFrame = self
        mainPanel.vbox = vbox
        vbox.Add(mainPanel, 1, wx.EXPAND | wx.ALL, 0)

        mainPanel.scroll = scroll = wx.ScrollBar(panel, style=SB_VERTICAL)
        scroll.Hide()
        scroll.SetScrollbar(position=0, thumbSize=16, range=1000, pageSize=100)
        vbox.Add(scroll, 0, wx.EXPAND | wx.ALL, 0)

        self.dev = dev = DevTreeArea(panel)
        dev.mainPanel = mainPanel
        dev.Hide()
        dev.SetSize((100, 600))
        vbox.Add(dev, 1, wx.EXPAND | wx.ALL, 0)

        self.SetSize((800, 600))
        self.SetTitle('Our Browser')
        self.Centre()

        scroll.Bind(wx.EVT_SCROLL, mainPanel.onScrollWin1)
        self.Bind(wx.EVT_MOUSEWHEEL, mainPanel.onWheelWin)

class DrawingArea(wx.Panel):

    def __init__ (self , *args , **kw):
        super(DrawingArea, self).__init__ (*args , **kw)

        self.input = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.input.SetPosition([-100, -100])
        #self.input.Hide() # FIXME some steps to good work with text

        self.scroll_pos = 0
        self.scroll_show = False
        self.scroll = None
        self.vbox = None
        self.mainFrame = None

        self.ROOT = None

        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.onDown)
        self.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.Bind(wx.EVT_MOTION, self.onMoving)
        self.Bind(wx.EVT_LEFT_DCLICK, self.onDbClick)

        """self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        #self.Bind(wx.EVT_CHAR, self.onKeyChar)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyChar)"""

        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        #self.SetFocus()
        self.dts = tuple()

        self.input.Bind(wx.EVT_TEXT, self.onTextChanged)
        self.input.Bind(wx.EVT_KEY_DOWN, self.onInputKeyDown)

    def onTextChanged(self, e):
        e.Skip()
        new_pos = self.input.GetInsertionPoint()
        #print(":::", e.String, "new_pos:", new_pos)
        self.setText(e.String, new_pos)

    def text_syncer(self, text):
        self.input.SetValue(text)

    def changeCursor(self, name):
        if name == 'wait':
            newCursor = wx.Cursor(wx.CURSOR_WAIT)
        elif name == 'pointer':
            newCursor = wx.Cursor(wx.CURSOR_HAND)
        elif name == 'progress':
            newCursor = wx.Cursor(wx.CURSOR_ARROWWAIT)
        elif name == 'crosshair':
            newCursor = wx.Cursor(wx.CURSOR_CROSS)
        elif name == 'ew-resize':
            newCursor = wx.Cursor(wx.CURSOR_SIZEWE)
        else:
            newCursor = wx.Cursor(wx.CURSOR_ARROW)
        self.SetCursor(newCursor)

    def OnSize(self, event):
        self.Refresh() # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip() # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window

    def OnPaint(self, e):
        SELECT_CONTROL._selected_lines[:] = []
        dc = wx.PaintDC(self)
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        self.DoDrawing(cr, dc)

    def DoDrawing(self, cr, dc):
        size = self.GetSize()

        cr.set_source_rgb (1.0, 1.0, 1.0)
        cr.rectangle(0, 0, size[0], size[1])
        cr.fill()

        start = datetime.now()
        self.calc(size)
        tm1 = datetime.now()
        dt1 = (tm1 - start).total_seconds()
        self.ROOT.draw(cr)
        tm2 = datetime.now()
        dt2 = (tm2 - tm1).total_seconds()
        self.ROOT.draw(cr, absolutes=True)
        tm3 = datetime.now()
        dt3 = (tm3 - tm2).total_seconds()
        self.dts = (dt1, dt2, dt3)

        if self.mainFrame.dev.IsShown():
            self.mainFrame.dev.Refresh()

    def calc(self, size):
        self.ROOT.calc_size(size, (0, self.scroll_pos), (0, self.scroll_pos))

        if self.ROOT.size_calced[1] > size[1]:
            position = self.scroll.ThumbPosition
            pageSize = size[1]
            _range = self.ROOT.size_calced[1] - pageSize
            thumbSize = _range / pageSize
            self.scroll.SetScrollbar(position=position, thumbSize=thumbSize, range=_range, pageSize=pageSize)
            if not self.scroll_show:
                self.scroll_show = True
                self.scroll.Show()
                self.vbox.Layout()
        else:
            if self.scroll_show:
                self.scroll_pos = 0
                self.scroll.ThumbPosition = 0
                self.scroll_show = False
                self.scroll.Hide()
                self.vbox.Layout()

    def onScrollWin1(self, event):
        self.scroll_pos = -event.Position
        self.Refresh()

    def onWheelWin(self, event):
        mposx, mposy = wx.GetMousePosition()
        mposx, mposy = self.ScreenToClient(mposx, mposy)
        #listview = self.ROOT.find_listview_by_pos(mposx, mposy)
        scrollable = self.ROOT.find_node_by_pos_and_tags(mposx, mposy, ('listview', 'input',))
        if scrollable:
            if scrollable.node.tag.text == 'listview':
                scrollable.node.attrs['data_model'].on_wheel(event)
            else:
                scrollable.ability.on_wheel(event)
            self.Refresh()
            return
        if not self.scroll_show:
            return
        d = -event.GetWheelRotation()/4
        self.scroll_pos -= d
        if self.scroll_pos > 0:
            self.scroll_pos = 0
        max_pos = self.scroll.GetRange()
        if self.scroll_pos < -max_pos:
            self.scroll_pos = -max_pos
        self.scroll.ThumbPosition = -self.scroll_pos
        self.Refresh()

    def onDown(self, event):
        SELECT_CONTROL.started = False
        SELECT_CONTROL.listview = None
        SELECT_CONTROL.start = event.Position
        print('[ onDown ]', len(PRIOR_EVENT_HANDLERS))
        SELECT_CONTROL.started = True
        for pr in PRIOR_EVENT_HANDLERS:
            if hasattr(pr, 'doEventPrior'):
                if pr.doEventPrior(event.Position, 'ondown'):
                    return
            elif hasattr(pr, 'propagateEvent'):
                if pr.propagateEvent(event.Position, 'ondown'):
                    return
        if _propagateEvent(self.ROOT.node, event.Position, 'ondown'):
            return
        if SELECT_CONTROL.started:
            SELECT_CONTROL.end = event.Position
        #SELECT_CONTROL.started = True

    def onDbClick(self, event):
        SELECT_CONTROL._double_clicked = True

    def onClick(self, event):
        if SELECT_CONTROL.started:
            SELECT_CONTROL.started = False
            SELECT_CONTROL.end = event.Position
        handled = False
        print('[ onClick ]', len(PRIOR_EVENT_HANDLERS), "DBL:", SELECT_CONTROL._double_clicked)
        for pr in PRIOR_EVENT_HANDLERS:
            if hasattr(pr, 'doEventPrior'):
                handled = pr.doEventPrior(event.Position, 'onclick')
                if handled:
                    break
            elif hasattr(pr, 'propagateEvent'):
                handled = pr.propagateEvent(event.Position, 'onclick')
                if handled:
                    break
        if not handled and not _propagateEvent(self.ROOT.node, event.Position, 'onclick'):
            INPUT_CONTROL.set_focus(None)
        self.Refresh()
        #SELECT_CONTROL._double_clicked = False

    def onMoving(self, event):
        handled = False
        for pr in PRIOR_EVENT_HANDLERS:
            if hasattr(pr, 'doEventPrior'):
                handled = pr.doEventPrior(event.Position, 'onmoving')
                if handled:
                    break
            elif hasattr(pr, 'propagateEvent'):
                handled = pr.propagateEvent(event.Position, 'onmoving')
                if handled:
                    break
        if handled:
            print('handled onMoving...')
        if not handled and _propagateEvent(self.ROOT.node, event.Position, 'onmoving'):
            handled = True
        if SELECT_CONTROL.started:
            SELECT_CONTROL.end = event.Position
        if not handled:
            if SELECT_CONTROL.started:
                SELECT_CONTROL.end = event.Position
                handled = True
        if handled:
            self.Refresh()
        SELECT_CONTROL._double_clicked = False

    def onInputKeyDown(self, event):
        keycode2 = event.GetKeyCode()
        cursor_way = None
        if keycode2 == wx.WXK_LEFT:
            cursor_way = 'left'
        elif keycode2 == wx.WXK_RIGHT:
            cursor_way = 'right'
        elif keycode2 == wx.WXK_UP:
            cursor_way = 'up'
        elif keycode2 == wx.WXK_DOWN:
            cursor_way = 'down'
        elif keycode2 == wx.WXK_HOME:
            cursor_way = 'home'
        elif keycode2 == wx.WXK_END:
            cursor_way = 'end'
        if cursor_way:
            print('..way:', cursor_way)
            ability = INPUT_CONTROL.focus_into
            if ability:
                if ability.moveCursor(cursor_way):
                    self.Refresh()

        event.Skip()

    # def onKeyDown(self, event):
    #     self.onKey(event, 'down')

    # def onKeyUp(self, event):
    #     self.onKey(event, 'up')

    # def onKeyChar(self, event):
    #     keycode2 = event.GetKeyCode()
    #     cursor_way = None
    #     if keycode2 == wx.WXK_LEFT:
    #         cursor_way = 'left'
    #     elif keycode2 == wx.WXK_RIGHT:
    #         cursor_way = 'right'
    #     elif keycode2 == wx.WXK_UP:
    #         cursor_way = 'up'
    #     elif keycode2 == wx.WXK_DOWN:
    #         cursor_way = 'down'
    #     if cursor_way:
    #         self.onKey(event, 'down')
    #     event.Skip()

    # def onKey(self, event, name):
    #     keycode = event.GetUnicodeKey()
    #     keycode2 = event.GetKeyCode()

    #     if keycode != wx.WXK_NONE:

    #         if keycode == wx.WXK_RETURN: #13:
    #             print('-- enter --')
    #             if name == 'up':
    #                 self.addText('\n')

    #         elif keycode == wx.WXK_BACK: #8:
    #             print('-- backspace --')
    #             if name == 'down':
    #                 self.addText(None) # for remove

    #         elif keycode == wx.WXK_TAB:
    #             if name == 'down':
    #                 print('-- tab --')

    #         elif keycode == wx.WXK_DELETE:
    #             if name == 'down':
    #                 print('-- delete --')

    #         else:
    #             has_shift = event.ShiftDown()
    #             keycode3 = event.GetRawKeyCode()

    #             ch = chr(keycode)
    #             ch = fix_key_by_mode(ch, has_shift)

    #             print(name, "You pressed: ", keycode, ch, keycode3, chr(keycode3), 'has_shift:', has_shift)
    #             if name == 'down':
    #                 self.addText(ch)

    #     else:
    #         cursor_way = None
    #         if keycode2 == wx.WXK_LEFT:
    #             cursor_way = 'left'
    #         elif keycode2 == wx.WXK_RIGHT:
    #             cursor_way = 'right'
    #         elif keycode2 == wx.WXK_UP:
    #             cursor_way = 'up'
    #         elif keycode2 == wx.WXK_DOWN:
    #             cursor_way = 'down'
    #         elif keycode2 == wx.WXK_HOME:
    #             cursor_way = 'home'
    #         elif keycode2 == wx.WXK_END:
    #             cursor_way = 'end'
    #         else:
    #             print('-- no key --')
    #             if keycode2 == wx.WXK_F1:
    #                 pass

    #         if cursor_way and name == 'down':
    #             print('-- curwor_way: {} -- ({})'.format(cursor_way, name))
    #             ability = INPUT_CONTROL.focus_into
    #             if ability:
    #                 if ability.moveCursor(cursor_way):
    #                     self.Refresh()

    #     event.Skip()

    def setText(self, text, new_pos=None):
        ability = INPUT_CONTROL.focus_into
        if ability:
            ability.setText(text)
            if new_pos != None:
                ability.moveCursor(new_pos)
            self.Refresh()

    def addText(self, text):
        ability = INPUT_CONTROL.focus_into
        if ability:
            ability.addText(text)
            way = 'left' if text == None else 'right'
            ability.moveCursor(way)
            self.Refresh()

    def OnRightDown(self, e):
        if not hasattr(self, "popupID1"):
            self.popupID0 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.popupID0)
            self.popupID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.popupID1)
            self.popupID2 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.popupID2)
        self._popupMenu = PopMenu(self, self.popupID0, self.popupID1, self.popupID2)
        self._popupMenuPos = e.GetPosition()
        self.PopupMenu(self._popupMenu, e.GetPosition())

    def onPopup(self, event):
        itemId = event.GetId()
        menu = event.GetEventObject()
        menuItem = menu.FindItemById(itemId)
        txt = menuItem.GetItemLabel()
        if itemId == self.popupID0:
            if txt.lower() == 'copy':
                self._do_copy()
        elif itemId == self.popupID1:
            if txt.lower() == 'show dev':
                self._show_dev()
            elif txt.lower() == 'hide dev':
                self.mainFrame.dev.Hide()
                self.mainFrame.vbox.Layout()
        elif itemId == self.popupID2:
            is_shown = self.mainFrame.dev.IsShown()
            if not is_shown:
                self._show_dev()
            _nodes = self.ROOT.find_nodes_in_pos(*self._popupMenuPos)
            class _e:
                Position = self._popupMenuPos
                WasShownBefore = is_shown
                Drawer = _nodes[-1] if len(_nodes) > 0 else None
            self.mainFrame.dev.onClick(_e)

    def _do_copy(self):
        lines = []
        cur_li = None
        for li in SELECT_CONTROL._selected_lines:
            if getattr(li, '_breaked', False):
                if cur_li != None:
                    cur_li = cur_li + " " + li
                else:
                    cur_li = li
            else:
                if cur_li != None:
                    li = cur_li + " " + li
                    cur_li = None
                lines.append(li)
                
        print('COPY:', '\n'.join(lines))

    def _show_dev(self):
        self.mainFrame.dev.ROOT_NODE = self.ROOT.ROOT_NODE if self.ROOT else None
        self.mainFrame.dev.Show()
        self.mainFrame.vbox.Layout()


class PopMenu(wx.Menu):

    def __init__(self, parent, menuId0, menuId, menuId2):
        super(PopMenu, self).__init__()

        self.parent = parent

        popmenu = wx.MenuItem(self, menuId0, 'Copy')
        self.Append(popmenu)
        popmenu = wx.MenuItem(self, menuId, 'Hide dev' if parent.mainFrame.dev.IsShown() else 'Show dev')
        self.Append(popmenu)
        popmenu = wx.MenuItem(self, menuId2, 'Show dev on element')
        self.Append(popmenu)


from our_browser.drawing import cr_set_source_rgb_any_hex

class DevTreeArea(wx.Panel, Scrollable):

    def __init__ (self , *args , **kw):
        super(DevTreeArea, self).__init__ (*args , **kw)
        Scrollable.__init__(self)

        self.mainPanel = None
        self.ROOT_NODE = None
        self.current_y = -1

        self.pos = (0, 0)
        self.mean_h = 15

        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.Bind(wx.EVT_LEFT_DOWN, self.onDown)
        self.Bind(wx.EVT_LEFT_UP, self.onClick)
        self.Bind(wx.EVT_MOTION, self.onMoving)
        self.Bind(wx.EVT_MOUSEWHEEL, self.onWheelWin)

    @property
    def ROOT(self):
        return self.mainPanel.ROOT

    @property
    def size_calced(self):
        return self.GetSize()

    def OnSize(self, event):
        self.Refresh() # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip() # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window

    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        # self.DoDrawing(cr, dc)

        scroll_area_height = self.calc_scroll_area_height()

        _ps = lv_pos = getattr(self, 'pos', (0, 0))
        _sz = lv_size = getattr(self, 'size_calced', (0, 0))

        need_scroll = scroll_area_height > _sz[1]
        if need_scroll:
            _sz = lv_size = self.draw_scroll(cr, _ps, _sz)

        if self.ROOT_NODE:
            self.draw_node(cr, self.ROOT_NODE, line_y=0, level=0)

        if need_scroll:
            self.draw_scroll_pos(cr, lv_pos, lv_size)

    def draw_node(self, cr, node, line_y, level):
        h = 11
        rect = (10 + level*5, 10 + line_y*(h+2) - self.scroll_pos_y, 100, h)
        if line_y==self.current_y:
            self.current_y = node
        cr_set_source_rgb_any_hex(cr, '#333399' if self.current_y==node else '#333333')
        cr.set_line_width(1)
        rect = (rect[0]+0.5, rect[1]+0.5, rect[2]-1+1, rect[3]-1+1)
        cr.rectangle(*rect)
        cr.stroke()

        font_size = 9
        cr.set_font_size(font_size)
        x, y = (rect[0]+5, rect[1])
        x += 0.5
        text = ''
        if node.tag:
            cr.move_to(x, y + font_size)
            text = node.tag.text
            drawer = getattr(node, 'drawer', None)
            if drawer:
                text += ': {}'.format(drawer.__class__.__name__[6:])
            for nm in ('id', 'id2',):
                _attrs = getattr(node, 'attrs', None)
                if _attrs:
                    _id = _attrs.get(nm, None)
                    if _id != None:
                        text += ' {}={}'.format(nm, _id)

        _drawer = getattr(node, 'drawer', None)
        if self.ROOT and _drawer == self.ROOT:
            text = '[ ROOT ] ' + text
        cr.show_text(text)

        x, y = 250, 10
        for dt in self.mainPanel.dts:
            cr.move_to(x, y + font_size)
            text = "{}".format(dt)
            cr.show_text(text)
            y += font_size

        if self.current_y==node:
            for add in ('simple', 'hover'):
                _style = getattr(node, 'style_'+add, None)
                if _style:
                    for a, v in _style.items():
                        cr.move_to(x, y + font_size)
                        text = "{}: {}".format(a, v)
                        cr.show_text(text)
                        y += font_size
                cr.rectangle(250, y, 100, 1)
                cr.stroke()

            cr_set_source_rgb_any_hex(cr, '#339933')

            _found_font_size = 0
            drawer = getattr(node, 'drawer', None)
            if drawer:
                for a in dir(drawer.calced):
                    if a.startswith('_'):
                        continue
                    cr.move_to(x, y + font_size)
                    v = getattr(drawer.calced, a)
                    if a == 'font_size':
                        _found_font_size = v
                    if not ismethod(v):
                        text = "{}: {}".format(a, v)
                        cr.show_text(text)
                        y += font_size

                cr.rectangle(250, y, 100, 1)
                cr.stroke()
                cr_set_source_rgb_any_hex(cr, '#999933')

                for a in ('pos', 'size_my', 'size_calced',):
                    cr.move_to(x, y + font_size)
                    v = getattr(drawer, a, None)
                    text = "{}: {}".format(a, v)
                    cr.show_text(text)
                    y += font_size

                cr.rectangle(250, y, 100, 1)
                cr.stroke()


            attrs = getattr(node, 'attrs', None)
            if attrs != None:
                cr_set_source_rgb_any_hex(cr, '#cc9933')

                for a in attrs:
                    cr.move_to(x, y + font_size)
                    v = attrs[a]
                    text = "{}: {}".format(a, v)
                    cr.show_text(text)
                    y += font_size

            lines = getattr(node, 'lines', None)
            if lines != None:
                cr.rectangle(250, y, 100, 1)
                cr.stroke()
                cr_set_source_rgb_any_hex(cr, '#cc9977')

                for li in lines:
                    cr.move_to(x, y + font_size)
                    ln = len(li)
                    text_w = Calced.calc_font_size_w(_found_font_size) * ln
                    text = "{} ({} / {})".format(li, ln, text_w)
                    cr.show_text(text)
                    y += font_size

            cr.rectangle(250, y, 100, 1)
            cr.stroke()
            cr_set_source_rgb_any_hex(cr, '#cccc33')

            lst = [('node', node)]
            if drawer:
                lst.append(('drawer', drawer))
                calced = getattr(drawer, 'calced', None)
                if calced:
                    lst.append(('calced', calced))
                    rect = getattr(calced, 'rect', None)
                    if rect:
                        lst.append(('rect', rect))

            for nm, o in lst:
                cr.move_to(x, y + font_size)
                text = "{}: {}".format(nm, id(o))
                cr.show_text(text)
                y += font_size

        line_y += 1
        for ch in node.children:
            line_y = self.draw_node(cr, ch, line_y, level+1)

        return line_y

    def onDown(self, event):
        self.doEvent(event.Position, 'ondown')

    def onClick(self, event):
        drawer = getattr(event, "Drawer", None)
        if drawer:
            print('::: drawer:', drawer)
            self.current_y = drawer.node
        else:
            handled = self.doEventPrior(event.Position, 'onclick') if self in PRIOR_EVENT_HANDLERS else False
            if not handled:
                self.current_y = int((event.Position[1] + self.scroll_pos_y - 10) / 13)
        self.Refresh()

    def onMoving(self, event):
        handled = self.doEventPrior(event.Position, 'onmoving') if self in PRIOR_EVENT_HANDLERS else False
        if handled:
            self.Refresh()

    def onWheelWin(self, event):
        self.on_wheel(event)
        self.Refresh()

    def getDrawer(self):
        return self

    def getItemsCount(self):
        count = 0
        if self.ROOT_NODE:
            count += self._calc_count(self.ROOT_NODE)
        return count

    def _calc_count(self, node):
        count = 1
        for ch in node.children:
            count += self._calc_count(ch)
        return count


if __name__ == '__main__':
    main()
