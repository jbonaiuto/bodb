import operator
from django.db.models import Q
from bodb.models import BrainRegion
from taggit.utils import parse_tags

def runBrainRegionSearch(search_data):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create BrainRegion search
    searcher=BrainRegionSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            filters.append(dispatch())

    q=reduce(op,filters)

    # get results
    if q and len(q):
        results = BrainRegion.objects.filter(q).distinct().select_related('nomenclature','parent_region').prefetch_related('nomenclature__species')
    else:
        results = BrainRegion.objects.all().select_related('nomenclature','parent_region').prefetch_related('nomenclature__species')

    if 'order_by' in search_data:
        if search_data['order_by']=='nomenclature':
            results=results.order_by('nomenclature__name')
        elif search_data['order_by']=='parent_region':
            results=list(results)
            results.sort(key=BrainRegion.parent_region_name,reverse=search_data['direction']=='descending')
        elif search_data['order_by']=='species':
            results=list(results)
            results.sort(key=BrainRegion.species_name,reverse=search_data['direction']=='descending')
        else:
            results=results.order_by(search_data['order_by'])
            if 'direction' in search_data and search_data['direction']=='descending':
                results=results.reverse()
    return results


class BrainRegionSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by name or abbreviation
    def search_keywords(self):
        if self.keywords:
            op=operator.or_
            if self.keywords_options=='all':
                op=operator.and_

            words=parse_tags(self.keywords)
            name_filters=[Q(name__icontains=word) for word in words]
            abbreviation_filters=[Q(abbreviation__icontains=word) for word in words]
            keyword_q = reduce(op,name_filters) | reduce(op,abbreviation_filters)
            return keyword_q
        return Q()

    def search_title(self):
        self.name=self.title
        self.name_options=self.title_options
        return self.search_name()

    # search by name
    def search_name(self):
        if self.name:
            op=operator.or_
            if self.name_options=='all':
                op=operator.and_

            words=parse_tags(self.name)
            keyword_filters=[Q(name__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by abbreviation
    def search_abbreviation(self):
        if self.abbreviation:
            op=operator.or_
            if self.abbreviation_options=='all':
                op=operator.and_
            words=parse_tags(self.abbreviation)
            keyword_filters=[Q(abbreviation__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by parent
    def search_parent(self):
        if self.parent:
            op=operator.or_
            if self.parent_options=='all':
                op=operator.and_
            words=parse_tags(self.parent)
            name_filters=[Q(parent_region__name__icontains=word) for word in words]
            abbreviation_filters=[Q(parent_region__abbreviation__icontains=word) for word in words]
            keyword_q = reduce(op,name_filters) | reduce(op,abbreviation_filters)
            return keyword_q
        return Q()

    # search by nomenclature
    def search_nomenclature(self):
        if self.nomenclature:
            op=operator.or_
            if self.nomenclature_options=='all':
                op=operator.and_
            words=parse_tags(self.nomenclature)
            keyword_filters=[Q(Q(nomenclature__name__icontains=word) | Q(nomenclature__lit__title__icontains=word) |
                               Q(nomenclature__lit__authors__author__first_name__icontains=word) |
                               Q(nomenclature__lit__authors__author__last_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_genus(self):
        if self.genus:
            return Q(nomenclature__species__genus_name__iexact=self.genus)
        return Q()

    # search by species
    def search_species(self):
        if self.species:
            genus,species=self.species.split(' ')
            return Q(Q(nomenclature__species__genus_name__iexact=genus) & Q(nomenclature__species__species_name__iexact=species))
        return Q()

    # search by region type
    def search_region_type(self):
        if self.region_type:
            return Q(brain_region_type__iexact=self.region_type)
        return Q()

    def search_public(self):
        if self.public:
            if self.public=='False':
                # all literature entries are public, so return no entries
                return Q(id=-1)
        return Q()

    # search by collator
    def search_collator(self):
        if self.collator:
            return Q(id=-1)
        return Q()

    def search_username(self):
        if self.username:
            return Q(id=-1)
        return Q()

    def search_first_name(self):
        if self.first_name:
            return Q(id=-1)
        return Q()

    def search_last_name(self):
        if self.last_name:
            return Q(id=-1)
        return Q()

