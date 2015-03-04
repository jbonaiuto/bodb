import operator
from django.db.models import Q
from bodb.models import Document, BOP
from bodb.search.document import DocumentWithLiteratureSearch
from registration.models import User
from taggit.utils import parse_tags

def runBOPSearch(search_data, userId, exclude=None):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create BOP search
    searcher=BOPSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            #q=dispatch(q, userId)
            filters.append(dispatch(userId))

    # restrict to user's own entries or those of other users that are not drafts
    try:
        user=User.objects.get(id=userId)
    except (User.DoesNotExist, User.MultipleObjectsReturned), err:
        user=User.get_anonymous()

    q=reduce(op,filters) & Document.get_security_q(user)

    # get results
    if q and len(q):
        results = BOP.objects.filter(q).select_related('collator').distinct()
    else:
        results = BOP.objects.all().select_related('collator')

    if exclude is not None and not exclude=='None' and len(exclude):
        results=results.exclude(id=int(exclude))

    if 'bop_order_by' in search_data:
        if search_data['bop_order_by']=='collator':
            results=list(results)
            results.sort(key=BOP.get_collator_str, reverse=search_data['bop_direction']=='descending')
        else:
            results=results.order_by(search_data['bop_order_by'])
            if 'bop_direction' in search_data and search_data['bop_direction']=='descending':
                results=results.reverse()
    else:
        results=results.order_by('title')


    return results


class BOPSearch(DocumentWithLiteratureSearch):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by parent
    def search_parent(self, userId):
        if self.parent:
            op=operator.or_
            if self.parent_options=='all':
                op=operator.and_
            words=parse_tags(self.parent)
            title_filters=[Q(parent__title__icontains=word) for word in words]
            description_filters=[Q(parent__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(parent__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            return keyword_q
        return Q()

    # search by building SED
    def search_building_sed(self, userId):
        if self.building_sed:
            op=operator.or_
            if self.building_sed_options=='all':
                op=operator.and_
            words=parse_tags(self.building_sed)
            title_filters=[Q(related_build_sed_document__sed__title__icontains=word) for word in words]
            description_filters=[Q(related_build_sed_document__sed__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_build_sed_document__sed__narrative__icontains=word) for word in words]
            relevance_filters=[Q(related_build_sed_document__relevance_narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters) | \
                        reduce(op,relevance_filters)
            return keyword_q
        return Q()



