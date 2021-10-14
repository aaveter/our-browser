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
        #print("OnSize" +str(event))
        #self.SetClientRect(event.GetRect()) # no need
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

        # cr.set_source_rgb (0.5, 0.5, 0.5)
        # cr.set_line_width(1)
        # cr.move_to(ps[0], ps[1])
        # cr.line_to(ps[0]+sz[0], ps[1])
        # cr.line_to(ps[0]+sz[0], ps[1]+sz[1])
        # cr.fill()

        #print('[size]', size)

        #dc.DrawRectangle(10, 10, )

        ROOT.calc_size(size, (0, 0))
        ROOT.draw(cr)
        # w1 = size[0] / 4
        
        # cr.set_source_rgb (0.2 , 0.23 , 0.9)
        # cr.rectangle(w1/4, 15, w1, 60)
        # cr.fill()
        
        # cr.set_source_rgb(0.9 , 0.1 , 0.1)
        # cr.rectangle(2*w1/4 + w1, 15, w1, 60)
        # cr.fill()
        
        # cr.set_source_rgb(0.4 , 0.9 , 0.4)
        # cr.rectangle(2*w1/4 + 2*w1, 15, w1, 60)       
        # cr.fill()     

        # draw_context(cr)


# def draw_context(context):
#     x, y, x1, y1 = 0.1, 0.5, 0.4, 0.9
#     x2, y2, x3, y3 = 0.6, 0.1, 0.9, 0.5
#     context.scale(200, 200)
#     context.set_line_width(0.04)
#     context.move_to(x, y)
#     context.curve_to(x1, y1, x2, y2, x3, y3)
#     context.stroke()
#     context.set_source_rgba(1, 0.2, 0.2, 0.6)
#     context.set_line_width(0.02)
#     context.move_to(x, y)
#     context.line_to(x1, y1)
#     context.move_to(x2, y2)
#     context.line_to(x3, y3)
#     context.stroke()


class Frame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(Frame, self).__init__(*args, **kwargs) 
        
        self.InitUI()

    def InitUI(self):

        self.SetIcon(wx.Icon("our_browser.ico"))

        #----------------------------------------------------
        # Build menu bar and submenus   
        
        # menubar = wx.MenuBar()
        # # file menu containing quit menu item
        # fileMenu = wx.Menu() 
        # quit_item = wx.MenuItem(fileMenu, wx.ID_EXIT, '&Quit\tCtrl+W')
        # fileMenu.Append(quit_item)
        # self.Bind(wx.EVT_MENU, self.OnQuit, quit_item)
        # menubar.Append(fileMenu, '&File')      

        # # help menu containing about menu item
        # helpMenu = wx.Menu() 
        # about_item = wx.MenuItem(helpMenu, wx.ID_ABOUT, '&About\tCtrl+A')
        # helpMenu.Append(about_item)
        # #~ self.Bind(wx.EVT_MENU, self.OnAboutBox, about_item)
        # menubar.Append(helpMenu, '&Help')     

        # self.SetMenuBar(menubar)

        #----------------------------------------------------
        # Build window layout

        panel = wx.Panel(self)        
        vbox = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vbox)        

        midPan = DrawingArea(panel)
        vbox.Add(midPan, 1, wx.EXPAND | wx.ALL, 0)
    

        # smallPan = wx.Panel(panel)
        # hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        # vbox.Add(smallPan, 1, wx.EXPAND|wx.ALL, 12)
        # smallPan.SetSizer(hbox2)   

        # #----------------------------------------------------
        # # Place buttons in correct box corresponding with panel

        # close_button = wx.Button(smallPan, wx.ID_CLOSE)
        # self.Bind(wx.EVT_BUTTON, self.OnQuit, close_button)

        # hbox2.Add(close_button)
        
        #----------------------------------------------------
        # Set window properties

        #~ self.SetSize((1600, 1200))
        self.SetSize((800, 600))
        #~ self.Maximize()
        self.SetTitle('Our Browser')
        self.Centre()

    # def OnQuit(self, e):
    #     self.Close()

def main():
    ex = wx.App()
    f = Frame(None)
    f.Show(True)  
    ex.MainLoop()  

if __name__ == '__main__':
    main()