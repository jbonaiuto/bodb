from django.contrib.auth.models import User
from django.conf import settings
from django.db import models

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


# Author of literature or a model
class Author(models.Model):
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    homepage = models.URLField(blank=True)
    alias = models.CharField(max_length=30, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    class Meta:
        app_label='legacy_bodb'

    # when printing instances of this class, print last_name, middle_name, first_name
    def __unicode__(self):
        return u"%s, %s %s" % (self.last_name, self.first_name, self.middle_name)



class OrderedAuthor(models.Model):
    author = models.ForeignKey(Author)
    order = models.IntegerField()
    class Meta:
        app_label='legacy_bodb'
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
    authors = models.ManyToManyField(OrderedAuthor)
    title = models.CharField(max_length=300)
    year = models.IntegerField()
    url = models.URLField(blank=True)
    language = models.CharField(max_length=100, default='English')
    annotation = models.TextField(blank=True)
    creation_time = models.DateTimeField(auto_now_add=True, blank=True)
    # user who added this record
    collator = models.ForeignKey(User)
    # when listing instances of this class, order by year
    class Meta:
        app_label='legacy_bodb'
        ordering=['year']

    def get_collator_str(self):
        if self.collator.last_name:
            return '%s %s' % (self.collator.first_name, self.collator.last_name)
        else:
            return self.collator.username
        
    # when printing instances of this class, print (authors year)
    def __unicode__(self):
        return u"%s (%s)" % (self.author_names(),str(self.year))

    def str(self):
        if Journal.objects.filter(id=self.id):
            return Journal.objects.get(id=self.id).str()
        elif Book.objects.filter(id=self.id):
            return Book.objects.get(id=self.id).str()
        elif Chapter.objects.filter(id=self.id):
            return Chapter.objects.get(id=self.id).str()
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

    def bibtexml_format(self):
        return''


# Journal article - inherits from Literature
class Journal(Literature):
    journal_name = models.CharField('journal', max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    issue = models.CharField(max_length=20, blank=True)
    pages = models.CharField(max_length=20, blank=True)
    class Meta:
        app_label='legacy_bodb'

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
            bibtex_id=self.authors.all()[0].author.last_name+'_'+str(self.id)
        bibtex='@article{'+bibtex_id+',\n'
        bibtex+='   author = {'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtex+=' and '
            bibtex+=unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')+', '+unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
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

    def bibtexml_format(self):
        bibtex_id='%d' % self.id
        if len(self.authors.all()):
            bibtex_id=self.authors.all()[0].author.last_name+'_'+str(self.id)
        bibtexml='<bibtex:entry bibtex:id="'+bibtex_id+'">\n'
        bibtexml+='<bibtex:article>\n'
        bibtexml+='<bibtex:author>'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtexml+='; '
            bibtexml+=unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
            if author.author.middle_name:
                bibtexml+=' '+unicode(author.author.middle_name).encode('latin1','xmlcharrefreplace')
            bibtexml+=' '+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')
            i+=1
        bibtexml+='</bibtex:author>\n'
        bibtexml+='<bibtex:title>'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'</bibtex:title>\n'
        bibtexml+='<bibtex:journal>'+unicode(self.journal_name).encode('latin1','xmlcharrefreplace')+'</bibtex:journal>\n'
        bibtexml+='<bibtex:year>'+unicode(self.year).encode('latin1','xmlcharrefreplace')+'</bibtex:year>\n'
        if self.volume:
            bibtexml+='<bibtex:volume>'+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'</bibtex:volume>\n'
        if self.issue:
            bibtexml+='<bibtex:number>'+unicode(self.issue).encode('latin1','xmlcharrefreplace')+'</bibtex:number>\n'
        if self.pages:
            bibtexml+='<bibtex:pages>'+unicode(self.pages).encode('latin1','xmlcharrefreplace')+'</bibtex:pages>\n'
        bibtexml+='</bibtex:article>\n'
        bibtexml+='</bibtex:entry>'
        return bibtexml

# Book - inherits from Literature
class Book(Literature):
    location = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    editors = models.CharField(max_length=200, blank=True)
    class Meta:
        app_label='legacy_bodb'

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

    def bibtexml_format(self):
        bibtex_id='%d' % self.id
        if len(self.authors.all()):
            bibtex_id=self.authors.all()[0].author.last_name+'_'+str(self.id)
        bibtexml='<bibtex:entry bibtex:id="'+bibtex_id+'">\n'
        bibtexml+='<bibtex:book>\n'
        bibtexml+='<bibtex:author>'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtexml+='; '
            bibtexml+=unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
            if author.author.middle_name:
                bibtexml+=' '+unicode(author.author.middle_name).encode('latin1','xmlcharrefreplace')
            bibtexml+=' '+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')
            i+=1
        bibtexml+='</bibtex:author>\n'
        bibtexml+='<bibtex:title>'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'</bibtex:title>\n'
        bibtexml+='<bibtex:publisher>'+unicode(self.publisher).encode('latin1','xmlcharrefreplace')+'</bibtex:publisher>\n'
        bibtexml+='<bibtex:year>'+unicode(self.year).encode('latin1','xmlcharrefreplace')+'</bibtex:year>\n'
        if self.volume:
            bibtexml+='<bibtex:volume>'+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'</bibtex:volume>\n'
        if self.location:
            bibtexml+='<bibtex:address>'+unicode(self.location).encode('latin1','xmlcharrefreplace')+'</bibtex:address>\n'
        if self.edition:
            bibtexml+='<bibtex:edition>'+unicode(self.edition).encode('latin1','xmlcharrefreplace')+'</bibtex:edition>\n'
        bibtexml+='</bibtex:book>\n'
        bibtexml+='</bibtex:entry>'
        return bibtexml

# Chapter - inherits from Literature
class Chapter(Literature):
    location = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    edition = models.CharField(max_length=100, blank=True)
    editors = models.CharField(max_length=200, blank=True)
    book_title = models.CharField(max_length=200, blank=True)
    class Meta:
        app_label='legacy_bodb'

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
    
    def bibtexml_format(self):
        bibtex_id='%d' % self.id
        if len(self.authors.all()):
            bibtex_id=self.authors.all()[0].author.last_name+'_'+str(self.id)
        bibtexml='<bibtex:entry bibtex:id="'+bibtex_id+'">\n'
        bibtexml+='<bibtex:inbook>\n'
        bibtexml+='<bibtex:author>'
        i=0
        for author in self.authors.all():
            if i>0:
                bibtexml+='; '
            bibtexml+=unicode(author.author.first_name).encode('latin1','xmlcharrefreplace')
            if author.author.middle_name:
                bibtexml+=' '+unicode(author.author.middle_name).encode('latin1','xmlcharrefreplace')
            bibtexml+=' '+unicode(author.author.last_name).encode('latin1','xmlcharrefreplace')
            i+=1
        bibtexml+='</bibtex:author>\n'
        bibtexml+='<bibtex:title>'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'</bibtex:title>\n'
        bibtexml+='<bibtex:publisher>'+unicode(self.publisher).encode('latin1','xmlcharrefreplace')+'</bibtex:publisher>\n'
        bibtexml+='<bibtex:year>'+unicode(self.year).encode('latin1','xmlcharrefreplace')+'</bibtex:year>\n'
        if self.volume:
            bibtexml+='<bibtex:volume>'+unicode(self.volume).encode('latin1','xmlcharrefreplace')+'</bibtex:volume>\n'
        if self.location:
            bibtexml+='<bibtex:address>'+unicode(self.location).encode('latin1','xmlcharrefreplace')+'</bibtex:address>\n'
        if self.edition:
            bibtexml+='<bibtex:edition>'+unicode(self.edition).encode('latin1','xmlcharrefreplace')+'</bibtex:edition>\n'
        if self.series:
            bibtexml+='<bibtex:series>'+unicode(self.series).encode('latin1','xmlcharrefreplace')+'</bibtex:series>\n'
        bibtexml+='</bibtex:inbook>\n'
        bibtexml+='</bibtex:entry>'
        return bibtexml

# Conference proceedings - inherits from Literature
class Conference(Literature):
    location = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=200)
    volume = models.IntegerField(blank=True, null=True)
    series = models.CharField(max_length=100, blank=True)
    organization = models.CharField(max_length=200)
    class Meta:
        app_label='legacy_bodb'

# Thesis - inherits from Literature
class Thesis(Literature):
    school = models.CharField(max_length=200)
    # When listing multiple records - the plural form of thesis is theses, not thesiss
    class Meta:
        app_label='legacy_bodb'
        verbose_name_plural = 'theses'


# Unpublished - inherits from Literature
class Unpublished(Literature):
    # just so class declaration isn't empty
    class Meta:
        app_label='legacy_bodb'
        ordering=['year']

# export the list of references to the given file_name in the given format
def reference_export(format, references, file_name):
    # open file for writing
    path=settings.MEDIA_ROOT+file_name
    FILE = open(path, 'w')

    if format=='xml':
        FILE.write('<?xml version="1.0" encoding="iso-8859-1"?>\n')
        FILE.write('<bibtex:file xmlns:bibtex="http://bibtexml.sf.net/"\n')
        FILE.write('    xmlns:xsi="http://www.w3.org/2001/XMLSchema-Instance">\n')
    # loop through list of references
    for reference in references:
        # only export journal and book references
        if Journal.objects.filter(id=reference.id):
            reference=Journal.objects.get(id=reference.id)
        elif Book.objects.filter(id=reference.id):
            reference=Book.objects.get(id=reference.id)
        else:
            continue

        # write the reference to the file - each reference type knows how to
        # export itself to endnote and bibtex format
        if format=='endnote':
            FILE.write(reference.endnote_format())
            FILE.write('\n\n\n')
        elif format=='bibtex':
            FILE.write(reference.bibtex_format())
            FILE.write('\n\n')
        elif format=='xml':
            FILE.write(reference.bibtexml_format())
            FILE.write('\n')

    if format=='xml':
        FILE.write('</bibtex:file>')
    FILE.close()
