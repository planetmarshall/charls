from PIL import Image
from .JplsImagePlugin import JplsImageFile, _save
from .JplsImageCodec import JplsImageDecoder, JplsImageEncoder

Image.register_open(JplsImageFile.format, JplsImageFile)
Image.register_save(JplsImageFile.format, _save)
Image.register_extension(JplsImageFile.format, ".jls")
Image.register_decoder('jpeg_ls', JplsImageDecoder)
