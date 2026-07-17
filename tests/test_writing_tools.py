from rmc.exporters.writing_tools import Pen, Shader, svg_alpha, svg_rgb


def test_svg_rgb_drops_alpha_channel():
    assert svg_rgb((48, 74, 224, 77)) == "rgb(48, 74, 224)"


def test_svg_alpha_converts_8bit_alpha_to_opacity():
    assert svg_alpha((48, 74, 224, 77)) == 77 / 255
    assert svg_alpha((48, 74, 224)) == 1


def test_pen_opacity_includes_explicit_rgba_alpha():
    pen = Pen("Test", 1, (48, 74, 224, 77))
    assert pen.get_segment_opacity(0, 0, 0, 0, 0) == 77 / 255


def test_shader_uses_explicit_rgba_alpha_without_extra_fade():
    pen = Shader(12, (48, 74, 224, 77))
    assert pen.get_segment_color(0, 0, 0, 0, 0) == "rgb(48, 74, 224)"
    assert pen.get_segment_opacity(0, 0, 0, 0, 0) == 77 / 255
