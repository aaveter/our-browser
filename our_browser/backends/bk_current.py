
class CUR_BACKEND:
    #
    ImageSurface__create_from_png = None
    #
    DrawContext__set_bold = None
    DrawContext__rectangle = None


if True:
    import cairo
    #
    CUR_BACKEND.ImageSurface__create_from_png = lambda src: cairo.ImageSurface.create_from_png(src)
    #
    CUR_BACKEND.DrawContext__set_bold = lambda cr, family: cr.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD)
    CUR_BACKEND.DrawContext__set_font_size = lambda cr, font_size: cr.set_font_size(font_size)
    CUR_BACKEND.DrawContext__rectangle = lambda cr, rect: cr.rectangle(*rect)
    CUR_BACKEND.DrawContext__fill = lambda cr: cr.fill()
    CUR_BACKEND.DrawContext__stroke = lambda cr: cr.stroke()
    CUR_BACKEND.DrawContext__show_text = lambda cr, line: cr.show_text(line)
    CUR_BACKEND.DrawContext__set_line_width = lambda cr, w: cr.set_line_width(w)
    CUR_BACKEND.DrawContext__set_source_rgb = lambda cr, color: cr.set_source_rgb(*color)
    CUR_BACKEND.DrawContext__move_to = lambda cr, x, y: cr.move_to(x, y)
    CUR_BACKEND.DrawContext__line_to = lambda cr, x, y: cr.line_to(x, y)
    CUR_BACKEND.DrawContext__get_text_width = lambda cr, line: cr.text_extents(line)[:4][2]
