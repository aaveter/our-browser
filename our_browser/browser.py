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


import win32api, win32con


def check_capslock():
    caps_status = win32api.GetKeyState(win32con.VK_CAPITAL)
    return caps_status != 0


# import keyboard

# def callback(event):
#     print('---', event, event.name, event.scan_code)

# keyboard.on_press(callback, suppress=False)


import ctypes
user32 = ctypes.WinDLL('user32', use_last_error=True)


def get_keyboard_language():
    """
    Gets the keyboard language in use by the current
    active window process.
    """

    languages = {'0x436' : "Afrikaans - South Africa", '0x041c' : "Albanian - Albania", '0x045e' : "Amharic - Ethiopia", '0x401' : "Arabic - Saudi Arabia",
                 '0x1401' : "Arabic - Algeria", '0x3c01' : "Arabic - Bahrain", '0x0c01' : "Arabic - Egypt", '0x801' : "Arabic - Iraq", '0x2c01' : "Arabic - Jordan",
                 '0x3401' : "Arabic - Kuwait", '0x3001' : "Arabic - Lebanon", '0x1001' : "Arabic - Libya", '0x1801' : "Arabic - Morocco", '0x2001' : "Arabic - Oman",
                 '0x4001' : "Arabic - Qatar", '0x2801' : "Arabic - Syria", '0x1c01' : "Arabic - Tunisia", '0x3801' : "Arabic - U.A.E.", '0x2401' : "Arabic - Yemen",
                 '0x042b' : "Armenian - Armenia", '0x044d' : "Assamese", '0x082c' : "Azeri (Cyrillic)", '0x042c' : "Azeri (Latin)", '0x042d' : "Basque",
                 '0x423' : "Belarusian", '0x445' : "Bengali (India)", '0x845' : "Bengali (Bangladesh)", '0x141A' : "Bosnian (Bosnia/Herzegovina)", '0x402' : "Bulgarian",
                 '0x455' : "Burmese", '0x403' : "Catalan", '0x045c' : "Cherokee - United States", '0x804' : "Chinese - People's Republic of China", 
                 '0x1004' : "Chinese - Singapore", '0x404' : "Chinese - Taiwan", '0x0c04' : "Chinese - Hong Kong SAR", '0x1404' : "Chinese - Macao SAR", '0x041a' : "Croatian",
                 '0x101a' : "Croatian (Bosnia/Herzegovina)", '0x405' : "Czech", '0x406' : "Danish", '0x465' : "Divehi", '0x413' : "Dutch - Netherlands", '0x813' : "Dutch - Belgium",
                 '0x466' : "Edo", '0x409' : "English - United States", '0x809' : "English - United Kingdom", '0x0c09' : "English - Australia", '0x2809' : "English - Belize",
                 '0x1009' : "English - Canada", '0x2409' : "English - Caribbean", '0x3c09' : "English - Hong Kong SAR", '0x4009' : "English - India", '0x3809' : "English - Indonesia",
                 '0x1809' : "English - Ireland", '0x2009' : "English - Jamaica", '0x4409' : "English - Malaysia", '0x1409' : "English - New Zealand", '0x3409' : "English - Philippines",
                 '0x4809' : "English - Singapore", '0x1c09' : "English - South Africa", '0x2c09' : "English - Trinidad", '0x3009' : "English - Zimbabwe", '0x425' : "Estonian",
                 '0x438' : "Faroese", '0x429' : "Farsi", '0x464' : "Filipino", '0x040b' : "Finnish", '0x040c' : "French - France", '0x080c' : "French - Belgium",
                 '0x2c0c' : "French - Cameroon", '0x0c0c' : "French - Canada", '0x240c' : "French - Democratic Rep. of Congo", '0x300c' : "French - Cote d'Ivoire",
                 '0x3c0c' : "French - Haiti", '0x140c' : "French - Luxembourg", '0x340c' : "French - Mali", '0x180c' : "French - Monaco", '0x380c' : "French - Morocco",
                 '0xe40c' : "French - North Africa", '0x200c' : "French - Reunion", '0x280c' : "French - Senegal", '0x100c' : "French - Switzerland", 
                 '0x1c0c' : "French - West Indies", '0x462' : "Frisian - Netherlands", '0x467' : "Fulfulde - Nigeria", '0x042f' : "FYRO Macedonian", '0x083c' : "Gaelic (Ireland)",
                 '0x043c' : "Gaelic (Scotland)", '0x456' : "Galician", '0x437' : "Georgian", '0x407' : "German - Germany", '0x0c07' : "German - Austria", '0x1407' : "German - Liechtenstein",
                 '0x1007' : "German - Luxembourg", '0x807' : "German - Switzerland", '0x408' : "Greek", '0x474' : "Guarani - Paraguay", '0x447' : "Gujarati", '0x468' : "Hausa - Nigeria",
                 '0x475' : "Hawaiian - United States", '0x040d' : "Hebrew", '0x439' : "Hindi", '0x040e' : "Hungarian", '0x469' : "Ibibio - Nigeria", '0x040f' : "Icelandic",
                 '0x470' : "Igbo - Nigeria", '0x421' : "Indonesian", '0x045d' : "Inuktitut", '0x410' : "Italian - Italy", '0x810' : "Italian - Switzerland", '0x411' : "Japanese",
                 '0x044b' : "Kannada", '0x471' : "Kanuri - Nigeria", '0x860' : "Kashmiri", '0x460' : "Kashmiri (Arabic)", '0x043f' : "Kazakh", '0x453' : "Khmer", '0x457' : "Konkani",
                 '0x412' : "Korean", '0x440' : "Kyrgyz (Cyrillic)", '0x454' : "Lao", '0x476' : "Latin", '0x426' : "Latvian", '0x427' : "Lithuanian", '0x043e' : "Malay - Malaysia",
                 '0x083e' : "Malay - Brunei Darussalam", '0x044c' : "Malayalam", '0x043a' : "Maltese", '0x458' : "Manipuri", '0x481' : "Maori - New Zealand", '0x044e' : "Marathi",
                 '0x450' : "Mongolian (Cyrillic)", '0x850' : "Mongolian (Mongolian)", '0x461' : "Nepali", '0x861' : "Nepali - India", '0x414' : "Norwegian (Bokmål)", 
                 '0x814' : "Norwegian (Nynorsk)", '0x448' : "Oriya", '0x472' : "Oromo", '0x479' : "Papiamentu", '0x463' : "Pashto", '0x415' : "Polish", '0x416' : "Portuguese - Brazil",
                 '0x816' : "Portuguese - Portugal", '0x446' : "Punjabi", '0x846' : "Punjabi (Pakistan)", '0x046B' : "Quecha - Bolivia", '0x086B' : "Quecha - Ecuador", 
                 '0x0C6B' : "Quecha - Peru", '0x417' : "Rhaeto-Romanic", '0x418' : "Romanian", '0x818' : "Romanian - Moldava", '0x419' : "Russian", '0x819' : "Russian - Moldava",
                 '0x043b' : "Sami (Lappish)", '0x044f' : "Sanskrit", '0x046c' : "Sepedi", '0x0c1a' : "Serbian (Cyrillic)", '0x081a' : "Serbian (Latin)", '0x459' : "Sindhi - India",
                 '0x859' : "Sindhi - Pakistan", '0x045b' : "Sinhalese - Sri Lanka", '0x041b' : "Slovak", '0x424' : "Slovenian", '0x477' : "Somali", '0x042e' : "Sorbian", 
                 '0x0c0a' : "Spanish - Spain (Modern Sort)", '0x040a' : "Spanish - Spain (Traditional Sort)", '0x2c0a' : "Spanish - Argentina", '0x400a' : "Spanish - Bolivia",
                 '0x340a' : "Spanish - Chile", '0x240a' : "Spanish - Colombia", '0x140a' : "Spanish - Costa Rica", '0x1c0a' : "Spanish - Dominican Republic", 
                 '0x300a' : "Spanish - Ecuador", '0x440a' : "Spanish - El Salvador", '0x100a' : "Spanish - Guatemala", '0x480a' : "Spanish - Honduras", '0xe40a' : "Spanish - Latin America",
                 '0x080a' : "Spanish - Mexico", '0x4c0a' : "Spanish - Nicaragua", '0x180a' : "Spanish - Panama", '0x3c0a' : "Spanish - Paraguay", '0x280a' : "Spanish - Peru",
                 '0x500a' : "Spanish - Puerto Rico", '0x540a' : "Spanish - United States", '0x380a' : "Spanish - Uruguay", '0x200a' : "Spanish - Venezuela", '0x430' : "Sutu",
                 '0x441' : "Swahili", '0x041d' : "Swedish", '0x081d' : "Swedish - Finland", '0x045a' : "Syriac", '0x428' : "Tajik", '0x045f' : "Tamazight (Arabic)", 
                 '0x085f' : "Tamazight (Latin)", '0x449' : "Tamil", '0x444' : "Tatar", '0x044a' : "Telugu", '0x041e' : "Thai", '0x851' : "Tibetan - Bhutan", 
                 '0x451' : "Tibetan - People's Republic of China", '0x873' : "Tigrigna - Eritrea", '0x473' : "Tigrigna - Ethiopia", '0x431' : "Tsonga", '0x432' : "Tswana",
                 '0x041f' : "Turkish", '0x442' : "Turkmen", '0x480' : "Uighur - China", '0x422' : "Ukrainian", '0x420' : "Urdu", '0x820' : "Urdu - India", '0x843' : "Uzbek (Cyrillic)",
                 '0x443' : "Uzbek (Latin)", '0x433' : "Venda", '0x042a' : "Vietnamese", '0x452' : "Welsh", '0x434' : "Xhosa", '0x478' : "Yi", '0x043d' : "Yiddish", '0x046a' : "Yoruba",
                 '0x435' : "Zulu", '0x04ff' : "HID (Human Interface Device)"
                 }

    # Get the current active window handle
    handle = user32.GetForegroundWindow()

    # Get the thread id from that window handle
    threadid = user32.GetWindowThreadProcessId(handle, 0)

    # Get the keyboard layout id from the threadid
    layout_id = user32.GetKeyboardLayout(threadid)

    # Extract the keyboard language id from the keyboard layout id
    language_id = layout_id & (2 ** 16 - 1)

    # Convert the keyboard language id from decimal to hexadecimal
    language_id_hex = hex(language_id)

    # Check if the hex value is in the dictionary.
    if language_id_hex in languages.keys():
        return languages[language_id_hex]
    else:
        # Return language id hexadecimal value if not found.
        return str(language_id_hex)


layout = dict(zip(map(ord, "qwertyuiop[]asdfghjkl;'zxcvbnm,./`"
                           'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?~'),
                           "йцукенгшщзхъфывапролджэячсмитьбю.ё"
                           'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'))


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
        print('-- char --')
    
    def onKey(self, event, name):
        keycode = event.GetUnicodeKey()
        keycode2 = event.GetKeyCode()
        
        if keycode != wx.WXK_NONE:

            if keycode == 13:
                print('-- enter --')
                if name == 'up':
                    self.addText('\n')

            elif keycode == 8:
                print('-- backspace --')
                if name == 'down':
                    self.addText(None) # for remove

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

                print(name, "You pressed: ", keycode, ch, keycode3, chr(keycode3), 'has_shift:', has_shift)
                if name == 'down':
                    self.addText(ch)

        else:
            if keycode2 == wx.WXK_LEFT:
                print('-- left --')

            elif keycode2 == wx.WXK_RIGHT:
                print('-- right --')

            else:
                print('-- no key --')

                if keycode2 == wx.WXK_F1:
                    pass

        event.Skip()

    def addText(self, text):
        ability = INPUT_CONTROL.focus_into
        if ability:
            ability.addText(text)
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
        self.ROOT_NODE = ROOT_NODE = noder_parse_file(html_path) if html_path else noder_parse_text(html_text)
        #connect_listview(ROOT_NODE, listview_cls=listview_cls)

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