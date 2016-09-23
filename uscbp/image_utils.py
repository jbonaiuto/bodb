import Image
import os

def get_thumbnail(image_path, w, h):
    new_size=scale(w,h,300,30000,True)
    image_dir, image_name = os.path.split(image_path)
    thumb_name = "%s-%sx%s.png" % (os.path.splitext(image_name)[0], new_size[0], new_size[1])
    thumb_path = os.path.join(image_dir, thumb_name)
    #if not os.path.exists(thumb_path):
    image = Image.open(image_path)
#        if image.mode not in ("L", "RGB"):
#            image = image.convert("RGB")
    try:
        image.thumbnail(new_size)#, Image.ANTIALIAS)
        image.save(thumb_path, "PNG", quality=100)
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

