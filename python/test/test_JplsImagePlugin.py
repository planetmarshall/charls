from io import BytesIO
from struct import pack

from PIL import Image
import jpls_image_plugin

# def test_decode_jpls_data():
#     img = Image.open('../build/img.jls')
#     data = img.getdata()
#     assert data is not None
#     assert img.width == 1152

def test_encode_jpls_8():
    data = [
        0, 3, 18, 15,
        155, 255, 1, 6,
        42, 9, 254, 127
    ]
    raw_img = Image.frombytes('L', (4,3), pack('12B', *data))
    stream = BytesIO()
    raw_img.save(stream, 'JPEG-LS')
    compressed_data = stream.getvalue()
    assert compressed_data is not None


def test_encode_jpls_16():
    data = [
        0, 3, 18, 15,
        155, 255, 1, 65535,
        42, 9, 254, 127
    ]
    raw_img = Image.frombytes('I;16', (4,3), pack('>12H', *data))
    stream = BytesIO()
    raw_img.save(stream, 'JPEG-LS')
    compressed_data = stream.getvalue()
    assert compressed_data is not None
