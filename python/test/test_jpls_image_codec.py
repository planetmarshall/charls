from charls.pillow_plugin.jpls_image_codec import (
    _interleave_pixels_for_encoding,
    _interleave_decoded_pixels,
    InterleaveMode
)


def test_encode_non_interleaved_rgb_pixels():
    src_pixels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    interleaved_pixels = list(_interleave_pixels_for_encoding(src_pixels, 3, InterleaveMode.NONE))

    assert [1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12] == interleaved_pixels


def test_encode_sample_interleaved_rgb_pixels():
    src_pixels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    interleaved_pixels = list(_interleave_pixels_for_encoding(src_pixels, 3, InterleaveMode.SAMPLE))

    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] == interleaved_pixels


def test_encode_line_interleaved_rgb_pixels():
    src_pixels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    interleaved_pixels = list(_interleave_pixels_for_encoding(src_pixels, 3, InterleaveMode.LINE))

    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] == interleaved_pixels


def test_decode_non_interleaved_rgb_pixels():
    interleaved_pixels = [1, 4, 7, 10, 2, 5, 8, 11, 3, 6, 9, 12]
    rgb_pixels = list(_interleave_decoded_pixels(interleaved_pixels, 3, InterleaveMode.NONE))

    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] == rgb_pixels


def test_decode_sample_interleaved_rgb_pixels():
    src_pixels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    rgb_pixels = list(_interleave_decoded_pixels(src_pixels, 3, InterleaveMode.SAMPLE))

    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] == rgb_pixels


def test_decode_line_interleaved_rgb_pixels():
    src_pixels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    rgb_pixels = list(_interleave_decoded_pixels(src_pixels, 3, InterleaveMode.LINE))

    assert [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] == rgb_pixels
