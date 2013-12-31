import re
import urllib
from xml.dom import minidom
from pyexpat import ExpatError
from django.db.models import Q
from bodb.models import RelatedBrainRegion, CoCoMacBrainRegion, CoCoMacConnectivitySED, Document
from cocomac.import_data import addNomenclature
from registration.models import User

def runCoCoMacSearch(search_data, userId):
    searchString=""
    searcher=CoCoMacSearcher(search_data)
    results=[]
    search_local=False
    if hasattr(searcher,'type') and (searcher.type=='' or searcher.type=='connectivity'):
        if hasattr(searcher,'search_cocomac') and searcher.search_cocomac:
            print('Trying to search CoCoMac')
            # construct search query
            for key in search_data.iterkeys():
                # if the searcher can search by this field
                if hasattr(searcher, 'search_%s' % key):
                    # add field to query
                    dispatch=getattr(searcher, 'search_%s' % key)
                    searchString=dispatch(searchString)
            cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=XML_Browser&SearchString="
            if len(searchString):
                cocomac_url+=searchString+" AND"
            cocomac_url+=" NOT ('0') [Density]"
            cocomac_url+="&Details=&SortOrder=asc&SortBy=SOURCEMAP&Dispmax=32767&ItemsPerPage=32767"

            # Parse cocomac results
            try:
                data=download(cocomac_url)
                doc = minidom.parseString(data)
                processed_nodes=doc.getElementsByTagName('ProcessedConnectivityData')

                for processed_node in processed_nodes:
                    projection_nodes=processed_node.getElementsByTagName('PrimaryProjection')

                    for projection_node in projection_nodes:

                        # Get target region - import nomenclature if not found
                        targetSiteNode=projection_node.getElementsByTagName('TargetSite')[0]
                        target_id=targetSiteNode.getElementsByTagName('ID_BrainSite')[0].firstChild.data
                        if not CoCoMacBrainRegion.objects.filter(cocomac_id=target_id):
                            addNomenclature(target_id.split('-',1)[0])

                        # Get source region - import nomenclature if not found
                        sourceSiteNode=projection_node.getElementsByTagName('SourceSite')[0]
                        source_id=sourceSiteNode.getElementsByTagName('ID_BrainSite')[0].firstChild.data
                        if not CoCoMacBrainRegion.objects.filter(cocomac_id=source_id):
                            addNomenclature(source_id.split('-',1)[0])

                        if CoCoMacBrainRegion.objects.filter(cocomac_id=target_id).count() and\
                           CoCoMacBrainRegion.objects.filter(cocomac_id=source_id).count():
                            target_region=CoCoMacBrainRegion.objects.get(cocomac_id=target_id).brain_region
                            source_region=CoCoMacBrainRegion.objects.get(cocomac_id=source_id).brain_region

                            # Look for connectivity SEDs that are already imported
                            already_imported_seds=CoCoMacConnectivitySED.objects.filter(source_region=source_region,
                                target_region=target_region).distinct()

                            # Import connectivity SEDs
                            if not already_imported_seds.count() :
                                sed=importConnectivitySED(source_region, target_region)
                                results.append(sed)
                            else:
                                for sed in already_imported_seds:
                                    results.append(sed)

            except ExpatError as inst:
                print type(inst)     # the exception instance
                print inst.args      # arguments stored in .args
                print inst           # __str__ allows args to printed directly:
                search_local=True
            except IOError:
                print('Error connecting to cocomac')
                search_local=True
        else:
            search_local=True

    if search_local:
        print('Searching locally')
        q=Q()

        # create SED search
        searcher=LocalCoCoMacSearcher(search_data)

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
            results = list(CoCoMacConnectivitySED.objects.filter(q).select_related().distinct())
        else:
            results = list(CoCoMacConnectivitySED.objects.all().select_related().distinct())
        return results

    return results



def importConnectivitySED(source_region, target_region):
    connSED=CoCoMacConnectivitySED(type='connectivity', source_region=source_region, target_region=target_region)
    connSED.collator=User.objects.get(username='jbonaiuto')
    connSED.public=1
    connSED.title='Projection from '+source_region.__unicode__()+' to '+target_region.__unicode__()
    connSED.brief_description='CoCoMac describes a projection from the region '+source_region.__unicode__()+' ('+source_region.nomenclature.name
    if source_region.nomenclature.version:
        connSED.brief_description+=', '+source_region.nomenclature.version
    connSED.brief_description+=') to the region '+target_region.__unicode__()+' ('+target_region.nomenclature.name
    if target_region.nomenclature.version:
        connSED.brief_description+=', '+target_region.nomenclature.version
    connSED.brief_description+=')'
    connSED.save()
    related_source=RelatedBrainRegion(document=connSED, brain_region=source_region,relationship='Source of the projection')
    related_source.save()
    related_target=RelatedBrainRegion(document=connSED, brain_region=target_region,relationship='Target of the projection')
    related_target.save()
    return connSED


class CoCoMacSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_source_region(self, searchString):
        if self.source_region:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="('"+unicode(self.source_region).encode('latin1','xmlcharrefreplace')+"') [SourceSite]"
        return searchString

    def search_source_region_nomenclature(self, searchString):
        if self.source_region_nomenclature:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="('"+unicode(self.source_region_nomenclature).encode('latin1','xmlcharrefreplace')+"')[SourceMap]"
        return searchString

    def search_target_region(self, searchString):
        if self.target_region:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="('"+unicode(self.target_region).encode('latin1','xmlcharrefreplace')+"') [TargetSite]"
        return searchString

    def search_target_region_nomenclature(self, searchString):
        if self.target_region_nomenclature:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="('"+unicode(self.target_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [TargetMap]"
        return searchString

    def search_connection_region(self, searchString):
        if self.connection_region:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="(('"+unicode(self.connection_region).encode('latin1','xmlcharrefreplace')+"') [SourceSite] OR ('"+unicode(self.connection_region).encode('latin1','xmlcharrefreplace')+"') [TargetSite]"
        return searchString

    def search_connection_region_nomenclature(self, searchString):
        if self.connection_region_nomenclature:
            if len(searchString)>0:
                searchString+=" AND "
            searchString+="(('"+unicode(self.connection_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [SourceMap] OR ('"+unicode(self.connection_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [TargetMap]"
        return searchString

    def search_related_brain_region(self, searchString):
        if self.related_brain_region:
            return self.search_connection_region(self, searchString)
        return searchString


class LocalCoCoMacSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by title, description, narrative, or tags
    def search_keywords(self, q, userId):
        if self.keywords:
            words=self.keywords.split()
            title_q=Q()
            description_q=Q()
            source_q=Q()
            target_q=Q()
            source_nom_q=Q()
            target_nom_q=Q()
            for word in words:
                title_q = title_q | Q(title__icontains=word)
                description_q = description_q | Q(brief_description__icontains=word)
                source_q=Q(source_region__name__icontains=word) |\
                         Q(source_region__abbreviation__icontains=word)
                target_q=Q(target_region__name__icontains=word) |\
                         Q(target_region__abbreviation__icontains=word)
                source_nom_q=Q(source_region__nomenclature__name__icontains=word)
                target_nom_q=Q(target_region__nomenclature__name__icontains=word)
            keyword_q = title_q | description_q | source_q | target_q | source_nom_q | target_nom_q
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

    def search_source_region(self, q, userId):
        if self.source_region:
            words=self.source_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__name__icontains=word) | \
                            Q(source_region__abbreviation__icontains=word)
            q &= keyword_q
        return q

    def search_source_region_nomenclature(self, q, userId):
        if self.source_region_nomenclature:
            words=self.source_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__nomenclature__name__icontains=word)
            q &= keyword_q
        return q

    def search_target_region(self, q, userId):
        if self.target_region:
            words=self.target_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(target_region__name__icontains=word) |\
                            Q(target_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    def search_target_region_nomenclature(self, q, userId):
        if self.target_region_nomenclature:
            words=self.target_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(target_region__nomenclature__name__icontains=word)
            q = q & keyword_q
        return q

    def search_connection_region(self, q, userId):
        if self.connection_region:
            words=self.connection_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__name__icontains=word) | \
                            Q(source_region__abbreviation__icontains=word) | Q(target_region__name__icontains=word) | \
                            Q(target_region__abbreviation__icontains=word)
            q = q & keyword_q
        return q

    def search_connection_region_nomenclature(self, q, userId):
        if self.connection_region_nomenclature:
            words=self.connection_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__nomenclature__name__icontains=word) |\
                            Q(target_region__nomenclature__name__icontains=word)
            q &= keyword_q
        return q

def download(url):
    """Copy the contents of a file from a given URL
    to a local file.
    """
    webFile = urllib.urlopen(url)
    data=webFile.read()
    data=re.sub('UTF-8','iso-8859-1',data)
    data=re.sub(' & ', ' &amp; ',data)
    data=re.sub('>< ', '> ',data)
    data=re.sub('><(\d)','>',data )
    data=re.sub('&qu<','<',data)
    data=re.sub('<HK>','',data)
    data=re.sub('<BR>','',data)
    webFile.close()
    return data