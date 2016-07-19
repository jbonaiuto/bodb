from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
from bodb.models import *


class BODBAPIAuthorization(Authorization):
    def read_list(self, object_list, bundle):
        q=Document.get_security_q(bundle.request.user)
        return object_list.filter(q)

    def read_detail(self, object_list, bundle):
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
        raise Unauthorized("Sorry, you are not allowed to perform this operation.")

    def create_detail(self, object_list, bundle):
        usr = bundle.request.user
        #print bundle.obj
        
        if usr.is_superuser:
            return True
        elif isinstance(bundle.obj, SED):
            usr.has_perm('bodb.add_sed')
        elif isinstance(bundle.obj, BOP):
            usr.has_perm('bodb.add_bop')
        elif isinstance(bundle.obj, Model):
            usr.has_perm('bodb.add_model')
        else: 
            raise Unauthorized("Sorry, you are not allowed to perform this operation.")

    def update_list(self, object_list, bundle):
        raise Unauthorized("Sorry, you are not allowed to perform this operation.")

    def update_detail(self, object_list, bundle):
        usr = bundle.request.user
        #print bundle.obj
        
        if usr.is_superuser:
            return True
        elif isinstance(bundle.obj, SED):
            usr.has_perm('bodb.change_sed')
        elif isinstance(bundle.obj, BOP):
            usr.has_perm('bodb.change_bop')
        elif isinstance(bundle.obj, Model):
            usr.has_perm('bodb.change_model')
        else: 
            raise Unauthorized("Sorry, you are not allowed to perform this operation.")

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, you are not allowed to perform this operation.")

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, you are not allowed to perform this operation.")