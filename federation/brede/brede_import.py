import os
import sqlite3
from Bio import Entrez
Entrez.email = 'uscbrainproject@gmail.com'
from django.conf import settings
from xml.dom import minidom
from pyexpat import ExpatError
from uscbp.bodb.models.atlas import *
from uscbp.bodb.models.document import *
from uscbp.bodb.models.literature import *
from django.contrib.auth.models import User

class BredeImporter:

    def importWiki(self):
        self.conn=sqlite3.connect(os.path.join(settings.MEDIA_ROOT),'brede/bredewiki-templates.sqlite3')
        c=self.conn.cursor()
        c.execute('SELECT __title, __pid, _woexp, _description, _modality, _brain_template from brede_talairach_coordinates_experiment')
        for row in c:
            importWikiExperiment(row)

    def importWikiExperiment(self, row):
        title=row[0]
        id=row[1]
        woexp=None
        if row[2]:
            woexp=row[2]
        if (not BredeWikiBrainImagingSED.objects.filter(title=title)) and (woexp is None or not BredeBrainImagingSED.objects.filter(woexp=woexp)):
            sed=BredeWikiBrainImagingSED(title=title)
            if row[3]:
                sed.brief_description=row[3]
            if row[4]:
                sed.method=row[4]
            if row[5] and row[5]=='MNI':
                sed.coord_space=CoordinateSpace.objects.get(name='MNI')
            else:
                sed.coord_space=CoordinateSpace.objects.get(name='Talairach')
            if woexp:
                sed.woexp=woexp
            sed.save()

            c=self.conn.cursor()
            c.execute('SELECT _pmid FROM brede_paper WHERE __pid='+str(id))
            for litrow in c:
                if litrow[0]:
                    lit=self.getLiterature(litrow[0])
                    sed.literature.add(lit)
            sed.save()

            importWikiCoordinates(id, sed)

    def importWOEXPs(self):
        wobbibsFile=os.path.join(settings.MEDIA_ROOT,'brede/wobibs.xml')
        try:
            doc=minidom.parse(wobbibsFile)
        except ExpatError:
            print('error parsing file')

        bibNodes=doc.getElementsByTagName('Bib')
        for bibNode in bibNodes:
            self.processBibNode(bibNode)

    def processBibNode(self, bibNode):
        if len(bibNode.getElementsByTagName('pmid'))>0 and bibNode.getElementsByTagName('pmid')[0].firstChild:
            lit=self.getLiterature(bibNode.getElementsByTagName('pmid')[0].firstChild.data)
        else:
            lit=Journal(collator=User.objects.get(username='jbonaiuto'))
            lit.journal_name=bibNode.getElementsByTagName('journal')[0].firstChild.data
            lit.title=bibNode.getElementsByTagName('title')[0].firstChild.data
            if len(bibNode.getElementsByTagName('volume'))>0 and bibNode.getElementsByTagName('volume')[0].firstChild:
                lit.volume=int(bibNode.getElementsByTagName('volume')[0].firstChild.data)
            if len(bibNode.getElementsByTagName('number'))>0 and bibNode.getElementsByTagName('number')[0].firstChild:
                lit.issue=bibNode.getElementsByTagName('number')[0].firstChild.data
            if len(bibNode.getElementsByTagName('pages'))>0 and bibNode.getElementsByTagName('pages')[0].firstChild:
                lit.pages=bibNode.getElementsByTagName('pages')[0].firstChild.data
            if len(bibNode.getElementsByTagName('year'))>0 and bibNode.getElementsByTagName('year')[0].firstChild:
                lit.year=int(bibNode.getElementsByTagName('year')[0].firstChild.data)
            lit.save()
            auth_string=bibNode.getElementsByTagName('authors')[0].firstChild.data
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
                ordered_auth=OrderedAuthor(author=author,order=idx)
                ordered_auth.save()
                lit.authors.add(ordered_auth)
            lit.save()

        expNodes=bibNode.getElementsByTagName('Exp')
        for expNode in expNodes:
            self.processExpNode(lit, expNode)

    def processExpNode(self, lit, expNode):
        woExpId=int(expNode.getElementsByTagName('woexp')[0].firstChild.data)
        if not BredeBrainImagingSED.objects.filter(woexp=woExpId):
            print('importing woexp='+str(woExpId))
            capsule_desc=expNode.getElementsByTagName('capsuleDescription')[0].firstChild.data
            #task=expNode.getElementsByTagName('specificTask')[0].firstChild.data
            method=expNode.getElementsByTagName('modality')[0].firstChild.data
            sed=BredeBrainImagingSED(type='imaging', woexp=woExpId, method=method, collator=User.objects.get(username='jbonaiuto'), public=True)
            sed.title=capsule_desc
            if len(expNode.getElementsByTagName('freeFormDescription'))>0 and expNode.getElementsByTagName('freeFormDescription')[0].firstChild:
                sed.brief_description=expNode.getElementsByTagName('freeFormDescription')[0].firstChild.data
            if len(expNode.getElementsByTagName('brainTemplate'))>0 and expNode.getElementsByTagName('brainTemplate')[0].firstChild and expNode.getElementsByTagName('brainTemplate')[0].firstChild.data=='MNI':
                sed.coord_space=CoordinateSpace.objects.get(name='MNI')
            else:
                sed.coord_space=CoordinateSpace.objects.get(name='Talairach')
            sed.core_header_2='x | y | z'
            if len(expNode.getElementsByTagName('zScore'))>0:
                sed.core_header_3='Z'
                sed.core_header_4='N/A'
            elif len(expNode.getElementsByTagName('tValue'))>0:
                sed.code_header_3='T'
                sed.core_header_4='N/A'
            else:
                sed.core_header_3='N/A'
                sed.core_header_4='N/A'
            sed.extra_header=''
            sed.save()
            sed.literature.add(lit)
            sed.save()

            locNodes=expNode.getElementsByTagName('Loc')
            for locNode in locNodes:
                self.processCoordinate(sed, locNode)

    def processCoordinate(self, sed, locNode):
        if sed.coord_space.name=='MNI':
            x=str(int(float(locNode.getElementsByTagName('xReported')[0].firstChild.data)*1000))
            y=str(int(float(locNode.getElementsByTagName('yReported')[0].firstChild.data)*1000))
            z=str(int(float(locNode.getElementsByTagName('zReported')[0].firstChild.data)*1000))
        else:
            x=str(int(float(locNode.getElementsByTagName('x')[0].firstChild.data)*1000))
            y=str(int(float(locNode.getElementsByTagName('y')[0].firstChild.data)*1000))
            z=str(int(float(locNode.getElementsByTagName('z')[0].firstChild.data)*1000))
        if ThreeDCoord.objects.filter(x=x,y=y,z=z):
            coord=ThreeDCoord.objects.get(x=x,y=y,z=z)
        else:
            coord=ThreeDCoord(x=x,y=y,z=z)
            coord.save()
        sedCoord=SEDCoord(sed=sed, coord=coord, coord_space=sed.coord_space, collator=User.objects.get(username='jbonaiuto'), extra_data='')
        if len(locNode.getElementsByTagName('zScore'))>0 and locNode.getElementsByTagName('zScore')[0].firstChild:
            sedCoord.statistic='z'
            sedCoord.statistic_value=str(locNode.getElementsByTagName('zScore')[0].firstChild.data)
        elif len(locNode.getElementsByTagName('tValue'))>0 and locNode.getElementsByTagName('tValue')[0].firstChild:
            sedCoord.statistic='t'
            sedCoord.statistic_value=str(locNode.getElementsByTagName('tValue')[0].firstChild.data)
        if len(locNode.getElementsByTagName('lobarAnatomy'))>0 and locNode.getElementsByTagName('lobarAnatomy')[0].firstChild:
            sedCoord.named_brain_region=locNode.getElementsByTagName('lobarAnatomy')[0].firstChild.data
        elif len(locNode.getElementsByTagName('functionalArea'))>0 and locNode.getElementsByTagName('functionalArea')[0].firstChild:
            sedCoord.named_brain_region=locNode.getElementsByTagName('functionalArea')[0].firstChild.data
        elif len(locNode.getElementsByTagName('brodmann'))>0 and locNode.getElementsByTagName('brodmann')[0].firstChild:
            sedCoord.named_brain_region='Brodmann Area '+str(locNode.getElementsByTagName('brodmann')[0].firstChild.data)
        if x<0:
            sedCoord.hemisphere='left'
        elif x>0:
            sedCoord.hemisphere='right'
        else:
            sedCoord.hemisphere='interhemispheric'
        sedCoord.save()

    def getLiterature(self, pubmed_id):
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
                        orderedAuth=OrderedAuthor(author=Author.objects.filter(first_name=first_name, last_name=last_name)[0], order=idx)
                        orderedAuth.save()
                        lit.authors.add(orderedAuth)

                    # otherwise add new author
                    else:
                        a=Author()
                        a.first_name=first_name
                        a.last_name=last_name
                        a.save()
                        orderedAuth=OrderedAuthor(author=a,order=idx)
                        orderedAuth.save()
                        lit.authors.add(orderedAuth)
        return lit