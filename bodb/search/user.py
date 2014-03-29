import operator
from django.db.models import Q
from bodb.models import Document
from registration.models import User
from taggit.utils import parse_tags

def runUserSearch(search_data, userId):
    filters=[]

    # create BOP search
    searcher=UserSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            #q=dispatch(q, userId)
            filters.append(dispatch(userId))

    results = User.objects.filter(is_active=True)
    # get results
    if search_data['search_options']=='all':
        for filter in filters:
            results=results.filter(filter)
    else:
        results=results.filter(reduce(operator.or_,filters))
    return results.order_by('username').select_related().distinct()


class UserSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, userId):
        if self.keywords:
            op=operator.or_
            if self.keywords_options=='all':
                op=operator.and_
            words=parse_tags(self.keywords)
            username_filters=[Q(username__icontains=word) for word in words]
            first_name_filters=[Q(first_name__icontains=word) for word in words]
            last_name_filters=[Q(last_name__icontains=word) for word in words]
            return reduce(op,username_filters) | reduce(op,first_name_filters) | reduce(op,last_name_filters)
        return Q()

    def search_username(self, userId):
        if self.username:
            return Q(username__icontains=self.username)
        return Q()

    def search_first_name(self, userId):
        if self.first_name:
            return Q(first_name__icontains=self.first_name)
        return Q()

    def search_last_name(self, userId):
        if self.last_name:
            return Q(last_name__icontains=self.last_name)
        return Q()

    def search_bop(self, userId):
        if self.bop:
            # restrict to user's own entries or those of other users that are not drafts
            if User.objects.filter(id=userId):
                user=User.objects.get(id=userId)
            else:
                user=User.get_anonymous()
            op=operator.or_
            if self.bop_options=='all':
                op=operator.and_
            words=parse_tags(self.bop)
            title_filters=[Q(document__bop__title__icontains=word) for word in words]
            description_filters=[Q(document__bop__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(document__bop__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            keyword_q&=Document.get_security_q(user,field='document')
            return keyword_q
        return Q()

    def search_model(self, userId):
        if self.model:
            # restrict to user's own entries or those of other users that are not drafts
            if User.objects.filter(id=userId):
                user=User.objects.get(id=userId)
            else:
                user=User.get_anonymous()
            op=operator.or_
            if self.model_options=='all':
                op=operator.and_
            words=parse_tags(self.model)
            title_filters=[Q(document__module__model__title__icontains=word) for word in words]
            description_filters=[Q(document__module__model__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(document__module__model__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            keyword_q&=Document.get_security_q(user,field='document')
            return keyword_q
        return Q()

    def search_sed(self, userId):
        if self.sed:
            # restrict to user's own entries or those of other users that are not drafts
            if User.objects.filter(id=userId):
                user=User.objects.get(id=userId)
            else:
                user=User.get_anonymous()
            op=operator.or_
            if self.sed_options=='all':
                op=operator.and_
            words=parse_tags(self.sed)
            title_filters=[Q(document__sed__title__icontains=word) for word in words]
            description_filters=[Q(document__sed__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(document__sed__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            keyword_q&=Document.get_security_q(user,field='document')
            return keyword_q
        return Q()

    def search_ssr(self, userId):
        if self.ssr:
            # restrict to user's own entries or those of other users that are not drafts
            if User.objects.filter(id=userId):
                user=User.objects.get(id=userId)
            else:
                user=User.get_anonymous()
            op=operator.or_
            if self.ssr_options=='all':
                op=operator.and_
            words=parse_tags(self.ssr)
            title_filters=[Q(document__ssr__title__icontains=word) for word in words]
            description_filters=[Q(document__ssr__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(document__ssr__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            keyword_q&=Document.get_security_q(user,field='document')
            return keyword_q
        return Q()
