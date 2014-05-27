import operator
from django.db.models import Q
from bodb.models import Workspace
from registration.models import User
from taggit.utils import parse_tags

def runWorkspaceSearch(search_data, userId):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create Workspace search
    searcher=WorkspaceSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            #q=dispatch(q, userId)
            filters.append(dispatch(userId))

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    visibility_q=Q(created_by__is_active=True)
    if not user.is_superuser:
        visibility_q=Q(visibility_q & Q(group__in=user.groups.all()))

    q=reduce(op,filters) & visibility_q
    print(q)
    # get results
    if q and len(q):
        results = Workspace.objects.filter(q).select_related().distinct()
    else:
        results = Workspace.objects.all().select_related()

    return results.order_by('title')


class WorkspaceSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, userId):
        if self.keywords:
            op=operator.or_
            if self.keywords_options=='all':
                op=operator.and_
            words=parse_tags(self.keywords)
            title_filters=[Q(title__icontains=word) for word in words]
            description_filters=[Q(description__icontains=word) for word in words]
            username_filters=[Q(created_by__username__icontains=word) for word in words]
            firstname_filters=[Q(created_by__first_name__icontains=word) for word in words]
            lastname_filters=[Q(created_by__last_name__icontains=word) for word in words]
            return reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,username_filters) | \
                   reduce(op,firstname_filters) | reduce(op,lastname_filters)
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

    # search by description
    def search_description(self, userId):
        if self.description:
            op=operator.or_
            if self.description_options=='all':
                op=operator.and_
            words=parse_tags(self.description)
            keyword_filters=[Q(description__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by created_by
    def search_created_by(self, userId):
        if self.created_by:
            return Q(created_by__id=userId)
        return Q()

    def search_username(self, userId):
        if self.username:
            return Q(created_by__username__icontains=self.username)
        return Q()

    def search_first_name(self, userId):
        if self.first_name:
            return Q(created_by__first_name__icontains=self.first_name)
        return Q()

    def search_last_name(self, userId):
        if self.last_name:
            return Q(created_by__last_name__icontains=self.last_name)
        return Q()

    def search_created_from(self, userId):
        if self.created_from:
            return Q(created_date__gte=self.created_from)
        return Q()

    def search_created_to(self, userId):
        if self.created_to:
            return Q(created_date__lte=self.created_to)
        return Q()

    # search by related brain region
    def search_related_brain_region(self, userId):
        if self.related_brain_region:
            op=operator.or_
            if self.related_brain_region_options=='all':
                op=operator.and_
            words=parse_tags(self.related_brain_region)
            keyword_filters=[Q(Q(related_regions__name__icontains=word) |
                               Q(related_regions__abbreviation__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related BOP
    def search_related_bop(self, userId):
        if self.related_bop:
            op=operator.or_
            if self.related_bop_options=='all':
                op=operator.and_
            words=parse_tags(self.related_bop)
            title_filters=[Q(related_bops__title__icontains=word) for word in words]
            description_filters=[Q(related_bops__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_bops__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            return keyword_q
        return Q()

    # search by related Model
    def search_related_model(self, userId):
        if self.related_model:
            op=operator.or_
            if self.related_model_options=='all':
                op=operator.and_
            words=parse_tags(self.related_model)
            title_filters=[Q(related_models__title__icontains=word) for word in words]
            description_filters=[Q(related_models__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_models__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            return keyword_q
        return Q()

    # search by related SED
    def search_related_sed(self, userId):
        if self.related_sed:
            op=operator.or_
            if self.related_sed_options=='all':
                op=operator.and_
            words=parse_tags(self.related_sed)
            title_filters=[Q(related_seds__title__icontains=word) for word in words]
            description_filters=[Q(related_seds__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_seds__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            return keyword_q
        return Q()

    # search by related SSR
    def search_related_ssr(self, userId):
        if self.related_ssr:
            op=operator.or_
            if self.related_ssr_options=='all':
                op=operator.and_
            words=parse_tags(self.related_ssr)
            title_filters=[Q(related_ssrs__title__icontains=word) for word in words]
            description_filters=[Q(related_ssrs__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_ssrs__narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters)
            return keyword_q
        return Q()

    # search by related Literature title
    def search_related_literature_title(self, userId):
        if self.related_literature_title:
            op=operator.or_
            if self.related_literature_title_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_title)
            keyword_filters=[Q(related_literature__title__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related Literature author name
    def search_related_literature_author(self, userId):
        if self.related_literature_author:
            op=operator.or_
            if self.related_literature_author_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_author)
            keyword_filters=[Q(Q(related_literature__authors__author__first_name__icontains=word) |
                               Q(related_literature__authors__author__last_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related Literature minimum year
    def search_related_literature_year_min(self, userId):
        if self.related_literature_year_min:
            return Q(related_literature__year__gte=self.related_literature_year_min)
        return Q()

    # search by related Literature maximum year
    def search_related_literature_year_max(self, userId):
        if self.related_literature_year_max:
            return Q(related_literature__year__lte=self.related_literature_year_max)
        return Q()

    # search by related Literature annotation
    def search_related_literature_annotation(self, userId):
        if self.related_literature_annotation:
            op=operator.or_
            if self.related_literature_annotation_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_annotation)
            keyword_filters=[Q(related_literature__annotation__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()