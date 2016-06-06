from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from bodb.models import Document


class BODBAPIAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        #return object_list.filter(user=bundle.request.user)
    
        #q=Document.get_security_q(bundle.request.user)
        #return object_list.filter(q)
        
        return object_list
            

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        #return bundle.obj.user == bundle.request.user
        if bundle.request.user.is_superuser:
            return True
        else:
            if bundle.obj.collator.id==bundle.request.user.id or bundle.obj.public==1:
                return True
            elif bundle.obj.draft==0:
                for group in bundle.request.user.groups.all():
                    if bundle.obj.collator.groups.filter(id=group.id).exists():
                        return True

    def create_list(self, object_list, bundle):
        # Assuming they're auto-assigned to ``user``.
        #return object_list
        raise Unauthorized("Sorry, no puts.")

    def create_detail(self, object_list, bundle):
        #return bundle.obj.user == bundle.request.user
        raise Unauthorized("Sorry, no puts.")

    def update_list(self, object_list, bundle):
#         allowed = []
# 
#         # Since they may not all be saved, iterate over them.
#         for obj in object_list:
#             if obj.user == bundle.request.user:
#                 allowed.append(obj)
# 
#         return allowed
    
        raise Unauthorized("Sorry, no updates.")

    def update_detail(self, object_list, bundle):
        #return bundle.obj.user == bundle.request.user
        raise Unauthorized("Sorry, no updates.")

    def delete_list(self, object_list, bundle):
        # Sorry user, no deletes for you!
        raise Unauthorized("Sorry, no deletes.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")