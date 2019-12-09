from PIL import Image
from charls.pillow_plugin.jpls_image_plugin import JplsImageFile, _save, _accept
from charls.pillow_plugin.jpls_image_codec import JplsImageDecoder, JplsImageEncoder

Image.register_open(JplsImageFile.format, JplsImageFile, _accept)
Image.register_save(JplsImageFile.format, _save)
Image.register_extension(JplsImageFile.format, ".jls")
Image.register_decoder('jpeg_ls', JplsImageDecoder)
