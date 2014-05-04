import Image
from StringIO import StringIO
import os
from django.core.files.uploadhandler import MemoryFileUploadHandler
from uscbp import settings

class ConvertImageUploadHandler(MemoryFileUploadHandler):
    def file_complete(self, file_size):
        """
        Return a file object if we're activated.
        """
        if not self.activated:
            return
        self.file.seek(0)
        if not self.content_type is None and 'image' in self.content_type:
            name, ext = os.path.splitext(self.file_name)
            if ext.lower().endswith('tif') or ext.lower().endswith('tiff'):

                newfile = StringIO()
                img = Image.open(self.file)
                img.save(newfile, 'PNG')
                self.file = newfile

                self.file_name = '%s.png' % name
                self.content_type = 'image/png'
        return super(ConvertImageUploadHandler, self).file_complete(file_size)