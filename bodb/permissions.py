from rest_framework import permissions
from bodb.models import Document


class IsEditorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        user=request.user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        elif request.method == "PUT" or request.method == "PATCH":
            return user.is_authenticated() and (obj.collator==user or user.is_superuser or
                                                user.has_perm('edit',Document.objects.get(id=obj.id)))
        elif request.method == "DELETE":
            return user.is_authenticated() and (obj.collator==user or user.is_superuser or
                                                user.has_perm('delete',Document.objects.get(id=obj.id)))
        else:
            return False
