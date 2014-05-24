from bodb.models import Literature, Journal, Book, Chapter, Author, LiteratureAuthor, Nomenclature, Species, BrainRegion, CoCoMacBrainRegion
from federation.cocomac.search import perform_query
from registration.models import User

def addNomenclature2(id):
    sql='SELECT * FROM BrainMaps WHERE BrainMap=$map'
    result=perform_query(sql, {'map':id})
    map_id_idx=result['fields'].index('ID')
    lit_id_idx=result['fields'].index('ID_Literature')
    map_id=result['data'].values()[0][map_id_idx]
    lit_id=result['data'].values()[0][lit_id_idx]

    lit_sql='SELECT * FROM Literature WHERE ID=%s' % lit_id
    lit_result=perform_query(lit_sql,{})
    type=lit_result['data'].values()[0][lit_result['fields'].index('Journal_Chapter_Book')]
    title=lit_result['data'].values[0][lit_result['fields'].index('Title')]
    year=lit_result['data'].values[0][lit_result['fields'].index('Year')]

    literatureRecs=Literature.objects.filter(title__iexact=title, year=year)
    if literatureRecs:
        literature=literatureRecs[0]
    else:
        literature=None

        if type=='J':
            journal_sql='SELECT * FROM Literature_JournalArticles WHERE ID_Literature=%s' % lit_id
            journal_results=perform_query(journal_sql,{})
            pmid=journal_results['data'].values[0][journal_results['fields'].index('PMID')]
            vol=journal_results['data'].values[0][journal_results['fields'].index('Volume')]
            issue=journal_results['data'].values[0][journal_results['fields'].index('Number')]
            journal=journal_results['data'].values[0][journal_results['fields'].index('Journal')]
            pages=journal_results['data'].values[0][journal_results['fields'].index('Pages')]
            literature=Journal(title=title, year=int(year), journal_name=journal, pages=pages,
                collator=User.objects.get(username='jbonaiuto'), volume=vol, pubmed_id=pmid, issue=issue)

        elif type=='B':
            book_sql='SELECT * FROM Literature_Books WHERE ID_Literature=%s' % lit_id
            book_results=perform_query(book_sql,{})
            publisher=book_results['data'].values[0][book_results['fields'].index('Publisher')]
            location=book_results['data'].values[0][book_results['fields'].index('Place')]
            literature=Book(title=title, year=int(year), publisher=publisher, location=location,
                collator=User.objects.get(username='jbonaiuto'))

        elif type=='C':
            chapter_sql='SELECT * FROM Literature_BookChapters WHERE ID_Literature=%s' % lit_id
            chapter_results=perform_query(chapter_sql,{})
            book_title=chapter_results['data'].values[0][chapter_results['fields'].index('Title_Book')]
            publisher=chapter_results['data'].values[0][chapter_results['fields'].index('Publisher')]
            location=chapter_results['data'].values[0][chapter_results['fields'].index('Place')]
            editors=chapter_results['data'].values[0][chapter_results['fields'].index('Editors')]
            literature=Chapter(title=title, year=int(year), book_title=book_title, location=location,
                publisher=publisher, editors=editors, collator=User.objects.get(username='jbonaiuto'))

        if not literature is None:
            literature.save()

        lit_author_sql='SELECT Literature_Authors.Initials_FirstName, Literature_Authors.LastName, '\
                       'Literature_LinkTable.Position FROM Literature_LinkTable '\
                       'JOIN Literature_Authors ON Literature_LinkTable.ID_Literature_Author=Literature_Authors.ID '\
                       'WHERE Literature_LinkTable.ID_Literature=%s' % lit_id
        lit_author_results=perform_query(lit_author_sql,{})
        first_name_idx=lit_author_results['fields'].index('Initials_FirstName')
        last_name_idx=lit_author_results['fields'].index('LastName')
        order_idx=lit_author_results['fields'].index('Position')
        for lit_author_result in lit_author_results['data'].values():
            first_name=lit_author_result[first_name_idx]
            last_name=lit_author_result[last_name_idx]
            order=lit_author_result[order_idx]
            # Get existing author
            authors=Author.objects.filter(last_name=last_name, first_name=first_name)
            if authors:
                author=authors[0]

            # Create new author
            else:
                author=Author(last_name=last_name, first_name=first_name[0])
                if len(first_name)>1:
                    author.middle_name=first_name[1:]
                author.save()
            oa=LiteratureAuthor(author=author,order=order)
            oa.save()
            literature.authors.add(oa)

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

    species_sql='SELECT MacaqueSpecies FROM Methods_Animals_Details JOIN Methods_Animals ON Methods_Animals.ID=Methods_Animals_Details.ID_Methods_Animals JOIN Methods ON Methods.ID=Methods_Animals.ID_Method WHERE Methods.ID_Literature=%s' % lit_id
    species_results=perform_query(species_sql,{})
    for species_result in species_results['data'].values():
        name=species_result[species_result['fields'].index('MacaqueSpecies')]
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

    brain_region_sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite, BrainMaps_BrainSiteAcronyms.Acronym, BrainMaps_BrainSiteAcronyms.FullName FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE BrainMaps_BrainSites.ID_BrainMap=%s' % map_id
    brain_region_results=perform_query(brain_region_sql,{})
    for brain_region_result in brain_region_results['data'].values():
        id=brain_region_result[brain_region_results['fields'].index('BrainSite')]
        abbrev=brain_region_result[brain_region_results['fields'].index('Acronym')]
        name=brain_region_result[brain_region_results['fields'].index('FullName')]
        addRegion2(nomenclature, id, abbrev, name)
    return nomenclature

# Add region
def addRegion2(nomenclature, id, abbrev, name):
    if not BrainRegion.objects.filter(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region'):
        region=BrainRegion(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region')
        region.save()
    else:
        region=BrainRegion.objects.get(nomenclature=nomenclature, name=name, abbreviation=abbrev, brain_region_type='neural region')

    if not CoCoMacBrainRegion.objects.filter(brain_region=region, cocomac_id=id):
        mappedRegion=CoCoMacBrainRegion(brain_region=region, cocomac_id=id)
        mappedRegion.save()

    return region