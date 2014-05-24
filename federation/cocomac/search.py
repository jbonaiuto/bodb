import re
import urllib
import json
import urllib2
from xml.dom import minidom
from pyexpat import ExpatError
from django.db.models import Q
import operator
from bodb.models import RelatedBrainRegion, CoCoMacBrainRegion, CoCoMacConnectivitySED, Document
from bodb.search.sed import SEDSearch
from federation.cocomac.import_data import addNomenclature
from federation.cocomac.import_data2 import addNomenclature2, perform_query
from registration.models import User
from taggit.utils import parse_tags

def runCoCoMacSearch2(search_data, userId):
    results=[]
    search_local=False
    if 'type' not in search_data or search_data['type']=='connectivity':
        if 'search_cocomac' in search_data and search_data['search_cocomac']:
            print('Trying to search CoCoMac2')
            try:
                origin_search_string=''
                terminal_search_string=''
                if 'source_region' in search_data and len(search_data['source_region']):
                    source_words=parse_tags(search_data['source_region'])
                    source_sql=' OR '.join(['(BrainSite LIKE $region_%d OR Acronym LIKE $region_%d)' % (x,x) for x in range(len(source_words))])
                    sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE %s' % source_sql
                    query_params={}
                    for idx,source_word in enumerate(source_words):
                        query_params['region_%d' % idx]=source_word
                    result=perform_query(sql, query_params)
                    brainsite_idx=result['fields'].index('BrainSite')
                    origin_search_string=','.join([x[brainsite_idx] for x in result['data'].values()])
                if 'target_region' in search_data and len(search_data['target_region']):
                    target_words=parse_tags(search_data['target_region'])
                    target_sql=' OR '.join(['(BrainSite LIKE $region_%d OR Acronym LIKE $region_%d)' % (x,x) for x in range(len(target_words))])
                    sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE %s' % target_sql
                    query_params={}
                    for idx,target_word in enumerate(target_words):
                        query_params['region_%d' % idx]=target_word
                    result=perform_query(sql, query_params)
                    brainsite_idx=result['fields'].index('BrainSite')
                    terminal_search_string=','.join([x[brainsite_idx] for x in result['data'].values()])

                searchDict={
                    'axonOriginList':origin_search_string,
                    'axonTerminalList': terminal_search_string,
                    'includeLargeInjections': '0',
                    'useAM': '1',
                    'useSORT': '0',
                    'output': 'temptable',
                    'fibercourse': 'I?'
                }
                query_req = urllib2.Request('http://cocomac.g-node.org/cocomac2/services/axonal_projections.php', urllib.urlencode( searchDict ) )
                query_response = urllib2.urlopen(query_req)
                temp_table=query_response.read()

                sql='SELECT * FROM %s' % temp_table
                result=perform_query(sql,{})
                axon_origin_idx=result['fields'].index('axon_origin')
                axon_terminal_idx=result['fields'].index('axon_terminal')
                axon_origins=[x[axon_origin_idx] for x in result['data'].values()]
                axon_terminals=[x[axon_terminal_idx] for x in result['data'].values()]
                region_id_list=[]
                for axon_origin,axon_terminal in zip(axon_origins,axon_terminals):
                    if not axon_origin in region_id_list:
                        region_id_list.append(axon_origin)
                    if not axon_terminal in region_id_list:
                        region_id_list.append(axon_terminal)

                region_map={}
                remaining_regions=region_id_list
                while len(remaining_regions)>0:
                    region_block=remaining_regions[-10:]
                    sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite FROM BrainMaps_BrainSites WHERE BrainMaps_BrainSites.ID IN (%s)' % ','.join(region_block)
                    result=perform_query(sql, {})
                    brainregion_id_idx=result['fields'].index('ID')
                    brainregion_name_idx=result['fields'].index('BrainSite')
                    for x in result['data'].values():
                        region_map[x[brainregion_id_idx]]=x[brainregion_name_idx]
                    remaining_regions=remaining_regions[:-10]

                    if not CoCoMacBrainRegion.objects.filter(cocomac_id=x[brainregion_name_idx]):
                        addNomenclature2(x[brainregion_name_idx].split('-',1)[0])

                for axon_origin,axon_terminal in zip(axon_origins,axon_terminals):
                    if CoCoMacBrainRegion.objects.filter(cocomac_id=region_map[axon_origin]).count() and\
                       CoCoMacBrainRegion.objects.filter(cocomac_id=region_map[axon_terminal]).count():
                        target_region=CoCoMacBrainRegion.objects.get(cocomac_id=region_map[axon_terminal]).brain_region
                        source_region=CoCoMacBrainRegion.objects.get(cocomac_id=region_map[axon_origin]).brain_region

                        # Look for connectivity SEDs that are already imported
                        already_imported_seds=CoCoMacConnectivitySED.objects.filter(source_region=source_region,
                            target_region=target_region).distinct()

                        # Import connectivity SEDs
                        if not already_imported_seds.count() :
                            sed=importConnectivitySED(source_region, target_region)
                            if not sed in results:
                                results.append(sed)
                        else:
                            for sed in already_imported_seds:
                                if not sed in results:
                                    results.append(sed)
            except:
                print('Error connecting to cocomac')
                search_local=True
        else:
            search_local=True

    if search_local:
        print('Searching locally')
        filters=[]

        op=operator.or_
        if search_data['search_options']=='all':
            op=operator.and_

        # create SED search
        searcher=LocalCoCoMacSearch(search_data)

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
            return list(CoCoMacConnectivitySED.objects.filter(q).select_related().distinct())
        return list(CoCoMacConnectivitySED.objects.all().select_related().distinct())

    return results


def runCoCoMacSearch(search_data, userId):
    searcher=CoCoMacSearch(search_data)
    results=[]
    search_local=False
    if not hasattr(searcher,'type') or (hasattr(searcher,'type') and searcher.type=='connectivity'):
        if hasattr(searcher,'search_cocomac') and searcher.search_cocomac:
            print('Trying to search CoCoMac')
            searchStrings=[]
            # construct search query
            for key in search_data.iterkeys():
                # if the searcher can search by this field
                if hasattr(searcher, 'search_%s' % key):
                    # add field to query
                    dispatch=getattr(searcher, 'search_%s' % key)
                    searchStrings.append(dispatch())
            cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=XML_Browser&SearchString="
            if len(searchStrings):
                if search_data['search_options']=='all':
                    cocomac_url+=" AND".join(searchStrings)
                else:
                    cocomac_url+=" OR".join(searchStrings)
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
        filters=[]

        op=operator.or_
        if search_data['search_options']=='all':
            op=operator.and_

        # create SED search
        searcher=LocalCoCoMacSearch(search_data)

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
            return list(CoCoMacConnectivitySED.objects.filter(q).select_related().distinct())
        return list(CoCoMacConnectivitySED.objects.all().select_related().distinct())

    return results



def importConnectivitySED(source_region, target_region):
    connSED=CoCoMacConnectivitySED(type='connectivity', source_region=source_region, target_region=target_region)
    connSED.collator=User.objects.get(username='jbonaiuto')
    connSED.last_modified_by=User.objects.get(username='jbonaiuto')
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


class CoCoMacSearch():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_source_region(self):
        if self.source_region:
            return "('"+unicode(self.source_region).encode('latin1','xmlcharrefreplace')+"') [SourceSite]"
        return ""

    def search_source_region_nomenclature(self):
        if self.source_region_nomenclature:
            return "('"+unicode(self.source_region_nomenclature).encode('latin1','xmlcharrefreplace')+"')[SourceMap]"
        return ""

    def search_target_region(self):
        if self.target_region:
            return "('"+unicode(self.target_region).encode('latin1','xmlcharrefreplace')+"') [TargetSite]"
        return ""

    def search_target_region_nomenclature(self):
        if self.target_region_nomenclature:
            return "('"+unicode(self.target_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [TargetMap]"
        return ""

    def search_connection_region(self):
        if self.connection_region:
            return "(('"+unicode(self.connection_region).encode('latin1','xmlcharrefreplace')+"') [SourceSite] OR ('"+unicode(self.connection_region).encode('latin1','xmlcharrefreplace')+"') [TargetSite]"
        return ""

    def search_connection_region_nomenclature(self):
        if self.connection_region_nomenclature:
            return "(('"+unicode(self.connection_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [SourceMap] OR ('"+unicode(self.connection_region_nomenclature).encode('latin1','xmlcharrefreplace')+"') [TargetMap]"
        return ""

    def search_related_brain_region(self):
        if self.related_brain_region:
            return self.search_connection_region(self)
        return ""


class LocalCoCoMacSearch(SEDSearch):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_source_region(self, userId):
        if self.source_region:
            words=self.source_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__name__icontains=word) | \
                            Q(source_region__abbreviation__icontains=word)
            return keyword_q
        return Q()

    def search_source_region_nomenclature(self, userId):
        if self.source_region_nomenclature:
            words=self.source_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__nomenclature__name__icontains=word)
            return keyword_q
        return Q()

    def search_target_region(self, userId):
        if self.target_region:
            words=self.target_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(target_region__name__icontains=word) |\
                            Q(target_region__abbreviation__icontains=word)
            return keyword_q
        return Q()

    def search_target_region_nomenclature(self, userId):
        if self.target_region_nomenclature:
            words=self.target_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(target_region__nomenclature__name__icontains=word)
            return keyword_q
        return Q()

    def search_connection_region(self, userId):
        if self.connection_region:
            words=self.connection_region.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__name__icontains=word) | \
                            Q(source_region__abbreviation__icontains=word) | Q(target_region__name__icontains=word) | \
                            Q(target_region__abbreviation__icontains=word)
            return keyword_q
        return Q()

    def search_connection_region_nomenclature(self, userId):
        if self.connection_region_nomenclature:
            words=self.connection_region_nomenclature.split()
            keyword_q=Q()
            for word in words:
                keyword_q = keyword_q | Q(source_region__nomenclature__name__icontains=word) |\
                            Q(target_region__nomenclature__name__icontains=word)
            return keyword_q
        return Q()

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


