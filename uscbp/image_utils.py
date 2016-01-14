import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg
matplotlib.use('Agg')
import Image
import os

def get_thumbnail(image_path, w, h):
    new_size=scale(w,h,300,30000,True)
    image_dir, image_name = os.path.split(image_path)
    thumb_name = "%s-%sx%s.jpg" % (os.path.splitext(image_name)[0], new_size[0], new_size[1])
    thumb_path = os.path.join(image_dir, thumb_name)
    if not os.path.exists(thumb_path):
        image = Image.open(image_path)
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")
        try:
            image.thumbnail(new_size, Image.ANTIALIAS)
            image.save(thumb_path, "JPEG", quality=100)
        except Exception,e:
            print(str(e))
            return image_path
    return thumb_path

def scale(w, h, x, y, maximum=True):
    nw = y * w / h
    nh = x * h / w
    if maximum ^ (nw >= x):
        return nw or 1, y
    return x, nh or 1


def save_to_png(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(output_file, dpi=72)

def save_to_eps(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_eps(output_file, dpi=72)