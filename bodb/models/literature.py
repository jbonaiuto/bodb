from Bio import Entrez
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from bodb.models.messaging import UserSubscription

class PubMedResult:
    """
    The result of a pubmed search. These objects are not saved from the database, they are
    basically just used as data structures to return search results
    """
    def __init__(self):
        self.pubmedId=''
        # Whether or not result already exists in database
        self.exists=False
        # If authors contains a single-quote (') we need to strip it from the string embedded in javascript
        self.authors=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.authors_display=''
        self.year=''
        # If title contains a single-quote (') we need to strip it from the string embedded in javascript
        self.title=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.title_display=''
        # If journal contains a single-quote (') we need to strip it from the string embedded in javascript
        self.journal=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.journal_display=''
        self.volume=''
        self.issue=''
        self.pages=''
        self.language=''
        self.url=''


# Author of literature or a model
class Author(models.Model):
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    homepage = models.URLField(blank=True)
    alias = models.CharField(max_length=30, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    #creation_time = models.DateTimeField(blank=True)
    class Meta:
        app_label='bodb'

    # when printing instances of this class, print last_name, middle_name, first_name
    def __unicode__(self):
        return u"%s, %s %s" % (self.last_name, self.first_name, self.middle_name)



class LiteratureAuthor(models.Model):
    author = models.ForeignKey(Author)
    order = models.IntegerField()
    class Meta:
        app_label='bodb'
        ordering=['order']


# A piece of literature: base class for Journal, Book, Conference, Thesis, Unpublished
class Literature(models.Model):
    TYPE_CHOICES = (
        ('', ''),
        ('Journal', 'Journal'),
        ('Book', 'Book'),
        ('Thesis', 'Thesis'),
        ('Conference', 'Conference'),
        ('Unpublished', 'Unpublished'),
        )
    # ID from pubmed
    pubmed_id=models.CharField(max_length=50, blank=True)
    # list of authors
    authors = models.ManyToManyField(LiteratureAuthor)
    title = models.CharField(max_length=300)
    year = models.IntegerField()
    url = models.URLField(blank=True)
    language = models.CharField(max_length=100, default='English')
    annotation = models.TextField(blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, blank=True)
    #creation_time = models.DateTimeField(blank=True)
    # user who added this record
    collator = models.ForeignKey(User,null=True)
    # when listing instances of this class, order by year
    class Meta:
        app_label='bodb'
        ordering=['year']

    def get_collator_str(self):
        if self.collator.last_name:
            return '%s %s' % (self.collator.first_name, self.collator.last_name)
        else:
            return self.collator.username

    # when printing instances of this class, print (authors year)
    def __unicode__(self):
        return u"%s (%s)" % (self.author_names(),str(self.year))

    def get_absolute_url(self):
        return reverse('lit_view', kwargs={'pk': self.pk})

    def str(self):
        try:
            return Journal.objects.prefetch_related('authors__author').get(id=self.id).str()
        except (Journal.DoesNotExist, Journal.MultipleObjectsReturned), err:
            pass
        try:
            return Book.objects.prefetch_related('authors__author').get(id=self.id).str()
        except (Book.DoesNotExist, Book.MultipleObjectsReturned), err:
            pass
        try:
            return Chapter.objects.prefetch_related('authors__author').get(id=self.id).str()
        except (Chapter.DoesNotExist, Chapter.MultipleObjectsReturned), err:
            pass
        return u'%s, %s,  %s.' % (self.author_names(),str(self.year),self.title)

    # print authors
    def author_names(self):
        # author1 et al. if more than 2 authors
        if len(self.authors.all())>2:
            return u"%s et al." % self.authors.all()[0].author.last_name
        # author1 & author2 if two authors
        elif len(self.authors.all())>1:
            return u"%s & %s" %(self.authors.all()[0].author.last_name, self.authors.all()[1].author.last_name)
        #just first author last name if one author
        elif len(self.authors.all())>0:
            return self.authors.all()[0].author.last_name
        return ''
    author_names.short_description='Authors'

    # print a list of all author names
    def author_list(self):
        name_list=[]
        for author in self.authors.all():
            name_list.append(author.author.__unicode__())
        return ', '.join(name_list)

    # function for getting endnote format - should be implemented by child classes
    def endnote_format(self):
        return ''

    # function for getting bibtex format - should be implemented by child classes
    def bibtex_format(self):
        return ''

    def as_json(self):
        return {
            'id': self.id,
            'authors': self.author_names(),
            'year': self.year,
            'title': self.title,
            'collator_id': self.collator.id,
            'collator': self.get_collator_str(),
            'string': self.str(),
            'url_str': self.html_url_string()
        }

    def html_url_string(self):
        if len(self.pubmed_id):
            url='http://www.ncbi.nlm.nih.gov/pubmed/%s' % self.pubmed_id
            return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in PubMed</a>' % (url,url)
        return ''

    @staticmethod
    def get_reference_list(references, workspace_lit, fav_lit, subscriptions):
        reference_list=[]
        for reference in references:
            selected=reference.id in workspace_lit
            is_favorite=reference.id in fav_lit
            subscribed_to_user=(reference.collator.id,'All') in subscriptions
            reference_list.append([selected,is_favorite,subscribed_to_user,reference])
        return reference_list


# Journal article - inherits from Literature
class Journal(Literature):
    journal_name = models.CharField('journal', max_length=200)
    volume = models.CharField(max_length=20, blank=True, null=True)
    issue = models.CharField(max_length=20, blank=True)
    pages = models.CharField(max_length=20, blank=True)
    class Meta:
        app_label='bodb'

    def str(self):
        litstr=u'%s, %s, %s, %s' % (self.author_names(),str(self.year),self.title,self.journal_name)
        if self.volume:
            litstr+=', v. '+str(self.volume)
        if self.issue:
            litstr+=' ('+self.issue+')'
        if self.pages:
            litstr+=', '+self.pages
        litstr+='.'
        return litstr

    # returns article record in endnote format
    def endnote_format(self):
        endnote='%0 Journal Article\n'
        for author in self.authors.all():
            endnote+='%A '+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')+', '+unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')+'\n'
        endnote+='%D '+unicode(self.year).encode('latin1','xmlcharrefreplace')+'\n%T '+unicode(self.title).encode('latin1','xmlcharrefreplace')+'\n%J '+unicode(self.journal_name).encode('latin1','xmlcharrefreplace')+'\n'
        if self.volume:
            endnote+='%V '+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'\n'
        if self.issue:
            endnote+='%N '+unicode(self.issue).encode('latin1','xmlcharrefreplace')+'\n'
        if self.pages:
            endnote+='%P '+unicode(self.pages).encode('latin1','xmlcharrefreplace')+'\n'
        if self.url:
            endnote+='%U '+unicode(self.url).encode('latin1','xmlcharrefreplace')+'\n'
        if self.language:
            endnote+='%G '+unicode(self.language).encode('latin1','xmlcharrefreplace')+'\n'
        return endnote

    # returns article record in bibtex format
    def bibtex_format(self):
        bibtex_id='%d' % self.id
        if len(self.authors.all()):
            bibtex_id=unicode(self.authors.all()[0].author.last_name).encode('latin1','xmlcharrefreplace')+'_'+str(self.id)
        bibtex='@article{'+bibtex_id+',\n'
        bibtex+='   author = {'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtex+=' and '
            bibtex+=''+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')+', '+unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
            i+=1
        bibtex+='},\n   title = {'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'},\n   journal = {'+unicode(self.journal_name).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.volume:
            bibtex+='   volume = {'+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.issue:
            bibtex+='   number = {'+unicode(self.issue).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.pages:
            bibtex+='   pages = {'+unicode(self.pages).encode('latin1','xmlcharrefreplace')+'},\n'
        bibtex+='   year = {'+unicode(self.year).encode('latin1','xmlcharrefreplace')+'}\n}\n'
        return bibtex


# Book - inherits from Literature
class Book(Literature):
    location = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    editors = models.CharField(max_length=200, blank=True)
    class Meta:
        app_label='bodb'

    def str(self):
        litstr='%s, %s, %s' % (self.author_names(), str(self.year), self.title)
        if self.editors:
            litstr+=', in '+self.editors+', ed.'
        if self.series:
            litstr+=', '+self.series
        if self.publisher:
            litstr+=', '+self.publisher
        if self.location:
            litstr+=', '+self.location
        litstr+='.'
        return litstr

    # returns book record in endnote format
    def endnote_format(self):
        endnote='%0 Book\n'
        for author in self.authors.all():
            endnote+='%A '+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')+', '+unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')+'\n'
        endnote+='%D '+unicode(self.year).encode('latin1','xmlcharrefreplace')+'\n%T '+unicode(self.title).encode('latin1','xmlcharrefreplace')+'\n'
        if self.editors:
            endnote+='%E '+unicode(self.editors).encode('latin1','xmlcharrefreplace')+'\n'
        if self.location:
            endnote+='%C '+unicode(self.location).encode('latin1','xmlcharrefreplace')+'\n'
        if self.publisher:
            endnote+='%I '+unicode(self.publisher).encode('latin1','xmlcharrefreplace')+'\n'
        if self.volume:
            endnote+='%V '+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'\n'
        if self.edition:
            endnote+='%7 '+unicode(self.edition).encode('latin1','xmlcharrefreplace')+'\n'
        if self.language:
            endnote+='%G '+unicode(self.language).encode('latin1','xmlcharrefreplace')+'\n'
        return endnote

    # returns book record in bibtex format
    def bibtex_format(self):
        bibtex_id='%d' % self.id
        if len(self.authors.all()):
            bibtex_id=self.authors.all()[0].author.last_name+'_'+str(self.id)
        bibtex='@book{'+bibtex_id+',\n'
        bibtex+='   author = {'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtex+=' and '
            bibtex+=unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')+', '+unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
            i+=1
        bibtex+='},\n   booktitle = {'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.editors:
            bibtex+='   editor = {'+unicode(self.editors).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.publisher:
            bibtex+='   publisher = {'+unicode(self.publisher).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.volume:
            bibtex+='   volume = {'+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.location:
            bibtex+='   address = {'+unicode(self.location).encode('latin1','xmlcharrefreplace')+'},\n'
        if self.edition:
            bibtex+='   edition = {'+unicode(self.edition).encode('latin1','xmlcharrefreplace')+'},\n'
        bibtex+='   year = {'+unicode(self.year).encode('latin1','xmlcharrefreplace')+'}\n}\n'
        return bibtex


# Chapter - inherits from Literature
class Chapter(Literature):
    location = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    editors = models.CharField(max_length=200, blank=True)
    book_title = models.CharField(max_length=200, blank=True)
    class Meta:
        app_label='bodb'

    def str(self):
        litstr='%s, %s, %s' % (self.author_names(), str(self.year), self.title)
        if self.editors:
            litstr+=', in '+self.editors+', ed.'
        if self.book_title:
            litstr+=', '+self.series
        if self.publisher:
            litstr+=', '+self.publisher
        if self.location:
            litstr+=', '+self.location
        litstr+='.'
        return litstr


# Conference proceedings - inherits from Literature
class Conference(Literature):
    location = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=200)
    class Meta:
        app_label='bodb'

# Thesis - inherits from Literature
class Thesis(Literature):
    school = models.CharField(max_length=200)
    # When listing multiple records - the plural form of thesis is theses, not thesiss
    class Meta:
        app_label='bodb'
        verbose_name_plural = 'theses'


# Unpublished - inherits from Literature
class Unpublished(Literature):
    # just so class declaration isn't empty
    class Meta:
        app_label='bodb'
        ordering=['year']

# export the list of references to the given file_name in the given format
def reference_export(format, references, file_name):
    # open file for writing
    FILE = open(file_name, 'w')

    # loop through list of references
    for reference in references:
        # only export journal and book references
        try:
            reference=Journal.objects.get(id=reference.id)
        except (Journal.DoesNotExist, Journal.MultipleObjectsReturned), err:
            reference=None
        try:
            reference=Book.objects.get(id=reference.id)
        except (Book.DoesNotExist, Book.MultipleObjectsReturned), err:
            reference=None
        if reference is None:
            continue

        # write the reference to the file - each reference type knows how to
        # export itself to endnote and bibtex format
        if format=='endnote':
            FILE.write(reference.endnote_format())
            FILE.write('\n\n\n')
        elif format=='bibtex':
            FILE.write(reference.bibtex_format())
            FILE.write('\n\n')

    if format=='xml':
        FILE.write('</bibtex:file>')
    FILE.close()


# The result of a pubmed search. These objects are not saved from the database, they are
# basically just used as data structures to return search results
class PubMedResult:
    def __init__(self):
        self.pubmedId=''
        # Whether or not result already exists in database
        self.exists=False
        # If authors contains a single-quote (') we need to strip it from the string embedded in javascript
        self.authors=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.authors_display=''
        self.year=''
        # If title contains a single-quote (') we need to strip it from the string embedded in javascript
        self.title=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.title_display=''
        # If journal contains a single-quote (') we need to strip it from the string embedded in javascript
        self.journal=''
        # but keep it in the string to display in HTML. TODO: we should use escapejs
        self.journal_display=''
        self.volume=''
        self.issue=''
        self.pages=''
        self.language=''
        self.url=''


def importPubmedLiterature(pubmed_id):
    if Literature.objects.filter(pubmed_id=pubmed_id).exists():
        lit=Literature.objects.filter(pubmed_id=pubmed_id)[0]
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
                try:
                    last_name = unicode(full_name[0],'utf-8')
                except:
                    last_name = full_name[0]
                try:
                    first_name = unicode(full_name[1],'utf-8')
                except:
                    first_name = full_name[1]

                # get Id if author exists
                if Author.objects.filter(first_name=first_name, last_name=last_name).exists():
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