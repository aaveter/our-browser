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
from our_browser.os_help import check_capslock, get_keyboard_language


NUMS = '1234567890'
NUMS_SIGNS = '!@#$%^&*()'
NUMS_SIGNS_RU = '!"№;%:?*()'
SPECIALS = NUMS + '`-=[];\'\\,./'
SPECIALS_SIGNS = NUMS_SIGNS + '~_+{}:"|<>?'
SPECIALS_SIGNS_RU = NUMS_SIGNS_RU + 'Ё_+ХЪЖЭ/БЮ,'


class DrawingArea(wx.Panel):
    
    def __init__ (self , *args , **kw):
        super(DrawingArea , self).__init__ (*args , **kw)

        self.scroll_pos = 0
        self.scroll_show = False
        self.scroll = None
        self.vbox = None

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
                _upper = check_capslock()
                if has_shift:
                    _upper = not _upper
                if not _upper:
                    ch = ch.lower()

                if get_keyboard_language().lower() == 'russian':
                    ch = ch.translate(layout)
                    if has_shift and ch in SPECIALS:
                        ind = SPECIALS.index(ch)
                        ch = SPECIALS_SIGNS_RU[ind]
                else:
                    if has_shift and ch in SPECIALS:
                        ind = SPECIALS.index(ch)
                        ch = SPECIALS_SIGNS[ind]

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
        mainPanel.vbox = vbox
        vbox.Add(mainPanel, 1, wx.EXPAND | wx.ALL, 0)

        mainPanel.scroll = scroll = wx.ScrollBar(panel, style=SB_VERTICAL)
        scroll.Hide()
        scroll.SetScrollbar(position=0, thumbSize=16, range=1000, pageSize=100)
        vbox.Add(scroll, 0, wx.EXPAND | wx.ALL, 0)

        self.SetSize((800, 600))
        self.SetTitle('Our Browser')
        self.Centre()

        scroll.Bind(wx.EVT_SCROLL, mainPanel.onScrollWin1)
        self.Bind(wx.EVT_MOUSEWHEEL, mainPanel.onWheelWin)


class BrowserApp:

    def __init__(self, html_path=None, html_text='', listview_cls=ListviewControl) -> None:

        self.listview_cls = listview_cls
        self.ROOT_NODE = noder_parse_file(html_path) if html_path else noder_parse_text(html_text)

        self.app = wx.App()
        self.frame = Frame(None)

    def update_drawers(self):
        self.frame.mainPanel.ROOT = make_drawable_tree(self.ROOT_NODE)

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


def main(listview_cls=ListviewControl, html_path=None):
    if html_path == None:
        html_path = sys.argv[1].replace('\\', '/')
    
    app = BrowserApp(listview_cls=listview_cls, html_path=html_path)
    app.run()


if __name__ == '__main__':
    main()