from django.db.models import Q
import operator
from taggit.utils import parse_tags

class DocumentSearch(object):
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
            description_filters=[Q(brief_description__icontains=word) for word in words]
            narrative_filters=[Q(narrative__icontains=word) for word in words]
            tags_filters=[Q(tags__name__icontains=word)for word in words]
            return reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters) | \
                   reduce(op,tags_filters)
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
            keyword_filters=[Q(brief_description__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by narrative
    def search_narrative(self, userId):
        if self.narrative:
            op=operator.or_
            if self.narrative_options=='all':
                op=operator.and_
            words=parse_tags(self.narrative)
            keyword_filters=[Q(narrative__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by tags
    def search_tags(self, userId):
        if self.tags:
            op=operator.or_
            if self.tags_options=='all':
                op=operator.and_
            keyword_filters=[Q(tags__name__icontains=word) for word in self.tags]
            return reduce(op,keyword_filters)
        return Q()

    # search by related brain region
    def search_related_brain_region(self, userId):
        if self.related_brain_region:
            op=operator.or_
            if self.related_brain_region_options=='all':
                op=operator.and_
            words=parse_tags(self.related_brain_region)
            keyword_filters=[Q(Q(relatedbrainregion__brain_region__name__icontains=word) |
                               Q(relatedbrainregion__brain_region__abbreviation__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related BOP
    def search_related_bop(self, userId):
        if self.related_bop:
            op=operator.or_
            if self.related_bop_options=='all':
                op=operator.and_
            words=parse_tags(self.related_bop)
            title_filters=[Q(related_bop_document__bop__title__icontains=word) for word in words]
            description_filters=[Q(related_bop_document__bop__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_bop_document__bop__narrative__icontains=word) for word in words]
            relevance_narrative_filters=[Q(related_bop_document__relevance_narrative__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters) |\
                        reduce(op,relevance_narrative_filters)
            return keyword_q
        return Q()

    # search by related Model
    def search_related_model(self, userId):
        if self.related_model:
            op=operator.or_
            if self.related_model_options=='all':
                op=operator.and_
            words=parse_tags(self.related_model)
            title_filters=[Q(related_model_document__model__title__icontains=word) for word in words]
            description_filters=[Q(related_model_document__model__brief_description__icontains=word) for word in words]
            narrative_filters=[Q(related_model_document__model__narrative__icontains=word) for word in words]
            relationship_filters=[Q(related_model_document__relationship__icontains=word) for word in words]
            keyword_q = reduce(op,title_filters) | reduce(op,description_filters) | reduce(op,narrative_filters) |\
                        reduce(op,relationship_filters)
            return keyword_q
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
            if self.public=='True':
                return Q(public=True)
            else:
                return Q(public=False)
        return Q()

    def search_created_from(self, userId):
        if self.created_from:
            return Q(creation_time__gte=self.created_from)
        return Q()

    def search_created_to(self, userId):
        if self.created_to:
            return Q(creation_time__lte=self.created_to)
        return Q()


class DocumentWithLiteratureSearch(DocumentSearch):
    # search by related Literature title
    def search_related_literature_title(self, userId):
        if self.related_literature_title:
            op=operator.or_
            if self.related_literature_title_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_title)
            keyword_filters=[Q(literature__title__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related Literature author name
    def search_related_literature_author(self, userId):
        if self.related_literature_author:
            op=operator.or_
            if self.related_literature_author_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_author)
            keyword_filters=[Q(Q(literature__authors__author__first_name__icontains=word) |
                               Q(literature__authors__author__last_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by related Literature minimum year
    def search_related_literature_year_min(self, userId):
        if self.related_literature_year_min:
            return Q(literature__year__gte=self.related_literature_year_min)
        return Q()

    # search by related Literature maximum year
    def search_related_literature_year_max(self, userId):
        if self.related_literature_year_max:
            return Q(literature__year__lte=self.related_literature_year_max)
        return Q()

    # search by related Literature annotation
    def search_related_literature_annotation(self, userId):
        if self.related_literature_annotation:
            op=operator.or_
            if self.related_literature_annotation_options=='all':
                op=operator.and_
            words=parse_tags(self.related_literature_annotation)
            keyword_filters=[Q(literature__annotation__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

