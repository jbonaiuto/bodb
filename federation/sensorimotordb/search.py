import operator
from django.db.models import Q
from bodb.models import Document, SensoriMotorDBNeurophysiologySED
from bodb.search.document import DocumentWithLiteratureSearch
from registration.models import User

def runSensorimotorDBSearch(search_data, userId):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create SED search
    searcher=LocalSensorimotorDBSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            filters.append(dispatch(userId))

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q = reduce(op,filters) & Document.get_security_q(user)

    # get results
    if q and len(q):
        results=list(SensoriMotorDBNeurophysiologySED.objects.filter(q).select_related('collator','region__nomenclature').distinct())
    else:
        results=list(SensoriMotorDBNeurophysiologySED.objects.all().select_related('collator','region__nomenclature').distinct())

    return results

class LocalSensorimotorDBSearch(DocumentWithLiteratureSearch):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_recorded_region(self, userId):
        if self.recorded_region:
            words=self.recorded_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(region__name__icontains=word) |\
                            Q(region__abbreviation__icontains=word)
            return keyword_q
        return Q()

    def search_recorded_region_nomenclature(self, userId):
        if self.recorded_region_nomenclature:
            words=self.recorded_region_nomenclature.split()
            keyword_filters=[Q() for word in words]
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(region__nomenclature__name__icontains=word) |\
                            Q(region__nomenclature__lit__title__icontains=word) |\
                            Q(region__nomenclature__lit__authors__author__first_name__icontains=word) |\
                            Q(region__nomenclature__lit__authors__author__last_name__icontains=word)
            return keyword_q
        return Q()
