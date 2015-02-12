import urllib
from Bio import Entrez
from django.db.models import Q
from bodb.search.sed import SEDSearch
from taggit.utils import parse_tags

Entrez.email = 'uscbrainproject@gmail.com'
import operator
from lxml import etree
from django.contrib.auth.models import User
from bodb.models import BredeBrainImagingSED, Journal, Author, LiteratureAuthor, CoordinateSpace, ThreeDCoord, SEDCoord, importPubmedLiterature, Document

def runBredeSearch(search_data, userId):
    searcher=BredeSearch(search_data)
    results=[]
    search_local=True
    if not hasattr(searcher,'type') or (hasattr(searcher,'type') and searcher.type=='brain imaging'):
        if hasattr(searcher,'search_brede') and searcher.search_brede:
            search_local=False
            print('Trying to search Brede')
            woBibsDoc=None
            try:
                woBibsDoc = etree.fromstring(download('http://neuro.imm.dtu.dk/services/brededatabase/wobibs.xml'))
            except etree.XMLSyntaxError as e:
                print ("PARSING ERROR", e)

            if not woBibsDoc is None:
                xpathStrings=[]
                # construct search query
                for key in search_data.iterkeys():
                    # if the searcher can search by this field
                    if hasattr(searcher, 'search_%s' % key):
                        # add field to query
                        dispatch=getattr(searcher, 'search_%s' % key)
                        xpathStrings.append(dispatch(userId))

                xpathString='//Exp'

                if len(xpathStrings):
                    if search_data['search_options']=='all':
                        xpathString=' & '.join(xpathStrings)
                    else:
                        xpathString=' | '.join(xpathStrings)

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
        filters=[]

        op=operator.or_
        if search_data['search_options']=='all':
            op=operator.and_
            
        searcher=LocalBredeSearch(search_data)
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
            return list(BredeBrainImagingSED.objects.filter(q).select_related('collator').distinct())
        return list(BredeBrainImagingSED.objects.all().select_related('collator'))

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
        lit=importPubmedLiterature(bib_node.xpath('pmid')[0].text)
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


class BredeSearch:

    def __init__(self, search_data):
        self.__dict__.update(search_data)
    
    def search_keywords(self, userId):
        xpath_string=''
        if self.keywords:            
            search_nodes=['capsuleDescription','freeFormDescription','specificTask','behavioralDomain']
            for search_node in search_nodes:
                words=self.keywords.split()
                for word in words:
                    if len(xpath_string):
                        xpath_string='%s | ' % xpath_string
                    xpath_string='%s //Exp[contains(%s,"%s")]' % (xpath_string,search_node,word)
        return xpath_string

    def search_title(self, userId):
        xpath_string=''
        if self.title:
            words=self.title.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(capsuleDescription,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by description
    def search_description(self, userId):
        xpath_string=''
        if self.description:
            words=self.description.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(freeFormDescription,"%s")]' % (xpath_string,word)
        return xpath_string

    def search_related_brain_region(self, userId):
        xpath_string=''
        if self.related_brain_region:
            words=self.related_brain_region.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(Loc/functionalArea,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature title
    def search_related_literature_title(self, userId):
        xpath_string=''
        if self.related_literature_title:
            words=self.related_literature_title.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(../title,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature author name
    def search_related_literature_author(self, userId):
        xpath_string=''
        if self.related_literature_author:
            words=self.related_literature_author.split()
            for word in words:
                if len(xpath_string):
                    xpath_string='%s | ' % xpath_string
                xpath_string='%s //Exp[contains(../authors,"%s")]' % (xpath_string,word)
        return xpath_string

    # search by related Literature minimum year
    def search_related_literature_year_min(self, userId):
        xpath_string=''
        if self.related_literature_year_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[../year>=%d)]' % (xpath_string,self.related_literature_year_min)
        return xpath_string

    # search by related Literature maximum year
    def search_related_literature_year_max(self, userId):
        xpath_string=''
        if self.related_literature_year_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[../year<=%d)]' % (xpath_string,self.related_literature_year_min)
        return xpath_string

    def search_method(self, userId):
        xpath_string=''
        if self.method:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[modality="%s")]' % (xpath_string,self.method)
        return xpath_string

    def search_coordinate_brain_region(self, userId):
        xpath_string=''
        if self.coordinate_brain_region:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/functionalArea="%s"]' % (xpath_string,self.coordinate_brain_region)
        return xpath_string

    # search by coordinate x
    def search_x_min(self, userId):
        xpath_string=''
        if self.x_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/xReported>=%.4f)]' % (xpath_string,self.x_min)
        return xpath_string

    # search by coordinate x
    def search_x_max(self, userId):
        xpath_string=''
        if self.x_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/xReported<=%.4f)]' % (xpath_string,self.x_max)
        return xpath_string

    # search by coordinate y
    def search_y_min(self, userId):
        xpath_string=''
        if self.y_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/yReported>=%.4f)]' % (xpath_string,self.y_min)
        return xpath_string

    # search by coordinate y
    def search_y_max(self, userId):
        xpath_string=''
        if self.y_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/yReported<=%.4f)]' % (xpath_string,self.y_max)
        return xpath_string

    # search by coordinate z
    def search_z_min(self, userId):
        xpath_string=''
        if self.z_min:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/zReported>=%.4f)]' % (xpath_string,self.z_min)
        return xpath_string

    # search by coordinate z
    def search_z_max(self, userId):
        xpath_string=''
        if self.z_max:
            if len(xpath_string):
                xpath_string='%s | ' % xpath_string
            xpath_string='%s //Exp[Loc/zReported<=%.4f)]' % (xpath_string,self.z_max)
        return xpath_string


class LocalBredeSearch(SEDSearch):

    # search by control condition
    def search_control_condition(self, userId):
        if self.control_condition:
            op=operator.or_
            if self.control_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.control_condition)
            keyword_filters=[Q(control_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by experimental condition
    def search_experimental_condition(self, userId):
        if self.experimental_condition:
            op=operator.or_
            if self.experimental_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.experimental_condition)
            keyword_filters=[Q(experimental_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by method
    def search_method(self, userId):
        if self.method:
            return Q(method=self.method)
        return Q()

    # search by coordinate brain region
    def search_coordinate_brain_region(self, userId):
        if self.coordinate_brain_region:
            op=operator.or_
            if self.coordinate_brain_region_options=='all':
                op=operator.and_

            words=parse_tags(self.coordinate_brain_region)
            region_filters=[Q(Q(coordinates__named_brain_region=word) |
                              Q(coordinates__coord__brainregionvolume__brain_region__name=word) |
                              Q(coordinates__coord__brainregionvolume__brain_region__parent_region__name=word))
                            for word in words]
            return reduce(op,region_filters)
        return Q()

    # search by coordinate x
    def search_x_min(self, userId):
        if self.x_min:
            return Q(coordinates__coord__x__gte=self.x_min)
        return Q()

    # search by coordinate x
    def search_x_max(self, userId):
        if self.x_max:
            return Q(coordinates__coord__x__lte=self.x_max)
        return Q()

    # search by coordinate y
    def search_y_min(self, userId):
        if self.y_min:
            return Q(coordinates__coord__y__gte=self.y_min)
        return Q()

    # search by coordinate y
    def search_y_max(self, userId):
        if self.y_max:
            return Q(coordinates__coord__y__lte=self.y_max)
        return Q()

    # search by coordinate z
    def search_z_min(self, userId):
        if self.z_min:
            return Q(coordinates__coord__z__gte=self.z_min)
        return Q()

    # search by coordinate z
    def search_z_max(self, userId):
        if self.z_max:
            return Q(coordinates__coord__z__lte=self.z_max)
        return Q()


def download(url):
    """Copy the contents of a file from a given URL
    to a local file.
    """
    webFile = urllib.urlopen(url)
    data=webFile.read()
    webFile.close()
    return data

if __name__ == '__main__':
    searcher=BredeSearch()
    searcher.searchString('saccade')