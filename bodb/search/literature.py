import operator
from django.db.models import Q
from bodb.models.literature import *
from taggit.utils import parse_tags

def runLiteratureSearch(search_data, userId):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create a Literature search
    searcher=LiteratureSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            filters.append(dispatch(userId))

    q=reduce(op,filters)

    # get results
    if len(q):
        # filter by literature type if given
        if 'type' in search_data and len(search_data['type']):
            results = eval(search_data['type']).objects.filter(q).select_related('collator').prefetch_related('authors__author').distinct()
        else:
            results = Literature.objects.filter(q).select_related('collator').prefetch_related('authors__author').distinct()
    # filter by literature type if given
    elif 'type' in search_data and len(search_data['type']):
        results = eval(search_data['type']).objects.all().select_related('collator').prefetch_related('authors__author')
    else:
        results = Literature.objects.all().select_related('collator').prefetch_related('authors__author')

    if 'order_by' in search_data:
        if search_data['order_by']=='string':
            results=list(results)
            results.sort(key=Literature.str, reverse=search_data['direction']=='descending')
        else:
            results=results.order_by(search_data['order_by'])
            if 'direction' in search_data and search_data['direction']=='descending':
                results=results.reverse()
    else:
        results=list(results)
        results.sort(key=Literature.author_names)
    return results


class LiteratureSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, annotation, and author name
    def search_keywords(self, userId):
        if self.keywords:
            op=operator.or_
            if self.keywords_options=='all':
                op=operator.and_

            words=parse_tags(self.keywords)
            title_filters=[Q(title__icontains=word) for word in words]
            annotation_filters=[Q(Q(authors__author__first_name__icontains=word) |
                                  Q(authors__author__last_name__icontains=word)) for word in words]
            author_filters=[Q(annotation__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,author_filters) | reduce(op,annotation_filters)
            return keyword_q
        return Q()

    # search by title
    def search_title(self, userId):
        if self.title:
            op=operator.or_
            if self.title_options=='all':
                op=operator.and_

            words=parse_tags(self.title)
            keyword_filters=[Q(title__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by author name
    def search_author(self, userId):
        if self.author:
            op=operator.or_
            if self.author_options=='all':
                op=operator.and_
            words=parse_tags(self.author)
            keyword_filters=[Q(Q(authors__author__first_name__icontains=word) |
                               Q(authors__author__last_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by literature type (handled by search function in views.py)
    def search_type(self, userId):
        return Q()

    # search by minimum year
    def search_year_min(self, userId):
        if self.year_min:
            return Q(year__gte=self.year_min)
        return Q()

    # search by maximum year
    def search_year_max(self, userId):
        if self.year_max:
            return Q(year__lte=self.year_max)
        return Q()

    # search by annotation
    def search_annotation(self, userId):
        if self.annotation:
            op=operator.or_
            if self.annotation_options=='all':
                op=operator.and_
            words=parse_tags(self.annotation)
            keyword_filters=[Q(annotation__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by collator
    def search_collator(self, userId):
        if self.collator:
            return Q(collator__id=userId)
        return Q()

    def search_username(self, userId):
        if self.username:
            return Q(collator__username__icontains=self.username)
        return Q()

    def search_first_name(self, userId):
        if self.first_name:
            return Q(collator__first_name__icontains=self.first_name)
        return Q()

    def search_last_name(self, userId):
        if self.last_name:
            return Q(collator__last_name__icontains=self.last_name)
        return Q()

    def search_public(self, userId):
        if self.public:
            if self.public=='False':
                # all literature entries are public, so return no entries
                return Q(id=-1)
        return Q()

    def search_created_from(self, userId):
        if self.created_from:
            return Q(creation_time__gte=self.created_from)
        return Q()

    def search_created_to(self, userId):
        if self.created_to:
            return Q(creation_time__lte=self.created_to)
        return Q()


