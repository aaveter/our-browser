#
import wx
from wx.core import SB_VERTICAL
import wx.lib.wxcairo
import cairo
from os.path import abspath, join, dirname
import sys

from our_browser.ext_depends import noder_parse_file, noder_parse_text, DATA_PATH
from our_browser.drawing import make_drawable_tree
from our_browser.listview import ListviewControl, connect_listview


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
        self.ROOT.propagateEvent(event.Position, 'ondown')

    def onClick(self, event):
        self.ROOT.propagateEvent(event.Position, 'onclick')
        self.Refresh()

    def onMoving(self, event):
        if self.ROOT.propagateEvent(event.Position, 'onmoving'):
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

        self.ROOT_NODE = ROOT_NODE = noder_parse_file(html_path) if html_path else noder_parse_text(html_text)
        connect_listview(ROOT_NODE, listview_cls=listview_cls)

        self.app = wx.App()
        self.frame = Frame(None)

    def update_drawers(self):
        self.frame.mainPanel.ROOT = make_drawable_tree(self.ROOT_NODE)

    def run(self):
        self.update_drawers()
        self._connect_styles(self.ROOT_NODE)
        self.frame.Show(True)
        self.app.MainLoop()

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