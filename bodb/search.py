from django.db.models import Q
from bodb.models import Literature, Journal, Chapter, Book, Thesis, Conference, Unpublished, BrainRegion, Model, SSR, Document
from bodb.models.bop import BOP
from bodb.models.sed import SED, SEDCoord
from registration.models import User

def runBOPSearch(search_data, userId):
    q=Q()

    # create BOP search
    searcher=BOPSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q, userId)

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q &= Document.get_security_q(user)

    # get results
    if q and len(q):
        results = BOP.objects.filter(q).select_related().distinct()
    else:
        results = BOP.objects.all()
    return results


class BOPSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            tags_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                description_q = description_q | Q(brief_description__icontains=word)
                narrative_q = narrative_q | Q(narrative__icontains=word)
                tags_q = tags_q | Q(tags__name__icontains=word)
            keyword_q = title_q | description_q | narrative_q | tags_q
            q = q & keyword_q
        return q

    # search by title
    def search_title(self, q, userId):
        if self.title:
            words=self.title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(title__icontains=word)
            q = q  & keyword_q
        return q

    # search by description
    def search_description(self, q, userId):
        if self.description:
            words=self.description.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brief_description__icontains=word)
            q = q  & keyword_q
        return q

    # search by narrative
    def search_narrative(self, q, userId):
        if self.narrative:
            words=self.narrative.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(narrative__icontains=word)
            q = q  & keyword_q
        return q

    # search by tags
    def search_tags(self, q, userId):
        if self.tags:
            #words=self.tags.split()
            keyword_q=Q()
            for word in self.tags:
                keyword_q = keyword_q | Q(tags__name__icontains=word)
            q = q  & keyword_q
        return q

    # search by parent
    def search_parent(self, q, userId):
        if self.parent:
            words=self.parent.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            for word in words:
                title_q = title_q | Q(parent__title__icontains=word)
                description_q = description_q | Q(parent__brief_description__icontains=word)
                narrative_q = narrative_q | Q(parent__narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q
            q = q & keyword_q
        return q

    # search by related brain region
    def search_related_brain_region(self, q, userId):
        if self.related_brain_region:
            words=self.related_brain_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(relatedbrainregion__brain_region__name__icontains=word) | Q(relatedbrainregion__brain_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    # search by building SED
    def search_building_sed(self, q, userId):
        if self.building_sed:
            words=self.building_sed.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relevance_q=Q()
            for word in words:
                title_q = title_q | Q(buildsed__sed__title__icontains=word)
                description_q = description_q | Q(buildsed__sed__brief_description__icontains=word)
                narrative_q = narrative_q | Q(buildsed__sed__narrative__icontains=word)
                relevance_q = relevance_q | Q(buildsed__relevance_narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q
            q = q & keyword_q
        return q

    # search by related BOP
    def search_related_bop(self, q, userId):
        if self.related_bop:
            words=self.related_bop.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relevance_narrative_q=Q()
            for word in words:
                title_q = title_q | Q(relatedbop__bop__title__icontains=word)
                description_q = description_q | Q(relatedbop__bop__brief_description__icontains=word)
                narrative_q = narrative_q | Q(relatedbop__bop__narrative__icontains=word)
                relevance_narrative_q = relevance_narrative_q | Q(relatedbop__relevance_narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q | relevance_narrative_q
            q = q & keyword_q
        return q

    # search by related Model
    def search_related_model(self, q, userId):
        if self.related_model:
            words=self.related_model.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relationship_q=Q()
            for word in words:
                title_q = title_q | Q(relatedmodel__model__title__icontains=word)
                description_q = description_q | Q(relatedmodel__model__brief_description__icontains=word)
                narrative_q = narrative_q | Q(relatedmodel__model__narrative__icontains=word)
                relationship_q = relationship_q | Q(relatedmodel__relationship__icontains=word)
            keyword_q = title_q | description_q | narrative_q | relationship_q
            q = q & keyword_q
        return q

    # search by collator
    def search_collator(self, q, userId):
        if self.collator:
            q = q & Q(collator__id=userId)
        return q

    def search_username(self, q, userId):
        if self.username:
            q = q & Q(collator__username__icontains=self.username)
        return q

    def search_first_name(self, q, userId):
        if self.first_name:
            q = q & Q(collator__first_name__icontains=self.first_name)
        return q

    def search_last_name(self, q, userId):
        if self.last_name:
            q = q & Q(collator__last_name__icontains=self.last_name)
        return q

    # search by related Literature title
    def search_related_literature_title(self, q, userId):
        if self.related_literature_title:
            words=self.related_literature_title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__title__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature author name
    def search_related_literature_author(self, q, userId):
        if self.related_literature_author:
            words=self.related_literature_author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__authors__author__first_name__icontains=word) | Q(literature__authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature minimum year
    def search_related_literature_year_min(self, q, userId):
        if self.related_literature_year_min:
            q = q & Q(literature__year__gte=self.related_literature_year_min)
        return q

    # search by related Literature maximum year
    def search_related_literature_year_max(self, q, userId):
        if self.related_literature_year_max:
            q = q & Q(literature__year__lte=self.related_literature_year_max)
        return q

    # search by related Literature annotation
    def search_related_literature_annotation(self, q, userId):
        if self.related_literature_annotation:
            words=self.related_literature_annotation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__annotation__icontains=word)
            q = q & keyword_q
        return q

    def search_public(self, q, userId):
        if self.public:
            if self.public=='True':
                q = q & Q(public=True)
            else:
                q = q & Q(public=False)
        return q

    def search_created_from(self, q, userId):
        if self.created_from:
            q = q & Q(creation_time__gte=self.created_from)
        return q

    def search_created_to(self, q, userId):
        if self.created_to:
            q = q & Q(creation_time__lte=self.created_to)
        return q


# perform a BrainRegion search
def runBrainRegionSearch(search_data):
    q=Q()

    # create BrainRegion search
    searcher=BrainRegionSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q)

    # get results
    if q and len(q):
        results = BrainRegion.objects.filter(q).distinct()
    else:
        results = BrainRegion.objects.all()
    return results

# BrainRegion search
class BrainRegionSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by name or abbreviation
    def search_keywords(self, q):
        if self.keywords:
            words=self.keywords.split()
            name_q=Q()
            abbreviation_q=Q()
            for word in words:
                name_q = name_q | Q(name__icontains=word)
                abbreviation_q = abbreviation_q | Q(abbreviation__icontains=word)
            keyword_q = name_q | abbreviation_q
            q = q & keyword_q
        return q

    # search by name
    def search_name(self, q):
        if self.name:
            words=self.name.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(name__icontains=word)
            q = q  & keyword_q
        return q

    # search by abbreviation
    def search_abbreviation(self, q):
        if self.abbreviation:
            words=self.abbreviation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(abbreviation__icontains=word)
            q = q & keyword_q
        return q

    # search by parent
    def search_parent(self, q):
        if self.parent:
            words=self.parent.split()
            name_q=Q()
            abbreviation_q=Q()
            for word in words:
                name_q = name_q | Q(parent_region__name__icontains=word)
                abbreviation_q = abbreviation_q | Q(parent_region__abbreviation__icontains=word)
            keyword_q = name_q | abbreviation_q
            q = q & keyword_q
        return q

    # search by nomenclature
    def search_nomenclature(self, q):
        if self.nomenclature:
            words=self.nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(nomenclature__name__icontains=word)
            q = q & keyword_q
        return q

    # search by species
    def search_species(self, q):
        if self.species:
            words=self.species.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(nomenclature__species__genus_name__icontains=word) | Q(nomenclature__species__species_name__icontains=word) | Q(nomenclature__species__common_name__icontains=word)
            q = q & keyword_q
        return q

    # search by region type
    def search_region_type(self, q):
        if self.region_type:
            q = q & Q(brain_region_type__iexact=self.region_type)
        return q

    def search_public(self, q):
        if self.public:
            if self.public=='False':
                # all literature entries are public, so return no entries
                q=q & Q(id=-1)
        return q

# perform a Literature search
def runLiteratureSearch(search_data, userId):
    q=Q()

    # create a Literature search
    searcher=LiteratureSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q, userId)

    # get results
    if q and len(q):
        # filter by literature type if given
        if 'type' in search_data and len(search_data['type']):
            results = eval(search_data['type']).objects.filter(q).select_related().distinct()
        else:
            results = Literature.objects.filter(q).select_related().distinct()
    # filter by literature type if given
    elif 'type' in search_data and len(search_data['type']):
        results = eval(search_data['type']).objects.all()
    else:
        results = Literature.objects.all()
    return results

# Literature search
class LiteratureSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, annotation, and author name
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            annotation_q=Q()
            author_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                author_q = author_q | Q(authors__author__first_name__icontains=word) | Q(authors__author__last_name__icontains=word)
                annotation_q = annotation_q | Q(annotation__icontains=word)
            keyword_q = title_q | author_q | annotation_q
            q = q & keyword_q
        return q

    # search by title
    def search_title(self, q, userId):
        if self.title:
            words=self.title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(title__icontains=word)
            q = q  & keyword_q
        return q

    # search by author name
    def search_author(self, q, userId):
        if self.author:
            words=self.author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(authors__author__first_name__icontains=word) | Q(authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by literature type (handled by search function in views.py)
    def search_type(self, q, userId):
        return q

    # search by minimum year
    def search_year_min(self, q, userId):
        if self.year_min:
            q = q & Q(year__gte=self.year_min)
        return q

    # search by maximum year
    def search_year_max(self, q, userId):
        if self.year_max:
            q = q & Q(year__lte=self.year_max)
        return q

    # search by annotation
    def search_annotation(self, q, userId):
        if self.annotation:
            words=self.annotation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(annotation__icontains=word)
            q = q  & keyword_q
        return q

    # search by collator
    def search_collator(self, q, userId):
        if self.collator:
            q = q & Q(collator__id=userId)
        return q

    def search_username(self, q, userId):
        if self.username:
            q = q & Q(collator__username__icontains=self.username)
        return q

    def search_first_name(self, q, userId):
        if self.first_name:
            q = q & Q(collator__first_name__icontains=self.first_name)
        return q

    def search_last_name(self, q, userId):
        if self.last_name:
            q = q & Q(collator__last_name__icontains=self.last_name)
        return q

    def search_public(self, q, userId):
        if self.public:
            if self.public=='False':
                # all literature entries are public, so return no entries
                q=q & Q(id=-1)
        return q

    def search_created_from(self, q, userId):
        if self.created_from:
            q = q & Q(creation_time__gte=self.created_from)
        return q

    def search_created_to(self, q, userId):
        if self.created_to:
            q = q & Q(creation_time__lte=self.created_to)
        return q

# perform a Model search
def runModelSearch(search_data, userId):
    q=Q()

    # create Model search
    searcher=ModelSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q, userId)

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q &= Document.get_security_q(user)

    # get results
    if q and len(q):
        results = Model.objects.filter(q).select_related().distinct()
    else:
        results = Model.objects.all()
    return results

class ModelSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            author_q=Q()
            description_q=Q()
            narrative_q=Q()
            tags_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                author_q = author_q | Q(authors__author__first_name__icontains=word) | Q(authors__author__last_name__icontains=word)
                description_q = description_q | Q(brief_description__icontains=word)
                narrative_q = narrative_q | Q(narrative__icontains=word)
                tags_q = tags_q | Q(tags__name__icontains=word)
            keyword_q = title_q | author_q | description_q | narrative_q | tags_q
            q = q & keyword_q
        return q

    # search by title
    def search_title(self, q, userId):
        if self.title:
            words=self.title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(title__icontains=word)
            q = q  & keyword_q
        return q

    # search by author name
    def search_author(self, q, userId):
        if self.author:
            words=self.author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(authors__author__first_name__icontains=word) | Q(authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by description
    def search_description(self, q, userId):
        if self.description:
            words=self.description.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brief_description__icontains=word)
            q = q  & keyword_q
        return q

    # search by narrative
    def search_narrative(self, q, userId):
        if self.narrative:
            words=self.narrative.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(narrative__icontains=word)
            q = q  & keyword_q
        return q

    # search by tags
    def search_tags(self, q, userId):
        if self.tags:
            #words=self.tags.split()
            keyword_q=Q()
            for word in self.tags:
                keyword_q = keyword_q | Q(tags__name__icontains=word)
            q = q  & keyword_q
        return q

    # search by related BrainRegion
    def search_related_brain_region(self, q, userId):
        if self.related_brain_region:
            words=self.related_brain_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(relatedbrainregion__brain_region__name__icontains=word) | Q(relatedbrainregion__brain_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    # search by building SED
    def search_building_sed(self, q, userId):
        if self.building_sed:
            words=self.building_sed.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relevance_q=Q()
            for word in words:
                title_q = title_q | Q(buildsed__sed__title__icontains=word)
                description_q = description_q | Q(buildsed__sed__brief_description__icontains=word)
                narrative_q = narrative_q | Q(buildsed__sed__narrative__icontains=word)
                relevance_q = relevance_q | Q(buildsed__relevance_narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q | relevance_q
            q = q & keyword_q
        return q

    # search by testing SED
    def search_testing_sed(self, q, userId):
        if self.testing_sed:
            words=self.testing_sed.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            for word in words:
                title_q = title_q | Q(testsed__sed__title__icontains=word)
                description_q = description_q | Q(testsed__sed__brief_description__icontains=word)
                narrative_q = narrative_q | Q(testsed__sed__narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q
            q = q & keyword_q
        return q

    # search by Prediction
    def search_prediction(self, q, userId):
        if self.prediction:
            words=self.prediction.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            for word in words:
                title_q = title_q | Q(prediction__title__icontains=word)
                description_q = description_q | Q(prediction__brief_description__icontains=word)
                narrative_q = narrative_q | Q(prediction__narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q
            q = q & keyword_q
        return q

    # search by SSR
    def search_ssr(self, q, userId):
        if self.ssr:
            words=self.ssr.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            for word in words:
                title_q = title_q | Q(testsed__testsedssr__ssr__title__icontains=word) | \
                          Q(prediction__predictionssr__ssr__title__icontains=word)
                description_q = description_q | Q(testsed__testsedssr__ssr__brief_description__icontains=word) |\
                                Q(prediction__predictionssr__ssr__brief_description__icontains=word)
                narrative_q = narrative_q | Q(testsed__testsedssr__ssr__narrative__icontains=word) |\
                              Q(prediction__predictionssr__ssr__narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q
            q = q & keyword_q
        return q

    # search by related BOP
    def search_related_bop(self, q, userId):
        if self.related_bop:
            words=self.related_bop.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relevance_narrative_q=Q()
            for word in words:
                title_q = title_q | Q(relatedbop__bop__title__icontains=word)
                description_q = description_q | Q(relatedbop__bop__brief_description__icontains=word)
                narrative_q = narrative_q | Q(relatedbop__bop__narrative__icontains=word)
                relevance_narrative_q = relevance_narrative_q | Q(relatedbop__relevance_narrative__icontains=word)
            keyword_q = title_q | description_q | narrative_q | relevance_narrative_q
            q = q & keyword_q
        return q

    # search by related Model
    def search_related_model(self, q, userId):
        if self.related_model:
            words=self.related_model.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            relationship_q=Q()
            for word in words:
                title_q = title_q | Q(relatedmodel__model__title__icontains=word)
                description_q = description_q | Q(relatedmodel__model__brief_description__icontains=word)
                narrative_q = narrative_q | Q(relatedmodel__model__narrative__icontains=word)
                relationship_q = relationship_q | Q(relatedmodel__relationship__icontains=word)
            keyword_q = title_q | description_q | narrative_q | relationship_q
            q = q & keyword_q
        return q

    # search by collator
    def search_collator(self, q, userId):
        if self.collator:
            q = q & Q(collator__id=userId)
        return q

    def search_username(self, q, userId):
        if self.username:
            q = q & Q(collator__username__icontains=self.username)
        return q

    def search_first_name(self, q, userId):
        if self.first_name:
            q = q & Q(collator__first_name__icontains=self.first_name)
        return q

    def search_last_name(self, q, userId):
        if self.last_name:
            q = q & Q(collator__last_name__icontains=self.last_name)
        return q

    # search by related Literature title
    def search_related_literature_title(self, q, userId):
        if self.related_literature_title:
            words=self.related_literature_title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__title__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature author name
    def search_related_literature_author(self, q, userId):
        if self.related_literature_author:
            words=self.related_literature_author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__authors__author__first_name__icontains=word) | Q(literature__authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature minimum year
    def search_related_literature_year_min(self, q, userId):
        if self.related_literature_year_min:
            q = q & Q(literature__year__gte=self.related_literature_year_min)
        return q

    # search by related Literature maximum year
    def search_related_literature_year_max(self, q, userId):
        if self.related_literature_year_max:
            q = q & Q(literature__year__lte=self.related_literature_year_max)
        return q

    # search by related Literature annotation
    def search_related_literature_annotation(self, q, userId):
        if self.related_literature_annotation:
            words=self.related_literature_annotation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__annotation__icontains=word)
            q = q & keyword_q
        return q

    def search_public(self, q, userId):
        if self.public:
            if self.public=='True':
                q = q & Q(public=True)
            else:
                q = q & Q(public=False)
        return q

    def search_created_from(self, q, userId):
        if self.created_from:
            q = q & Q(creation_time__gte=self.created_from)
        return q

    def search_created_to(self, q, userId):
        if self.created_to:
            q = q & Q(creation_time__lte=self.created_to)
        return q

# perform a SED search
def runSEDSearch(search_data, userId):
    q=Q()
    results=None

    # create SED search
    searcher=SEDSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q, userId)

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q &= Document.get_security_q(user)
    # get results
    if q and len(q):
        results = list(SED.objects.filter(connectivitysed__cocomacconnectivitysed__isnull=True,
            brainimagingsed__bredebrainimagingsed__isnull=True).filter(q).select_related().distinct())
    else:
        results = list(SED.objects.filter(connectivitysed__cocomacconnectivitysed__isnull=True,
            brainimagingsed__bredebrainimagingsed__isnull=True).select_related().distinct())
    return results


# SED search
class SEDSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            tags_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                description_q = description_q | Q(brief_description__icontains=word)
                narrative_q = narrative_q | Q(narrative__icontains=word)
                tags_q = tags_q | Q(tags__name__icontains=word)
            keyword_q = title_q | description_q | narrative_q | tags_q
            q = q & keyword_q
        return q

    # search by title
    def search_title(self, q, userId):
        if self.title:
            words=self.title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(title__icontains=word)
            q = q  & keyword_q
        return q

    # search by description
    def search_description(self, q, userId):
        if self.description:
            words=self.description.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brief_description__icontains=word)
            q = q  & keyword_q
        return q

    # search by narrative
    def search_narrative(self, q, userId):
        if self.narrative:
            words=self.narrative.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(narrative__icontains=word)
            q = q  & keyword_q
        return q

    # search by SED type
    def search_type(self, q, userId):
        if self.type:
            q = q & Q(type=self.type)
        return q

    # search by tags
    def search_tags(self, q, userId):
        if self.tags:
            #words=self.tags.split()
            keyword_q=Q()
            for word in self.tags:
                keyword_q = keyword_q | Q(tags__name__icontains=word)
            q = q  & keyword_q
        return q

    # search by related BrainRegion
    def search_related_brain_region(self, q, userId):
        if self.related_brain_region:
            words=self.related_brain_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(relatedbrainregion__brain_region__name__icontains=word) | \
                            Q(relatedbrainregion__brain_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    # search by collator
    def search_collator(self, q, userId):
        if self.collator:
            q = q & Q(collator__id=userId)
        return q

    def search_username(self, q, userId):
        if self.username:
            q = q & Q(collator__username__icontains=self.username)
        return q

    def search_first_name(self, q, userId):
        if self.first_name:
            q = q & Q(collator__first_name__icontains=self.first_name)
        return q

    def search_last_name(self, q, userId):
        if self.last_name:
            q = q & Q(collator__last_name__icontains=self.last_name)
        return q

    # search by related Literature title
    def search_related_literature_title(self, q, userId):
        if self.related_literature_title:
            words=self.related_literature_title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__title__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature author name
    def search_related_literature_author(self, q, userId):
        if self.related_literature_author:
            words=self.related_literature_author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__authors__author__first_name__icontains=word) | Q(literature__authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature minimum year
    def search_related_literature_year_min(self, q, userId):
        if self.related_literature_year_min:
            q = q & Q(literature__year__gte=self.related_literature_year_min)
        return q

    # search by related Literature maximum year
    def search_related_literature_year_max(self, q, userId):
        if self.related_literature_year_max:
            q = q & Q(literature__year__lte=self.related_literature_year_max)
        return q

    # search by related Literature annotation
    def search_related_literature_annotation(self, q, userId):
        if self.related_literature_annotation:
            words=self.related_literature_annotation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__annotation__icontains=word)
            q = q & keyword_q
        return q

    # search by control condition
    def search_control_condition(self, q, userId):
        if self.type=='brain imaging' and self.control_condition:
            words=self.control_condition.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brainimagingsed__control_condition__icontains=word)
            q = q & keyword_q
        return q

    # search by experimental condition
    def search_experimental_condition(self, q, userId):
        if self.type=='brain imaging' and self.experimental_condition:
            words=self.experimental_condition.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brainimagingsed__experimental_condition__icontains=word)
            q = q & keyword_q
        return q

    # search by method
    def search_method(self, q, userId):
        if self.type=='brain imaging' and self.method:
            q = q & Q(brainimagingsed__method=self.method)
        return q

    # search by coordinate brain region
    def search_coordinate_brain_region(self, q, userId):
        if self.type=='brain imaging' and self.coordinate_brain_region:
            region_q=Q()
            region_q=region_q | Q(brainimagingsed__sedcoord__named_brain_region=self.coordinate_brain_region)
            region_q=region_q | Q(brainimagingsed__sedcoord__coord__brainregionvolume__brain_region__name=self.coordinate_brain_region)
            region_q=region_q | Q(brainimagingsed__sedcoord__coord__brainregionvolume__brain_region__parent_region__name=self.coordinate_brain_region)
            q = q & region_q
        return q

    # search by coordinate x
    def search_x_min(self, q, userId):
        if self.type=='brain imaging' and self.x_min:
            q = q & Q(brainimagingsed__sedcoord__coord__x__gte=self.x_min)
        return q

    # search by coordinate x
    def search_x_max(self, q, userId):
        if self.type=='brain imaging' and self.x_max:
            q = q & Q(brainimagingsed__sedcoord__coord__x__lte=self.x_max)
        return q

    # search by coordinate y
    def search_y_min(self, q, userId):
        if self.type=='brain imaging' and self.y_min:
            q = q & Q(brainimagingsed__sedcoord__coord__y__gte=self.y_min)
        return q

    # search by coordinate y
    def search_y_max(self, q, userId):
        if self.type=='brain imaging' and self.y_max:
            q = q & Q(brainimagingsed__sedcoord__coord__y__lte=self.y_max)
        return q

    # search by coordinate z
    def search_z_min(self, q, userId):
        if self.type=='brain imaging' and self.z_min:
            q = q & Q(brainimagingsed__sedcoord__coord__z__gte=self.z_min)
        return q

    # search by coordinate z
    def search_z_max(self, q, userId):
        if self.type=='brain imaging' and self.z_max:
            q = q & Q(brainimagingsed__sedcoord__coord__z__lte=self.z_max)
        return q

    def search_public(self, q, userId):
        if self.public:
            if self.public=='True':
                q = q & Q(public=True)
            else:
                q = q & Q(public=False)
        return q

    def search_created_from(self, q, userId):
        if self.created_from:
            q = q & Q(creation_time__gte=self.created_from)
        return q

    def search_created_to(self, q, userId):
        if self.created_to:
            q = q & Q(creation_time__lte=self.created_to)
        return q

    def search_cognitive_paradigm(self, q, userId):
        if self.type=='event related potential' and self.cognitive_paradigm:
            words=self.cognitive_paradigm.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__cognitive_paradigm__icontains=word)
            q &= keyword_q
        return q

    def search_sensory_modality(self, q, userId):
        if self.type=='event related potential' and self.sensory_modality:
            words=self.sensory_modality.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__sensory_modality__icontains=word)
            q &= keyword_q
        return q

    def search_response_modality(self, q, userId):
        if self.type=='event related potential' and self.response_modality:
            words=self.response_modality.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__response_modality__icontains=word)
            q &= keyword_q
        return q

    def search_erp_control_condition(self, q, userId):
        if self.type=='event related potential' and self.erp_control_condition:
            words=self.erp_control_condition.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__control_condition__icontains=word)
            q &= keyword_q
        return q

    def search_erp_experimental_condition(self, q, userId):
        if self.type=='event related potential' and self.erp_experimental_condition:
            words=self.erp_experimental_condition.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__experimental_condition__icontains=word)
            q &= keyword_q
        return q

    def search_erp_component_name(self, q, userId):
        if self.type=='event related potential' and self.erp_component_name:
            words=self.erp_component_name.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__erpcomponent__component_name__icontains=word)
            q &= keyword_q
        return q

    def search_latency_peak_min(self, q, userId):
        if self.type=='event related potential' and self.latency_peak_min:
            q = q & Q(erpsed__erpcomponent__latency_peak__gte=self.latency_peak_min)
        return q

    def search_latency_peak_max(self, q, userId):
        if self.type=='event related potential' and self.latency_peak_max:
            q = q & Q(erpsed__erpcomponent__latency_peak__lte=self.latency_peak_max)
        return q

    def search_latency_peak_type(self, q, userId):
        if self.type=='event related potential' and self.latency_peak_type:
            q = q & Q(erpsed__erpcomponent__latency_peak_type=self.latency_peak_type)
        return q

    def search_latency_onset_min(self, q, userId):
        if self.type=='event related potential' and self.latency_onset_min:
            q = q & Q(erpsed__erpcomponent__latency_onset__gte=self.latency_onset_min)
        return q

    def search_latency_onset_max(self, q, userId):
        if self.type=='event related potential' and self.latency_onset_max:
            q = q & Q(erpsed__erpcomponent__latency_onset__lte=self.latency_onset_max)
        return q

    def search_amplitude_peak_min(self, q, userId):
        if self.type=='event related potential' and self.amplitude_peak_min:
            q = q & Q(erpsed__erpcomponent__amplitude_peak__gte=self.amplitude_peak_min)
        return q

    def search_amplitude_peak_max(self, q, userId):
        if self.type=='event related potential' and self.amplitude_peak_max:
            q = q & Q(erpsed__erpcomponent__amplitude_peak__lte=self.amplitude_peak_max)
        return q

    def search_amplitude_mean_min(self, q, userId):
        if self.type=='event related potential' and self.amplitude_mean_min:
            q = q & Q(erpsed__erpcomponent__amplitude_mean__gte=self.amplitude_mean_min)
        return q

    def search_amplitude_mean_max(self, q, userId):
        if self.type=='event related potential' and self.amplitude_mean_max:
            q = q & Q(erpsed__erpcomponent__amplitude_mean__lte=self.amplitude_mean_max)
        return q

    def search_scalp_region(self, q, userId):
        if self.type=='event related potential' and self.scalp_region:
            words=self.scalp_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__erpcomponent__scalp_region__icontains=word)
            q &= keyword_q
        return q

    def search_electrode_cap(self, q, userId):
        if self.type=='event related potential' and self.electrode_cap:
            words=self.electrode_cap.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__erpcomponent__electrode_cap__icontains=word)
            q &= keyword_q
        return q

    def search_electrode_name(self, q, userId):
        if self.type=='event related potential' and self.electrode_name:
            words=self.electrode_name.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__erpcomponent__electrode_name__icontains=word)
            q &= keyword_q
        return q

    def search_source(self, q, userId):
        if self.type=='event related potential' and self.source:
            words=self.source.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(erpsed__erpcomponent__source__icontains=word)
            q &= keyword_q
        return q


# perform a SED coordinate search
def runSEDCoordSearch(seds, search_data, userId):
    sedCoords={}
    for sed in seds:
        q=Q(sed__id=sed.id)
        # create SEDCoord search
        searcher=SEDCoordSearch(search_data)
        # construct search query
        for key in search_data.iterkeys():
            # if the searcher can search by this field
            if hasattr(searcher, 'search_%s' % key):
                # add field to query
                dispatch=getattr(searcher, 'search_%s' % key)
                q=dispatch(q, userId)
        results=SEDCoord.objects.filter(q)
        sedCoords[sed.id]=results
    return sedCoords


# SEDCoord search
class SEDCoordSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by coordinate brain region
    def search_coordinate_brain_region(self, q, userId):
        if self.coordinate_brain_region:
            region_q=Q()
            region_q=region_q | Q(named_brain_region=self.coordinate_brain_region)
            region_q=region_q | Q(coord__brainregionvolume__brain_region__name=self.coordinate_brain_region)
            region_q=region_q | Q(coord__brainregionvolume__brain_region__parent_region__name=self.coordinate_brain_region)
            q = q & region_q
        return q

    # search by coordinate x
    def search_x_min(self, q, userId):
        if self.x_min:
            q = q & Q(coord__x__gte=self.x_min)
        return q

    # search by coordinate x
    def search_x_max(self, q, userId):
        if self.x_max:
            q = q & Q(coord__x__lte=self.x_max)
        return q

    # search by coordinate y
    def search_y_min(self, q, userId):
        if self.y_min:
            q = q & Q(coord__y__gte=self.y_min)
        return q

    # search by coordinate y
    def search_y_max(self, q, userId):
        if self.y_max:
            q = q & Q(coord__y__lte=self.y_max)
        return q

    # search by coordinate z
    def search_z_min(self, q, userId):
        if self.z_min:
            q = q & Q(coord__z__gte=self.z_min)
        return q

    # search by coordinate z
    def search_z_max(self, q, userId):
        if self.z_max:
            q = q & Q(coord__z__lte=self.z_max)
        return q


# perform a SSR search
def runSSRSearch(search_data, userId):
    q=Q()

    # create SSR search
    searcher=SSRSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            q=dispatch(q, userId)

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q &= Document.get_security_q(user)

    # get results
    if q and len(q):
        results = SSR.objects.filter(q).select_related().distinct()
    else:
        results = SSR.objects.all()
    return results


# SSR search
class SSRSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            description_q=Q()
            narrative_q=Q()
            tags_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                description_q = description_q | Q(brief_description__icontains=word)
                narrative_q = narrative_q | Q(narrative__icontains=word)
                tags_q = tags_q | Q(tags__name__icontains=word)
            keyword_q = title_q | description_q | narrative_q | tags_q
            q = q & keyword_q
        return q

    # search by title
    def search_title(self, q, userId):
        if self.title:
            words=self.title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(title__icontains=word)
            q = q  & keyword_q
        return q

    # search by description
    def search_description(self, q, userId):
        if self.description:
            words=self.description.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(brief_description__icontains=word)
            q = q  & keyword_q
        return q

    # search by narrative
    def search_narrative(self, q, userId):
        if self.narrative:
            words=self.narrative.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(narrative__icontains=word)
            q = q  & keyword_q
        return q

    # search by tags
    def search_tags(self, q, userId):
        if self.tags:
            #words=self.tags.split()
            keyword_q=Q()
            for word in self.tags:
                keyword_q = keyword_q | Q(tags__name__icontains=word)
            q = q  & keyword_q
        return q

    # search by related BrainRegion
    def search_related_brain_region(self, q, userId):
        if self.related_brain_region:
            words=self.related_brain_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(relatedbrainregion__brain_region__name__icontains=word) | Q(relatedbrainregion__brain_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    # search by collator
    def search_collator(self, q, userId):
        if self.collator:
            q = q & Q(collator__id=userId)
        return q

    def search_username(self, q, userId):
        if self.username:
            q = q & Q(collator__username__icontains=self.username)
        return q

    def search_first_name(self, q, userId):
        if self.first_name:
            q = q & Q(collator__first_name__icontains=self.first_name)
        return q

    def search_last_name(self, q, userId):
        if self.last_name:
            q = q & Q(collator__last_name__icontains=self.last_name)
        return q

    # search by related Literature title
    def search_related_literature_title(self, q, userId):
        if self.related_literature_title:
            words=self.related_literature_title.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__title__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature author name
    def search_related_literature_author(self, q, userId):
        if self.related_literature_author:
            words=self.related_literature_author.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__authors__author__first_name__icontains=word) | Q(literature__authors__author__last_name__icontains=word)
            q = q & keyword_q
        return q

    # search by related Literature minimum year
    def search_related_literature_year_min(self, q, userId):
        if self.related_literature_year_min:
            q = q & Q(literature__year__gte=self.related_literature_year_min)
        return q

    # search by related Literature maximum year
    def search_related_literature_year_max(self, q, userId):
        if self.related_literature_year_max:
            q = q & Q(literature__year__lte=self.related_literature_year_max)
        return q

    # search by related Literature annotation
    def search_related_literature_annotation(self, q, userId):
        if self.related_literature_annotation:
            words=self.related_literature_annotation.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(literature__annotation__icontains=word)
            q = q & keyword_q
        return q

    def search_public(self, q, userId):
        if self.public:
            if self.public=='True':
                q = q & Q(public=True)
            else:
                q = q & Q(public=False)
        return q

    def search_created_from(self, q, userId):
        if self.created_from:
            q = q & Q(creation_time__gte=self.created_from)
        return q

    def search_created_to(self, q, userId):
        if self.created_to:
            q = q & Q(creation_time__lte=self.created_to)
        return q