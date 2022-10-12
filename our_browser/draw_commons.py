

def cr_set_source_rgb_any_hex(cr, color):
    col = hex2color(color)
    if len(col) == 3:
        cr.set_source_rgb(*col)
    else:
        cr.set_source_rgba(*col)

def hex2color(color_hex):
    color_hex = color_hex.split('#')[1]
    if len(color_hex) >= 8:
        return (int(color_hex[:2], 16)/255.0, int(color_hex[2:4], 16)/255.0, int(color_hex[4:6], 16)/255.0,
            int(color_hex[6:8], 16)/255.0)
    else:
        return (int(color_hex[:2], 16)/255.0, int(color_hex[2:4], 16)/255.0, int(color_hex[4:6], 16)/255.0)
