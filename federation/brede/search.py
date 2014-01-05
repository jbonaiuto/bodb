import urllib
from Bio import Entrez
from django.db.models import Q
from bodb.search import SEDSearch

Entrez.email = 'uscbrainproject@gmail.com'
from lxml import etree
from django.contrib.auth.models import User
from bodb.models import BredeBrainImagingSED, Literature, Journal, Author, LiteratureAuthor, CoordinateSpace, ThreeDCoord, SEDCoord

def runBredeSearch(search_data, userId):
    xpathString=''
    searcher=BredeSearcher(search_data)
    results=[]
    search_local=False
    if hasattr(searcher,'type') and (searcher.type=='' or searcher.type=='brain imaging'):
        if hasattr(searcher,'search_brede') and searcher.search_brede:
            print('Trying to search Brede')
            woBibsDoc=None
            try:
                woBibsDoc = etree.fromstring(download('http://neuro.imm.dtu.dk/services/brededatabase/wobibs.xml'))
            except etree.XMLSyntaxError as e:
                print ("PARSING ERROR", e)

            if not woBibsDoc is None:
                # construct search query
                for key in search_data.iterkeys():
                    # if the searcher can search by this field
                    if hasattr(searcher, 'search_%s' % key):
                        # add field to query
                        dispatch=getattr(searcher, 'search_%s' % key)
                        xpathString=dispatch(xpathString, userId)

                if not len(xpathString):
                    xpathString='//Exp'

                exp_nodes=woBibsDoc.xpath(xpathString)
                for exp_node in exp_nodes:
                    wo_exp=int(exp_node.xpath('./woexp')[0].text)
                    if not BredeBrainImagingSED.objects.filter(woexp=wo_exp):
                        bib_node=exp_node.getparent()
                        try:
                            lit=importLiterature(bib_node)
                            sed=importSED(exp_node, lit, wo_exp)
                            results.append(sed)
                        except:
                            pass
                    else:
                        results.append(BredeBrainImagingSED.objects.get(woexp=wo_exp))
            else:
                search_local=True
        else:
            search_local=True

    if search_local:
        print('Searching locally')
        q=Q()
        searcher=SEDSearch(search_data)
        # construct search query
        for key in search_data.iterkeys():
            # if the searcher can search by this field
            if hasattr(searcher, 'search_%s' % key):
                # add field to query
                dispatch=getattr(searcher, 'search_%s' % key)
                q=dispatch(q, userId)

        # get results
        if q and len(q):
            results = list(BredeBrainImagingSED.objects.filter(q).select_related().distinct())
        else:
            results = list(BredeBrainImagingSED.objects.all())

    return results

def importSED(exp_node, lit, wo_exp):
    capsule_desc = exp_node.xpath('./capsuleDescription')[0].text
    #task=expNode.xpath('specificTask')[0].text
    method = exp_node.xpath('./modality')[0].text
    sed = BredeBrainImagingSED(type='brain imaging', woexp=wo_exp, method=method,
        collator=User.objects.get(username='jbonaiuto'), public=True)
    sed.title = capsule_desc
    if len(exp_node.xpath('./freeFormDescription')) > 0 and exp_node.xpath('./freeFormDescription')[0].text:
        sed.brief_description = exp_node.xpath('./freeFormDescription')[0].text
    if len(exp_node.xpath('./brainTemplate')) > 0 and exp_node.xpath('./brainTemplate')[0].text and\
       exp_node.xpath('./brainTemplate')[0].text == 'MNI':
        sed.coord_space = CoordinateSpace.objects.get(name='MNI')
    else:
        sed.coord_space = CoordinateSpace.objects.get(name='Talairach')
    sed.core_header_2 = 'x | y | z'
    if len(exp_node.xpath('.//zScore')) > 0:
        sed.core_header_3 = 'Z'
        sed.core_header_4 = 'N/A'
    elif len(exp_node.xpath('.//tValue')) > 0:
        sed.code_header_3 = 'T'
        sed.core_header_4 = 'N/A'
    else:
        sed.core_header_3 = 'N/A'
        sed.core_header_4 = 'N/A'
    sed.extra_header = ''
    sed.save()
    sed.literature.add(lit)
    sed.save()

    locNodes=exp_node.xpath('Loc')
    for locNode in locNodes:
        processCoordinate(sed, locNode)

    return sed

def processCoordinate(sed, locNode):
    if sed.coord_space.name=='MNI':
        x=str(int(float(locNode.xpath('xReported')[0].text)*1000))
        y=str(int(float(locNode.xpath('yReported')[0].text)*1000))
        z=str(int(float(locNode.xpath('zReported')[0].text)*1000))
    else:
        x=str(int(float(locNode.xpath('x')[0].text)*1000))
        y=str(int(float(locNode.xpath('y')[0].text)*1000))
        z=str(int(float(locNode.xpath('z')[0].text)*1000))
    if ThreeDCoord.objects.filter(x=x,y=y,z=z):
        coord=ThreeDCoord.objects.get(x=x,y=y,z=z)
    else:
        coord=ThreeDCoord(x=x,y=y,z=z)
        coord.save()
    sedCoord=SEDCoord(sed=sed, coord=coord, extra_data='')
    if len(locNode.xpath('zScore'))>0 and locNode.xpath('zScore')[0].text:
        sedCoord.statistic='z'
        sedCoord.statistic_value=str(locNode.xpath('zScore')[0].text)
    elif len(locNode.xpath('tValue'))>0 and locNode.xpath('tValue')[0].text:
        sedCoord.statistic='t'
        sedCoord.statistic_value=str(locNode.xpath('tValue')[0].text)
    if len(locNode.xpath('lobarAnatomy'))>0 and locNode.xpath('lobarAnatomy')[0].text:
        sedCoord.named_brain_region=locNode.xpath('lobarAnatomy')[0].text
    elif len(locNode.xpath('functionalArea'))>0 and locNode.xpath('functionalArea')[0].text:
        sedCoord.named_brain_region=locNode.xpath('functionalArea')[0].text
    elif len(locNode.xpath('brodmann'))>0 and locNode.xpath('brodmann')[0].text:
        sedCoord.named_brain_region='Brodmann Area '+str(locNode.xpath('brodmann')[0].text)
    if float(x)<0:
        sedCoord.hemisphere='left'
    elif float(x)>0:
        sedCoord.hemisphere='right'
    else:
        sedCoord.hemisphere='interhemispheric'
    sedCoord.save()

def importLiterature(bib_node):
    if len(bib_node.xpath('pmid'))>0 and bib_node.xpath('pmid')[0].text:
        lit=getLiterature(bib_node.xpath('pmid')[0].text)
    else:
        lit=Journal(collator=User.objects.get(username='jbonaiuto'))
        lit.journal_name=bib_node.xpath('journal')[0].text
        lit.title=bib_node.xpath('title')[0].text
        if len(bib_node.xpath('volume'))>0 and bib_node.xpath('volume')[0].text:
            lit.volume=int(bib_node.xpath('volume')[0].text)
        if len(bib_node.xpath('number'))>0 and bib_node.xpath('number')[0].text:
            lit.issue=bib_node.xpath('number')[0].text
        if len(bib_node.xpath('pages'))>0 and bib_node.xpath('pages')[0].text:
            lit.pages=bib_node.xpath('pages')[0].text
        if len(bib_node.xpath('year'))>0 and bib_node.xpath('year')[0].text:
            lit.year=int(bib_node.xpath('year')[0].text)
        lit.save()
        auth_string=bib_node.xpath('authors')[0].text
        auth_list=auth_string.split('; ')
        for idx, auth in enumerate(auth_list):
            single_auth_list=auth.split(' ')
            first_name=single_auth_list[0]
            middle_name=''
            last_name=''
            if len(single_auth_list)==2:
                last_name=single_auth_list[1]
            else:
                middle_name=single_auth_list[1]
                last_name=single_auth_list[2]
            if Author.objects.filter(first_name=first_name, last_name=last_name):
                author=Author.objects.get(first_name=first_name, last_name=last_name)
            else:
                author=Author(first_name=first_name,middle_name=middle_name,last_name=last_name)
                author.save()
            ordered_auth=LiteratureAuthor(author=author,order=idx)
            ordered_auth.save()
            lit.authors.add(ordered_auth)
        lit.save()
    return lit

def getLiterature(pubmed_id):
    if Literature.objects.filter(pubmed_id=pubmed_id):
        lit=Literature.objects.get(pubmed_id=pubmed_id)
    else:
        article_handles=Entrez.esummary(db="pubmed", id=pubmed_id)
        article_record=Entrez.read(article_handles)[0]
        lit=Journal(title=article_record['Title'].replace('\'', '\\\''), year=article_record['PubDate'].split(' ')[0],
            pubmed_id=pubmed_id, url='http://www.ncbi.nlm.nih.gov/pubmed/'+article_record['Id'], collator=User.objects.get(username='jbonaiuto'))
        if 'Source' in article_record:
            lit.journal_name=article_record['Source'].replace('\'', '\\\'')
        if 'Volume' in article_record:
            try:
                lit.volume=int(article_record['Volume'])
            except ValueError:
                None
        if 'Issue' in article_record:
            lit.issue=article_record['Issue']
        if 'Pages' in article_record:
            lit.pages=article_record['Pages']
        if 'LangList' in article_record:
            lit.language=", ".join(article_record['LangList'])
        lit.save()
        if 'AuthorList' in article_record:
            authorList=", ".join(article_record['AuthorList']).replace('\'', '\\\'')
            authors=authorList.split(', ')
            # list of author ids
            for idx,author in enumerate(authors):
                full_name = author.split()
                last_name = unicode(full_name[0].encode('latin1','xmlcharrefreplace'))
                first_name = full_name[1]

                # get Id if author exists
                if Author.objects.filter(first_name=first_name, last_name=last_name):
                    orderedAuth=LiteratureAuthor(author=Author.objects.filter(first_name=first_name, last_name=last_name)[0], order=idx)
                    orderedAuth.save()
                    lit.authors.add(orderedAuth)

                # otherwise add new author
                else:
                    a=Author()
                    a.first_name=first_name
                    a.last_name=last_name
                    a.save()
                    orderedAuth=LiteratureAuthor(author=a,order=idx)
                    orderedAuth.save()
                    lit.authors.add(orderedAuth)
    return lit

class BredeSearcher:

    def __init__(self, search_data):
        self.__dict__.update(search_data)
    
    def search_keywords(self, xpath_string, userId):
        if self.keywords:
            search_nodes=['capsuleDescription','freeFormDescription','specificTask','behavioralDomain']
            for search_node in search_nodes:
                words=self.keywords.split()
                for word in words:
                    if len(xpath_string):
                        xpath_string='%s | ' % xpath_string
                    xpath_string='%s //Exp[contains(%s,"%s")]' % (xpath_string,search_node,word)
        return xpath_string

    def search_title(self, xpath_string, userId):
        if self.title:
            words=self.title.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(capsuleDescription,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by description
    def search_description(self, xpath_string, userId):
        if self.description:
            words=self.description.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(freeFormDescription,"%s")]' % (xpath_string,word)
        return xpath_string

    def search_related_brain_region(self, xpath_string, userId):
        if self.related_brain_region:
            words=self.related_brain_region.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(Loc/functionalArea,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature title
    def search_related_literature_title(self, xpath_string, userId):
        if self.related_literature_title:
            words=self.related_literature_title.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(../title,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature author name
    def search_related_literature_author(self, xpath_string, userId):
        if self.related_literature_author:
            words=self.related_literature_author.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(../authors,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature minimum year
    def search_related_literature_year_min(self, xpath_string, userId):
        if self.related_literature_year_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[../year>=%d)]' % (xpath_string,self.related_literature_year_min)
        return xpath_string

    # search by related Literature maximum year
    def search_related_literature_year_max(self, xpath_string, userId):
        if self.related_literature_year_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[../year<=%d)]' % (xpath_string,self.related_literature_year_min)
        return xpath_string

    def search_method(self, xpath_string, userId):
        if self.method:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[modality="%s")]' % (xpath_string,self.method)
        return xpath_string

    def search_coordinate_brain_region(self, xpath_string, userId):
        if self.coordinate_brain_region:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/functionalArea="%s"]' % (xpath_string,self.coordinate_brain_region)
        return xpath_string

    # search by coordinate x
    def search_x_min(self, xpath_string, userId):
        if self.x_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/xReported>=%.4f)]' % (xpath_string,self.x_min)
        return xpath_string

    # search by coordinate x
    def search_x_max(self, xpath_string, userId):
        if self.x_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/xReported<=%.4f)]' % (xpath_string,self.x_max)
        return xpath_string

    # search by coordinate y
    def search_y_min(self, xpath_string, userId):
        if self.y_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/yReported>=%.4f)]' % (xpath_string,self.y_min)
        return xpath_string

    # search by coordinate y
    def search_y_max(self, xpath_string, userId):
        if self.y_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/yReported<=%.4f)]' % (xpath_string,self.y_max)
        return xpath_string

    # search by coordinate z
    def search_z_min(self, xpath_string, userId):
        if self.z_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/zReported>=%.4f)]' % (xpath_string,self.z_min)
        return xpath_string

    # search by coordinate z
    def search_z_max(self, xpath_string, userId):
        if self.z_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/zReported<=%.4f)]' % (xpath_string,self.z_max)
        return xpath_string

class LocalBredeSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

def download(url):
    """Copy the contents of a file from a given URL
    to a local file.
    """
    webFile = urllib.urlopen(url)
    data=webFile.read()
    webFile.close()
    return data

if __name__ == '__main__':
    searcher=BredeSearcher()
    searcher.searchString('saccade')