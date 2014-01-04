from django.dispatch import Signal

forum_post_added = Signal(providing_args=[])
document_changed=Signal()
coord_selection_created=Signal()
coord_selection_changed=Signal()
coord_selection_deleted=Signal()
bookmark_added=Signal()
bookmark_deleted=Signal()
