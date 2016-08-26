from django.dispatch import Signal

document_changed=Signal()
coord_selection_created=Signal()
coord_selection_changed=Signal()
coord_selection_deleted=Signal()
bookmark_added=Signal()
bookmark_deleted=Signal()
