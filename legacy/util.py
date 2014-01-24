from legacy.photologue.models import  Gallery

# get unique gallery slug by appending number to name until it is unique
def get_unique_gallery_slug(slug):
    unique_slug=slug
    idx=0
    while Gallery.objects.filter(title_slug=unique_slug):
        unique_slug=slug+str(idx)
        idx += 1
    return unique_slug


# get unique gallery title by appending number to title until it is unique
def get_unique_gallery_title(title):
    unique_title=title
    idx=0
    while Gallery.objects.filter(title=unique_title):
        unique_title=title+str(idx)
        idx += 1
    return unique_title


# create a new gallery with a unique title and slug
def create_gallery(title, title_slug):
    gallery=Gallery()
    gallery.title=get_unique_gallery_title(title)
    gallery.title_slug=get_unique_gallery_slug(title_slug)
    gallery.save()
    return gallery


