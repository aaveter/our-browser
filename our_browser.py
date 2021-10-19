#
import wx
import wx.lib.wxcairo
import cairo

from drawing import ROOT


class DrawingArea(wx.Panel):
    
    def __init__ (self , *args , **kw):
        super(DrawingArea , self).__init__ (*args , **kw)
        
        self.SetDoubleBuffered(True)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
    
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

        ROOT.calc_size(size, (0, 0))
        ROOT.draw(cr)


class Frame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Frame, self).__init__(*args, **kwargs) 
        
        self.InitUI()

    def InitUI(self):
        self.SetIcon(wx.Icon("our_browser.ico"))

        panel = wx.Panel(self)        
        vbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vbox)        

        midPan = DrawingArea(panel)
        vbox.Add(midPan, 1, wx.EXPAND | wx.ALL, 0)

        self.SetSize((800, 600))
        self.SetTitle('Our Browser')
        self.Centre()


def main():
    ex = wx.App()
    f = Frame(None)
    f.Show(True)  
    ex.MainLoop()  


if __name__ == '__main__':
    main()