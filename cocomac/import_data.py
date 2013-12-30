import os
import re
import urllib
from xml.dom import minidom
from pyexpat import ExpatError
from bodb.models import BrainRegion, RelatedBrainRegion, Literature, Journal, Book, Author, LiteratureAuthor, Nomenclature, Species, CoCoMacBrainRegion, Chapter, CoCoMacConnectivitySED
from registration.models import User

regions_checked=[]

def importAll():
    importNomenclatures()
    importConnections()


def importConnections():
    fname='cocomac/data/lit_list.xml'
    if not os.path.isfile(fname):
        download('http://cocomac.org/URLSearch.asp?Search=Literature&OutputType=XML_Browser&User=jbonaiuto&Password=4uhk48s3&SearchString=(\'\') [KEYWORDS]&SortOrder=DESC&SortBy=YEAR&Dispmax=32767&ItemsPerPage=32767', fname)
    doc = minidom.parse(fname)
    exportNode=doc.firstChild

    bibList=exportNode.getElementsByTagName('BibliographicData')

    for bibData in bibList:
        id=bibData.getElementsByTagName('ID')[0].firstChild.data
        print('importing connections from '+id)
        fname='cocomac/data/bibData/bib_'+unicode(id).encode('latin1','xmlcharrefreplace')+'.xml'

        if not os.path.isfile(fname):
            try:
                download('http://cocomac.org/URLSearch.asp?Search=Literature&OutputType=XML_BROWSER&User=jbonaiuto&Password=4uhk48s3&SearchString=(\''+ unicode(id).encode('latin1','xmlcharrefreplace')+'\') [LITID]&SortOrder=DESC&SortBy=YEAR&DispMax=32767&ItemsPerPage=32767&Details=BRAINSITES,METHODS,INJECTIONS,LABELLEDSITES', fname)
            except UnicodeError:
                print('couldnt download '+id)
                return
            try:
                doc=minidom.parse(fname)
                brain_sites=doc.getElementsByTagName('BrainSite')
                for brain_site_node in brain_sites:
                    importBrainRegionConnections(brain_site_node)
            except ExpatError:
                print('*** error parsing XML ***')

def importBrainRegionConnections(region_node):

    id=region_node.getElementsByTagName('ID_BrainSite')[0].firstChild.data
    #try:
    if not id in regions_checked:
        importEfferentProjections(id)
        importAfferentProjections(id)
        regions_checked.append(id)

        #except ExpatError:
        #    print('*** error parsing XML ***')

def importEfferentProjections(id):
    print('importing efferent projections of '+id)
    if BrainRegion.objects.get(cocomac_region__cocomac_id=id):
        source_region=BrainRegion.objects.get(cocomac_region__cocomac_id=id)
        source_id=id.split('-',1)

        fname='cocomac/data/efferent.xml'

        # Get projections from this brain region
        cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=XML_Browser&SearchString="
        cocomac_url+="(\\'"+unicode(source_id[0]).encode('latin1','xmlcharrefreplace')+"\\')[SourceMap]"
        cocomac_url+=" AND "
        cocomac_url+="(\\'"+unicode(source_id[1]).encode('latin1','xmlcharrefreplace')+"\\') [SourceSite]"
        cocomac_url+=" AND NOT (\\'0\\') [Density]"
        cocomac_url+="&Details=&SortOrder=asc&SortBy=SOURCEMAP&Dispmax=32767&ItemsPerPage=32767"

        download(cocomac_url.replace("\\'","'"), fname)

        try:
            doc = minidom.parse(fname)
        except ExpatError:
            print('Error parsing efferent projections of '+id)
            return

        processed_nodes=doc.getElementsByTagName('ProcessedConnectivityData')
        for processed_node in processed_nodes:
            projection_nodes=processed_node.getElementsByTagName('PrimaryProjection')
            for projection_node in projection_nodes:
                imporEfferentProjection(projection_node, source_region)

def imporEfferentProjection(projection_node, source_region):
    targetSiteNode=projection_node.getElementsByTagName('TargetSite')[0]
    target_id=targetSiteNode.getElementsByTagName('ID_BrainSite')[0].firstChild.data
    if not BrainRegion.objects.filter(cocomac_region__cocomac_id=target_id):
        addNomenclature(target_id.split('-',1)[0])
    if BrainRegion.objects.filter(cocomac_region__cocomac_id=target_id):
        target_region=BrainRegion.objects.get(cocomac_region__cocomac_id=target_id)
        if not CoCoMacConnectivitySED.objects.filter(source_region=source_region, target_region=target_region):
            print('connection from '+source_region.__unicode__()+' to '+target_region.__unicode__())
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

    else:
        print('couldnt find '+target_id)

def importAfferentProjections(id):
    print('importing afferent projections of '+id)
    if BrainRegion.objects.filter(cocomac_region__cocomac_id=id):
        target_region=BrainRegion.objects.get(cocomac_region__cocomac_id=id)
        target_id=id.split('-',1)

        fname='cocomac/data/afferent.xml'
        # Get projections from this brain region
        cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=XML_Browser&SearchString="
        cocomac_url+="(\\'"+ unicode(target_id[0]).encode('latin1','xmlcharrefreplace')+"\\')[TargetMap]"
        cocomac_url+=" AND "
        cocomac_url+="(\\'"+ unicode(target_id[1]).encode('latin1','xmlcharrefreplace')+"\\') [TargetSite]"
        cocomac_url+=" AND NOT (\\'0\\') [Density]"
        cocomac_url+="&Details=&SortOrder=asc&SortBy=SOURCEMAP&Dispmax=32767&ItemsPerPage=32767"
        download(cocomac_url.replace("\\'","'"), fname)


        try:
            doc = minidom.parse(fname)
        except ExpatError:
            print('Error parsing afferent projections of '+id)
            return

        processed_nodes=doc.getElementsByTagName('ProcessedConnectivityData')
        for processed_node in processed_nodes:
            projection_nodes=processed_node.getElementsByTagName('PrimaryProjection')
            for projection_node in projection_nodes:
                importAfferentProjection(projection_node, target_region)

def importAfferentProjection(projection_node, target_region):
    sourceSiteNode=projection_node.getElementsByTagName('SourceSite')[0]
    source_id=sourceSiteNode.getElementsByTagName('ID_BrainSite')[0].firstChild.data
    if not BrainRegion.objects.filter(cocomac_region__cocomac_id=source_id):
        addNomenclature(source_id.split('-',1)[0])
    if BrainRegion.objects.filter(cocomac_region__cocomac_id=source_id):
        source_region=BrainRegion.objects.get(cocomac_region__cocomac_id=source_id)
        if not CoCoMacConnectivitySED.objects.filter(source_region=source_region, target_region=target_region):
            print('connection from '+source_region.__unicode__()+' to '+target_region.__unicode__())
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

    else:
        print('couldnt find '+source_id)

def importNomenclatures():
    fname='cocomac/data/lit_list.xml'
    if not os.path.isfile(fname):
        download('http://cocomac.org/URLSearch.asp?Search=Literature&OutputType=XML_Browser&User=jbonaiuto&Password=4uhk48s3&SearchString=(\'\') [KEYWORDS]&SortOrder=DESC&SortBy=YEAR&Dispmax=32767&ItemsPerPage=32767', fname)
    doc = minidom.parse(fname)

    exportNode=doc.firstChild

    # create list of nomenclatures
    nomenclatures=[]

    # add each nomenclature's brain regions
    bibList=exportNode.getElementsByTagName('BibliographicData')
    for bibData in bibList:
        id=bibData.getElementsByTagName('ID')[0].firstChild.data
        nomenclatures.append(addNomenclature(id))


def addNomenclature(id):

    print('adding '+id)

    fname='cocomac/data/bibData/bib_'+ unicode(id).encode('latin1','xmlcharrefreplace')+'.xml'

    if not os.path.isfile(fname):
        try:
            download('http://cocomac.org/URLSearch.asp?Search=Literature&OutputType=XML_BROWSER&User=jbonaiuto&Password=4uhk48s3&SearchString=(\''+ unicode(id).encode('latin1','xmlcharrefreplace')+'\') [LITID]&SortOrder=DESC&SortBy=YEAR&DispMax=32767&ItemsPerPage=32767&Details=BRAINSITES,METHODS,INJECTIONS,LABELLEDSITES', fname)
        except UnicodeError:
            print('couldnt download '+id)
            return

    try:
        doc=minidom.parse(fname)

        exportNode=doc.firstChild

        # get nomenclature brain region list
        mapData=exportNode.getElementsByTagName('MapData')[0]
        regionNodeList=mapData.getElementsByTagName('BrainSite')

        # only add nomenclature if it defines regions
        if regionNodeList:
            # Get literature data
            refData=exportNode.getElementsByTagName('BibliographicData')[0]

            title=refData.getElementsByTagName('Title')[0].firstChild.data
            year=refData.getElementsByTagName('Year')[0].firstChild.data
            if year=='?':
                year=''

            literatureRecs=Literature.objects.filter(title__iexact=title, year=year)
            if literatureRecs:
                literature=literatureRecs[0]
            else:
                literature=None
                if refData.getElementsByTagName('Journal'):
                    journalNode=refData.getElementsByTagName('Journal')[0]
                    journalName=journalNode.getElementsByTagName('JournalName')[0].firstChild.data

                    pages=journalNode.getElementsByTagName('Pages')[0].firstChild.data
                    literature=Journal(title=title, year=int(year), journal_name=journalName, pages=pages,
                        collator=User.objects.get(username='jbonaiuto'))
                    vol=journalNode.getElementsByTagName('Volume')[0].firstChild.data
                    lParenIdx=vol.find('(')
                    if lParenIdx>-1:
                        rParenIdx=vol.find(')')
                        issue=vol[lParenIdx+1:rParenIdx]
                        literature.issue=issue
                        vol=vol[:lParenIdx]
                    literature.volume=vol


                elif refData.getElementsByTagName('Book'):
                    bookNode=refData.getElementsByTagName('Book')[0]
                    publisher=bookNode.getElementsByTagName('Publisher')[0].firstChild.data
                    location=bookNode.getElementsByTagName('Place')[0].firstChild.data
                    literature=Book(title=title, year=int(year), publisher=publisher, location=location,
                        collator=User.objects.get(username='jbonaiuto'))

                elif refData.getElementsByTagName('Chapter'):
                    chapterNode=refData.getElementsByTagName('Chapter')[0]
                    editors=chapterNode.getElementsByTagName('Editors')[0].firstChild.data
                    bookTitle=chapterNode.getElementsByTagName('BookTitle')[0].firstChild.data
                    publisher=chapterNode.getElementsByTagName('Publisher')[0].firstChild.data
                    location=chapterNode.getElementsByTagName('Place')[0].firstChild.data
                    literature=Chapter(title=title, year=int(year), book_title=bookTitle, location=location,
                        publisher=publisher, editors=editors, collator=User.objects.get(username='jbonaiuto'))

                if not literature is None:
                    literature.save()

                # Process author list
                authorList=refData.getElementsByTagName('Author')
                order=1
                for authorNode in authorList:
                    initials=authorNode.getElementsByTagName('Initials')[0].firstChild.data
                    lastname=authorNode.getElementsByTagName('LastName')[0].firstChild.data

                    # Get existing author
                    authors=Author.objects.filter(last_name=lastname, first_name__startswith=initials[0])
                    if authors:
                        author=authors[0]

                    # Create new author
                    else:
                        author=Author(last_name=lastname, first_name=initials[0])
                        if len(initials)>1:
                            author.middle_name=initials[1]
                        author.save()
                    oa=LiteratureAuthor(author=author,order=order)
                    oa.save()
                    literature.authors.add(oa)
                    order += 1
                literature.save()

            # generate nomenclature name and version from id
            name=''
            ver=''
            nameRead=False
            i=0
            while i<len(id):
                if (not nameRead) and (not (id[i]>='0' and id[i]<='9')):
                    name=name+id[i]
                else:
                    nameRead=True
                    ver=ver+id[i]
                i += 1

            # create nomenclature
            if not Nomenclature.objects.filter(lit=literature, name=name, version=ver):
                nomenclature=Nomenclature(lit=literature, name=name, version=ver)
                nomenclature.save()
            else:
                nomenclature=Nomenclature.objects.get(lit=literature, name=name, version=ver)

            speciesNodes=exportNode.getElementsByTagName('MacaqueSpecies')
            for speciesNode in speciesNodes:
                name=speciesNode.firstChild.data
                if not name=='?':
                    genusName=name[:name.find(' ')]
                    speciesName=name[name.find(' ')+1:]
                    if Species.objects.filter(genus_name=genusName, species_name=speciesName):
                        species=Species.objects.get(genus_name=genusName, species_name=speciesName)
                    else:
                        species=Species(genus_name=genusName, species_name=speciesName)
                        species.save()
                    if not species in nomenclature.species.all():
                        nomenclature.species.add(species)

            nomenclature.save()

            # process each region in nomenclature
            for regionNode in regionNodeList:
                addRegion(nomenclature, regionNode)
        else:
            nomenclature=None

    except ExpatError as e:
        print('**** error ****')
        print(e.message)
        nomenclature=None

    return nomenclature

# Add region
def addRegion(nomenclature, regionNode):
    id=regionNode.getElementsByTagName('ID_BrainSite')[0].firstChild.data
    abbrev=regionNode.getElementsByTagName('Acronym')[0].firstChild.data
    name=abbrev
    nameNode=regionNode.getElementsByTagName('FullName')
    if len(nameNode)>0:
        name=nameNode[0].firstChild.data

    if not BrainRegion.objects.filter(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region'):
        region=BrainRegion(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region')
        region.save()
    else:
        region=BrainRegion.objects.get(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region')

    if not CoCoMacBrainRegion.objects.filter(brain_region=region, cocomac_id=id):
        mappedRegion=CoCoMacBrainRegion(brain_region=region, cocomac_id=id)
        mappedRegion.save()

    return region


def download(url, fileName):
    """Copy the contents of a file from a given URL
    to a local file.
    """
    webFile = urllib.urlopen(url)
    localFile = open(fileName, 'w')
    data=webFile.read()
    data=re.sub('UTF-8','iso-8859-1',data)
    data=re.sub(' & ', ' &amp; ',data)
    data=re.sub('>< ', '> ',data)
    data=re.sub('><(\d)','>',data )
    data=re.sub('&qu<','<',data)
    data=re.sub('<HK>','',data)
    data=re.sub('<BR>','',data)
    localFile.write(data)
    webFile.close()
    localFile.close()
