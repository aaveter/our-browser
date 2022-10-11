#
import wx
from wx.core import SB_VERTICAL
import wx.lib.wxcairo
import cairo
from os.path import abspath, join, dirname
import sys

from our_browser.ext_depends import noder_parse_file, noder_parse_text, DATA_PATH
from our_browser.drawing import make_drawable_tree, INPUT_CONTROL, _propagateEvent
from our_browser.listview import ListviewControl, connect_listview
from our_browser.os_help import fix_key_by_mode


def main(listview_cls=ListviewControl, html_path=None):
    if html_path == None:
        html_path = sys.argv[1].replace('\\', '/')
    
    app = BrowserApp(listview_cls=listview_cls, html_path=html_path)
    app.run()


class BrowserApp:

    def __init__(self, html_path=None, html_text='', listview_cls=ListviewControl) -> None:

        self.listview_cls = listview_cls
        self.ROOT_NODE = noder_parse_file(html_path) if html_path else noder_parse_text(html_text)

        self.app = wx.App()
        self.frame = Frame(None)

    def update_drawers(self):
        self.frame.mainPanel.ROOT = make_drawable_tree(self.ROOT_NODE)
        self.frame.mainPanel.ROOT.ROOT_NODE = self.ROOT_NODE

    def run(self):
        connect_listview(self.ROOT_NODE, listview_cls=self.listview_cls)

        self.update_drawers()
        self._connect_styles(self.ROOT_NODE)

        INPUT_CONTROL.set_refresher(self.frame.mainPanel.Refresh)

        self.frame.Show(True)
        self.app.MainLoop()

        INPUT_CONTROL.stop_timer()

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
        
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        #self.Bind(wx.EVT_CHAR, self.onKeyChar)
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyChar)

        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        #self.SetFocus()
    
    def OnSize(self, event):
        self.Refresh() # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip() # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window
        
    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        self.DoDrawing(cr, dc)
        
    def DoDrawing(self, cr, dc):
        size = self.GetSize()

        cr.set_source_rgb (1.0, 1.0, 1.0)
        cr.rectangle(0, 0, size[0], size[1])
        cr.fill()

        self.calc(size)

        self.ROOT.draw(cr)

    def calc(self, size):
        self.ROOT.calc_size(size, (0, self.scroll_pos))

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
        listview = self.ROOT.find_listview_by_pos(mposx, mposy)
        if listview:
            listview.node.attrs['data_model'].on_wheel(event)
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
        _propagateEvent(self.ROOT.node, event.Position, 'ondown')

    def onClick(self, event):
        if not _propagateEvent(self.ROOT.node, event.Position, 'onclick'):
            INPUT_CONTROL.set_focus(None)
        self.Refresh()

    def onMoving(self, event):
        if _propagateEvent(self.ROOT.node, event.Position, 'onmoving'):
            self.Refresh()

    def onKeyDown(self, event):
        self.onKey(event, 'down')

    def onKeyUp(self, event):
        self.onKey(event, 'up')

    def onKeyChar(self, event):
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
        if cursor_way:
            self.onKey(event, 'down')
        event.Skip()
    
    def onKey(self, event, name):
        keycode = event.GetUnicodeKey()
        keycode2 = event.GetKeyCode()
        
        if keycode != wx.WXK_NONE:

            if keycode == wx.WXK_RETURN: #13:
                print('-- enter --')
                if name == 'up':
                    self.addText('\n')

            elif keycode == wx.WXK_BACK: #8:
                print('-- backspace --')
                if name == 'down':
                    self.addText(None) # for remove

            elif keycode == wx.WXK_TAB:
                if name == 'down':
                    print('-- tab --')

            elif keycode == wx.WXK_DELETE:
                if name == 'down':
                    print('-- delete --')

            else:
                has_shift = event.ShiftDown()
                keycode3 = event.GetRawKeyCode()

                ch = chr(keycode)
                ch = fix_key_by_mode(ch, has_shift)

                print(name, "You pressed: ", keycode, ch, keycode3, chr(keycode3), 'has_shift:', has_shift)
                if name == 'down':
                    self.addText(ch)

        else:
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
            else:
                print('-- no key --')
                if keycode2 == wx.WXK_F1:
                    pass

            if cursor_way and name == 'down':
                print('-- curwor_way: {} -- ({})'.format(cursor_way, name))
                ability = INPUT_CONTROL.focus_into
                if ability:
                    if ability.moveCursor(cursor_way):
                        self.Refresh()

        event.Skip()

    def addText(self, text):
        ability = INPUT_CONTROL.focus_into
        if ability:
            ability.addText(text)
            way = 'left' if text == None else 'right'
            ability.moveCursor(way)
            self.Refresh()

    def OnRightDown(self, e):
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.onPopup, id=self.popupID1)
        self._popupMenu = PopMenu(self, self.popupID1)
        self.PopupMenu(self._popupMenu, e.GetPosition())

    def onPopup(self, event):
        itemId = event.GetId()
        menu = event.GetEventObject()
        menuItem = menu.FindItemById(itemId)
        txt = menuItem.GetItemLabel()
        if txt.lower() == 'show dev':
            self.mainFrame.dev.ROOT_NODE = self.ROOT.ROOT_NODE if self.ROOT else None
            self.mainFrame.dev.Show()
            self.mainFrame.vbox.Layout()
        elif txt.lower() == 'hide dev':
            self.mainFrame.dev.Hide()
            self.mainFrame.vbox.Layout()


class PopMenu(wx.Menu): 
  
    def __init__(self, parent, menuId):
        super(PopMenu, self).__init__()
  
        self.parent = parent
  
        popmenu = wx.MenuItem(self, menuId, 'Hide dev' if parent.mainFrame.dev.IsShown() else 'Show dev')
        self.Append(popmenu)


from our_browser.drawing import cr_set_source_rgb_any_hex

class DevTreeArea(wx.Panel):
    
    def __init__ (self , *args , **kw):
        super(DevTreeArea, self).__init__ (*args , **kw)

        self.ROOT_NODE = None
        
        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
    def OnSize(self, event):
        self.Refresh() # MUST have this, else the rectangle gets rendered corruptly when resizing the window!
        event.Skip() # seems to reduce the ammount of OnSize and OnPaint events generated when resizing the window
        
    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        # self.DoDrawing(cr, dc)

        if self.ROOT_NODE:
            self.draw_node(cr, self.ROOT_NODE, line_y=0, level=0)

    def draw_node(self, cr, node, line_y, level):
        h = 11
        rect = (10 + level*5, 10 + line_y*(h+2), 100, h)
        cr_set_source_rgb_any_hex(cr, '#333333')
        cr.set_line_width(1)
        rect = (rect[0]+0.5, rect[1]+0.5, rect[2]-1+1, rect[3]-1+1)
        cr.rectangle(*rect)
        cr.stroke()

        font_size = 9
        cr.set_font_size(font_size)
        x, y = (rect[0]+5, rect[1])
        x += 0.5
        if node.tag:
            cr.move_to(x, y + font_size)
            text = node.tag.text
            drawer = getattr(node, 'drawer', None)
            if drawer:
                text += ': {}'.format(drawer.__class__.__name__[6:])
            cr.show_text(text)

        line_y += 1
        for ch in node.children:
            line_y = self.draw_node(cr, ch, line_y, level+1)

        return line_y


if __name__ == '__main__':
    main()
