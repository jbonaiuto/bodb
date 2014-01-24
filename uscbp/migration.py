from django.db.models.query_utils import Q
from django.db import connection
import os
import shutil
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from bodb.models import Forum
import bodb.models.workspace as workspace
from guardian.shortcuts import assign_perm
import legacy.old_models.workspace as legacy_workspace
import legacy.old_models.atlas as legacy_atlas
import bodb.models.atlas as new_atlas
import legacy.old_models.literature as legacy_literature
import bodb.models.literature as new_literature
import bodb.models.bop as new_bop
import legacy.old_models.document as legacy_document
import bodb.models.document as new_document
import bodb.models.sed as new_sed
import bodb.models.ssr as new_ssr
import bodb.models.model as new_model
import legacy.old_models.messaging as legacy_messaging
import bodb.models.messaging as new_messaging
import bodb.models.workspace as new_workspace
from legacy.tagging.utils import parse_tag_input
from taggit.models import Tag
from uscbp import settings

def migration(legacy_img_dir, new_media_dir):
    import_groups()
    import_users(legacy_img_dir, new_media_dir)
    import_authors()
    import_literature()
    import_atlases()
    import_seds(legacy_img_dir, new_media_dir)
    import_bops(legacy_img_dir, new_media_dir)
    import_ssrs(legacy_img_dir, new_media_dir)
    import_models(legacy_img_dir, new_media_dir)
    import_related_models()
    import_messages()
    import_workspaces()
    import_saved_coord_selections()

def import_groups():
    print('importing groups')
    # Get old groups from DB
    old_groups=Group.objects.using('legacy').all()
    for old_group in old_groups:

        # Create new group
        new_group=Group(id=old_group.id, name=old_group.name)
        new_group.save()

        # Go through old permissions
        for old_permission in old_group.permissions.db_manager('legacy').all():

            # Create permission if doesnt exist
            if not Permission.objects.filter(codename=old_permission.codename).count():
                old_ct=old_permission.content_type

                # Create content type if doesnt exist
                if not ContentType.objects.filter(name = old_ct.name, app_label=old_ct.app_label,
                    model=old_ct.model).count():
                    ct=ContentType(name = old_ct.name, app_label=old_ct.app_label, model=old_ct.model)
                    ct.save()
                else:
                    ct=ContentType.objects.get(name = old_ct.name, app_label=old_ct.app_label, model=old_ct.model)

                # Create new permission
                new_permission=Permission(
                    name = old_permission.name,
                    content_type = ct,
                    codename = old_permission.codename
                )
                new_permission.save()
            else:
                new_permission=Permission.objects.get(codename=old_permission.codename)

            # Add permission to group
            new_group.permissions.add(new_permission)


def import_users(legacy_img_dir, new_media_dir):
    print('importing users')

    # Get old users from DB
    old_users=User.objects.using('legacy').all()
    for old_user in old_users:

        # Create new user
        new_user=User(
            id=old_user.id,
            username=old_user.username,
            first_name=old_user.first_name,
            last_name=old_user.last_name,
            email=old_user.email,
            is_staff=old_user.is_staff,
            is_active=old_user.is_active,
            is_superuser=old_user.is_superuser,
            date_joined=old_user.date_joined,
            password=old_user.password,
            last_login=old_user.last_login
        )
        new_user.save()

        # Go through old permissions
        for old_permission in old_user.user_permissions.db_manager('legacy').all():

            # Create permission if doesnt exist
            if not Permission.objects.filter(codename=old_permission.codename).count():
                old_ct=old_permission.content_type

                # Create content type if doesnt exist
                if not ContentType.objects.filter(name = old_ct.name, app_label=old_ct.app_label,
                    model=old_ct.model).count():
                    ct=ContentType(name = old_ct.name, app_label=old_ct.app_label, model=old_ct.model)
                    ct.save()
                else:
                    ct=ContentType.objects.get(name = old_ct.name, app_label=old_ct.app_label, model=old_ct.model)

                # Create new permission
                new_permission=Permission(
                    name = old_permission.name,
                    content_type = ct,
                    codename = old_permission.codename
                )
                new_permission.save()
            else:
                new_permission=Permission.objects.get(codename=old_permission.codename)

            # Add permission to user
            new_user.user_permissions.add(new_permission)

        # Add groups to user
        for old_group in old_user.groups.db_manager('legacy').all():
            new_group=Group.objects.get(id=old_group.id)
            new_user.groups.add(new_group)

        # If the user has a profile
        if legacy_workspace.BodbProfile.objects.using('legacy').filter(user=old_user).count():
            old_profile=legacy_workspace.BodbProfile.objects.using('legacy').get(user=old_user)

            # Create new profile
            new_profile=workspace.BodbProfile(
                id=old_profile.id,
                user=new_user,
                new_message_notify=old_profile.new_message_notify,
                affiliation=old_profile.affiliation,
                notification_preference=old_profile.notification_preference
            )
            new_profile.save()

            # Copy avatar image
            gallery=old_profile.gallery
            if gallery.photos.db_manager('legacy').all().count():
                photo=gallery.photos.db_manager('legacy').all()[0]
                if os.path.exists(os.path.join(legacy_img_dir,photo.image_filename())):
                    shutil.copyfile(os.path.join(legacy_img_dir,photo.image_filename()),
                        os.path.join(new_media_dir,'avatars',photo.image_filename()))
                    new_profile.avatar.name=os.path.join('avatars',photo.image_filename())
                    new_profile.save()
        else:
            new_workspace.create_user_profile(new_user)


def import_authors():
    print('importing authors')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_author(id, first_name, middle_name, last_name, email, homepage, alias, creation_time) (SELECT id, first_name, middle_name, last_name, email, homepage, alias, creation_time FROM %s.legacy_bodb_author)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()


def import_literature_authors(new_lit_obj, old_lit_obj):
    for old_author in old_lit_obj.authors.db_manager('legacy').all():
        new_author = new_literature.Author.objects.get(id=old_author.author.id)
        ordered_author = new_literature.LiteratureAuthor(author=new_author, order=old_author.order)
        ordered_author.save()
        new_lit_obj.authors.add(ordered_author)


def import_literature():
    print('importing literature')
    # import journals
    old_journals=legacy_literature.Journal.objects.using('legacy').all()
    for old_journal in old_journals:
        new_journal=new_literature.Journal(
            id=old_journal.id,
            journal_name = old_journal.journal_name,
            volume = old_journal.volume,
            issue = old_journal.issue,
            pages = old_journal.pages,
            pubmed_id=old_journal.pubmed_id,
            title = old_journal.title,
            year = old_journal.year,
            url = old_journal.url,
            language = old_journal.language,
            annotation = old_journal.annotation,
            creation_time = old_journal.creation_time,
            collator=User.objects.get(id=old_journal.collator.id)
        )
        new_journal.save()
        import_literature_authors(new_journal, old_journal)

    # import books
    old_books=legacy_literature.Book.objects.using('legacy').all()
    for old_book in old_books:
        new_book=new_literature.Book(
            id=old_book.id,
            location = old_book.location,
            publisher = old_book.publisher,
            volume = old_book.volume,
            series = old_book.series,
            edition = old_book.edition,
            editors = old_book.editors,
            pubmed_id=old_book.pubmed_id,
            title = old_book.title,
            year = old_book.year,
            url = old_book.url,
            language = old_book.language,
            annotation = old_book.annotation,
            creation_time = old_book.creation_time,
            collator=User.objects.get(id=old_book.collator.id)
        )
        new_book.save()
        import_literature_authors(new_book, old_book)

    # import chapters
    old_chapters=legacy_literature.Chapter.objects.using('legacy').all()
    for old_chapter in old_chapters:
        new_chapter=new_literature.Chapter(
            id=old_chapter.id,
            location = old_chapter.location,
            publisher = old_chapter.publisher,
            volume = old_chapter.volume,
            series = old_chapter.series,
            edition = old_chapter.edition,
            editors = old_chapter.editors,
            book_title = old_chapter.book_title,
            pubmed_id=old_chapter.pubmed_id,
            title = old_chapter.title,
            year = old_chapter.year,
            url = old_chapter.url,
            language = old_chapter.language,
            annotation = old_chapter.annotation,
            creation_time = old_chapter.creation_time,
            collator=User.objects.get(id=old_chapter.collator.id)
        )
        new_chapter.save()
        import_literature_authors(new_chapter, old_chapter)

    # import conferences
    old_conferences=legacy_literature.Conference.objects.using('legacy').all()
    for old_conference in old_conferences:
        new_conference=new_literature.Conference(
            id=old_conference.id,
            location = old_conference.location,
            publisher = old_conference.publisher,
            volume = old_conference.volume,
            series = old_conference.series,
            organization = old_conference.organization,
            pubmed_id=old_conference.pubmed_id,
            title = old_conference.title,
            year = old_conference.year,
            url = old_conference.url,
            language = old_conference.language,
            annotation = old_conference.annotation,
            creation_time = old_conference.creation_time,
            collator=User.objects.get(id=old_conference.collator.id)
        )
        new_conference.save()
        import_literature_authors(new_conference, old_conference)

    # import theses
    old_theses=legacy_literature.Thesis.objects.using('legacy').all()
    for old_thesis in old_theses:
        new_thesis=new_literature.Thesis(
            id=old_thesis.id,
            school=old_thesis.school,
            pubmed_id=old_thesis.pubmed_id,
            title = old_thesis.title,
            year = old_thesis.year,
            url = old_thesis.url,
            language = old_thesis.language,
            annotation = old_thesis.annotation,
            creation_time = old_thesis.creation_time,
            collator=User.objects.get(id=old_thesis.collator.id)
        )
        new_thesis.save()
        import_literature_authors(new_thesis, old_thesis)

    # import unpublished
    old_unpublishes=legacy_literature.Unpublished.objects.using('legacy').all()
    for old_unpublished in old_unpublishes:
        new_unpublished=new_literature.Unpublished(
            id=old_unpublished.id,
            pubmed_id=old_unpublished.pubmed_id,
            title = old_unpublished.title,
            year = old_unpublished.year,
            url = old_unpublished.url,
            language = old_unpublished.language,
            annotation = old_unpublished.annotation,
            creation_time = old_unpublished.creation_time,
            collator=User.objects.get(id=old_unpublished.collator.id)
        )
        new_unpublished.save()
        import_literature_authors(new_unpublished, old_unpublished)

    # import generic literature
    old_generics=legacy_literature.Literature.objects.using('legacy').filter(journal__isnull=True,book__isnull=True,
        chapter__isnull=True,conference__isnull=True,thesis__isnull=True,unpublished__isnull=True)
    for old_generic in old_generics:
        new_generic=new_literature.Unpublished(
            id=old_generic.id,
            pubmed_id=old_generic.pubmed_id,
            title = old_generic.title,
            year = old_generic.year,
            url = old_generic.url,
            language = old_generic.language,
            annotation = old_generic.annotation,
            creation_time = old_generic.creation_time,
            collator=User.objects.get(id=old_generic.collator.id)
        )
        new_generic.save()
        import_literature_authors(new_generic, old_generic)


def import_atlases():
    print('importing species')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_species(id,genus_name,species_name,common_name,creation_time) (SELECT id,genus_name,species_name,common_name,creation_time FROM %s.legacy_bodb_species)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing nomenclatures')
    # Get old nomenclatures from db
    old_nomenclatures=legacy_atlas.Nomenclature.objects.using('legacy').all()
    for old_nomenclature in old_nomenclatures:
        # Create new nomenclature
        new_nomenclature=new_atlas.Nomenclature(
            id=old_nomenclature.id,
            lit = new_literature.Literature.objects.get(id=old_nomenclature.lit.id),
            name = old_nomenclature.name,
            version = old_nomenclature.version,
            creation_time = old_nomenclature.creation_time
        )
        new_nomenclature.save()

        # Add species to nomenclature
        for species in old_nomenclature.species.db_manager('legacy').all():
            new_nomenclature.species.add(new_atlas.Species.objects.get(id=species.id))

    print('importing coord spaces')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_coordinatespace(id, name) (SELECT id, name FROM %s.legacy_bodb_coordinatespace)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing atlases')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_atlas(id,file) (SELECT id, file FROM %s.legacy_bodb_atlas)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing 3d coords')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_threedcoord(id,x,y,z) (SELECT id,x,y,z FROM %s.legacy_bodb_threedcoord)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing brain regions')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_brainregion(id, nomenclature_id, name, abbreviation, brain_region_type) (SELECT id, nomenclature_id, name, abbreviation, brain_region_type FROM %s.legacy_bodb_brainregion)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()
    old_brain_regions=legacy_atlas.BrainRegion.objects.using('legacy').all()
    for old_brain_region in old_brain_regions:
        if old_brain_region.parent_region is not None:
            new_brain_region=new_atlas.BrainRegion.objects.get(id=old_brain_region.id)
            new_brain_region.parent_region=new_atlas.BrainRegion.objects.get(id=old_brain_region.parent_region.id)
            new_brain_region.save()

    print('importing brain region volumes')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_brainregionvolume(id, brain_region_id, coord_space_id) (SELECT id, brain_region_id, coord_space_id FROM %s.legacy_bodb_brainregionvolume)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing brain region volume coords')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_brainregionvolume_coords(id, brainregionvolume_id, threedcoord_id) (SELECT id, brainregionvolume_id, threedcoord_id FROM %s.legacy_bodb_brainregionvolume_coords)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing cocomac regions')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_cocomacbrainregion(id, brain_region_id,cocomac_id) (SELECT id, brain_region_id, cocomac_id FROM %s.legacy_bodb_cocomacbrainregion)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()

    print('importing brain navigator regions')
    cursor=connection.cursor()
    cursor.execute('INSERT INTO %s.bodb_brainnavigatorbrainregion(id,brain_region_id,color) (SELECT id, brain_region_id, color FROM %s.legacy_bodb_brainnavigatorbrainregion)' %
                   (settings.DATABASES['default']['NAME'],settings.DATABASES['legacy']['NAME']))
    cursor.close()


def import_figures(old_obj, new_obj, legacy_img_dir, new_media_dir):
    for i, photo in enumerate(old_obj.gallery.photos.db_manager('legacy').all()):
        if os.path.exists(os.path.join(legacy_img_dir, photo.image_filename())):
            shutil.copyfile(os.path.join(legacy_img_dir, photo.image_filename()),
                os.path.join(new_media_dir, 'figures', photo.image_filename()))
            df = new_document.DocumentFigure(
                document=new_obj,
                title=photo.title,
                caption=photo.caption,
                order=i
            )
            df.figure.name = os.path.join('figures', photo.image_filename())
            df.save()


def import_related_brain_regions(new_obj, old_obj):
    for old_related_region in old_obj.related_brain_regions.db_manager('legacy').all():
        new_related_region = new_atlas.RelatedBrainRegion(
            id=old_related_region.id,
            document=new_obj,
            brain_region=new_atlas.BrainRegion.objects.get(id=old_related_region.brain_region.id),
            relationship=old_related_region.relationship
        )
        new_related_region.save()


def import_building_seds(new_obj, old_obj):
    for old_buildsed in old_obj.building_seds.db_manager('legacy').all():
        new_buildsed = new_sed.BuildSED(
            id=old_buildsed.id,
            sed=new_sed.SED.objects.get(id=old_buildsed.sed.id),
            document=new_obj,
            relationship=old_buildsed.relationship,
            relevance_narrative=old_buildsed.relevance_narrative
        )
        new_buildsed.save()


def import_related_literature(new_obj, old_obj):
    for lit in old_obj.literature.db_manager('legacy').all():
        new_obj.literature.add(new_literature.Literature.objects.get(id=lit.id))


def import_bops(legacy_img_dir, new_media_dir):
    print('importing bops')
    old_bops=legacy_document.BOP.objects.using('legacy').all()
    for old_bop in old_bops:
        new_bp=new_bop.BOP(
            id=old_bop.id,
            collator = User.objects.get(id=old_bop.collator.id),
            title = old_bop.title,
            brief_description = old_bop.brief_description,
            narrative = old_bop.narrative,
            draft = old_bop.draft,
            public = old_bop.public,
            creation_time = old_bop.creation_time,
            last_modified_time = old_bop.last_modified_time,
            last_modified_by=User.objects.get(id=old_bop.collator.id)
        )
        new_bp.save()
        import_figures(old_bop, new_bp, legacy_img_dir, new_media_dir)
        import_related_literature(new_bp, old_bop)
        import_tags(new_bp, old_bop)
        import_related_brain_regions(new_bp, old_bop)
        import_building_seds(new_bp, old_bop)
    for old_bop in old_bops:
        if not old_bop.parent is None:
            new_bp=new_bop.BOP.objects.get(id=old_bop.id)
            new_bp.parent=new_bop.BOP.objects.get(id=old_bop.parent.id)
            new_bp.save()

        for old_related_bop in old_bop.related_bops.db_manager('legacy').all():
            new_related_bop=new_bop.RelatedBOP(
                id=old_related_bop.id,
                document=new_bop.BOP.objects.get(id=old_bop.id),
                bop=new_bop.BOP.objects.get(id=old_related_bop.bop.id),
                relevance_narrative=old_related_bop.relationship
            )
            new_related_bop.save()


def import_tags(new_obj, old_obj):
    old_tags=parse_tag_input(old_obj.tags)
    for old_tag in old_tags:
        if Tag.objects.filter(name=old_tag).count():
            new_obj.tags.add(Tag.objects.get(name=old_tag))
        else:
            new_obj.tags.add(old_tag)


def import_seds(legacy_img_dir, new_media_dir):
    print('importing generic seds')
    # generic
    old_seds=legacy_document.SED.objects.using('legacy').filter(Q(Q(type='generic') | Q(type='')))
    for old_sed in old_seds:
        new_sd=new_sed.SED(
            id=old_sed.id,
            type='generic',
            collator = User.objects.get(id=old_sed.collator.id),
            title = old_sed.title,
            brief_description = old_sed.brief_description,
            narrative = old_sed.narrative,
            draft = old_sed.draft,
            public = old_sed.public,
            creation_time = old_sed.creation_time,
            last_modified_time = old_sed.last_modified_time,
            last_modified_by=User.objects.get(id=old_sed.collator.id)
        )
        new_sd.save()
        import_figures(old_sed, new_sd, legacy_img_dir, new_media_dir)
        import_related_literature(new_sd, old_sed)
        import_related_brain_regions(new_sd, old_sed)
        import_tags(new_sd, old_sed)

    # connectivity
    print('importing connectivity seds')
    old_seds=legacy_document.ConnectivitySED.objects.using('legacy').all()
    for old_sed in old_seds:
        new_sd=new_sed.CoCoMacConnectivitySED(
            id=old_sed.id,
            type='connectivity',
            collator = User.objects.get(id=old_sed.collator.id),
            title = old_sed.title,
            brief_description = old_sed.brief_description,
            narrative = old_sed.narrative,
            draft = old_sed.draft,
            public = old_sed.public,
            creation_time = old_sed.creation_time,
            last_modified_time = old_sed.last_modified_time,
            last_modified_by=User.objects.get(id=old_sed.collator.id),
            source_region=new_atlas.BrainRegion.objects.get(id=old_sed.source_region.id),
            target_region=new_atlas.BrainRegion.objects.get(id=old_sed.target_region.id)
        )
        new_sd.save()
        import_figures(old_sed, new_sd, legacy_img_dir, new_media_dir)
        import_related_literature(new_sd, old_sed)
        import_related_brain_regions(new_sd, old_sed)
        import_tags(new_sd, old_sed)


    # erp
    print('importing erp seds')
    old_seds=legacy_document.ErpSED.objects.using('legacy').all()
    for old_sed in old_seds:
        new_sd=new_sed.ERPSED(
            id=old_sed.id,
            type='event related potential',
            collator = User.objects.get(id=old_sed.collator.id),
            title = old_sed.title,
            brief_description = old_sed.brief_description,
            narrative = old_sed.narrative,
            draft = old_sed.draft,
            public = old_sed.public,
            creation_time = old_sed.creation_time,
            last_modified_time = old_sed.last_modified_time,
            last_modified_by=User.objects.get(id=old_sed.collator.id),
            cognitive_paradigm=old_sed.cognitive_paradigm,
            sensory_modality=old_sed.sensory_modality,
            response_modality=old_sed.response_modality,
            control_condition=old_sed.control_condition,
            experimental_condition=old_sed.experimental_condition
        )
        new_sd.save()
        old_erp_components=legacy_document.ErpSEDComponent.objects.using('legacy').filter(erp_sed=old_sed)
        for old_erp_component in old_erp_components:
            new_erp_component=new_sed.ERPComponent(
                id=old_erp_component.id,
                erp_sed=new_sd,
                component_name=old_erp_component.component_name,
                latency_peak=old_erp_component.latency_peak,
                latency_peak_type=old_erp_component.latency_peak_type,
                latency_onset=old_erp_component.latency_onset,
                amplitude_peak=old_erp_component.amplitude_peak,
                amplitude_mean=old_erp_component.amplitude_mean,
                scalp_region=old_erp_component.scalp_region,
                electrode_cap=old_erp_component.electrode_cap,
                electrode_name=old_erp_component.electrode_name,
                source=old_erp_component.source,
                interpretation=old_erp_component.interpretation
            )
            new_erp_component.save()
        import_figures(old_sed, new_sd, legacy_img_dir, new_media_dir)
        import_related_literature(new_sd, old_sed)
        import_related_brain_regions(new_sd, old_sed)
        import_tags(new_sd, old_sed)

    # BredeBrainImagingSED
    print('importing brede brain imaging seds')
    old_seds=legacy_document.BredeBrainImagingSED.objects.using('legacy').all()
    for old_sed in old_seds:
        new_sd=new_sed.BredeBrainImagingSED(
            id=old_sed.id,
            type='brain imaging',
            collator = User.objects.get(id=old_sed.collator.id),
            title = old_sed.title,
            brief_description = old_sed.brief_description,
            narrative = old_sed.narrative,
            draft = old_sed.draft,
            public = old_sed.public,
            creation_time = old_sed.creation_time,
            last_modified_time = old_sed.last_modified_time,
            last_modified_by=User.objects.get(id=old_sed.collator.id),
            method = old_sed.method,
            control_condition = old_sed.control_condition,
            experimental_condition = old_sed.experimental_condition,
            coord_space = new_atlas.CoordinateSpace.objects.get(id=old_sed.coord_space.id),
            core_header_1 = old_sed.core_header_1,
            core_header_2 = old_sed.core_header_2,
            core_header_3 = old_sed.core_header_3,
            core_header_4 = old_sed.core_header_4,
            extra_header = old_sed.extra_header,
            woexp=old_sed.woexp
        )
        new_sd.save()
        old_sed_coords=legacy_document.SEDCoord.objects.using('legacy').filter(sed=old_sed)
        for old_sed_coord in old_sed_coords:
            new_sed_coord=new_sed.SEDCoord(
                id=old_sed_coord.id,
                sed=new_sd,
                coord=new_atlas.ThreeDCoord.objects.get(id=old_sed_coord.coord.id),
                rcbf = old_sed_coord.rcbf,
                statistic_value = old_sed_coord.statistic_value,
                statistic = old_sed_coord.statistic,
                hemisphere = old_sed_coord.hemisphere,
                named_brain_region = old_sed_coord.named_brain_region,
                extra_data = old_sed_coord.extra_data
            )
            new_sed_coord.save()
        import_figures(old_sed, new_sd, legacy_img_dir, new_media_dir)
        import_related_literature(new_sd, old_sed)
        import_related_brain_regions(new_sd, old_sed)
        import_tags(new_sd, old_sed)

    # BrainImagingSED
    print('importing brain imaging seds')
    old_seds=legacy_document.BrainImagingSED.objects.using('legacy').filter(bredebrainimagingsed__isnull=True)
    for old_sed in old_seds:
        new_sd=new_sed.BrainImagingSED(
            id=old_sed.id,
            type='brain imaging',
            collator = User.objects.get(id=old_sed.collator.id),
            title = old_sed.title,
            brief_description = old_sed.brief_description,
            narrative = old_sed.narrative,
            draft = old_sed.draft,
            public = old_sed.public,
            creation_time = old_sed.creation_time,
            last_modified_time = old_sed.last_modified_time,
            last_modified_by=User.objects.get(id=old_sed.collator.id),
            method = old_sed.method,
            control_condition = old_sed.control_condition,
            experimental_condition = old_sed.experimental_condition,
            coord_space = new_atlas.CoordinateSpace.objects.get(id=old_sed.coord_space.id),
            core_header_1 = old_sed.core_header_1,
            core_header_2 = old_sed.core_header_2,
            core_header_3 = old_sed.core_header_3,
            core_header_4 = old_sed.core_header_4,
            extra_header = old_sed.extra_header
        )
        new_sd.save()
        old_sed_coords=legacy_document.SEDCoord.objects.using('legacy').filter(sed=old_sed)
        for old_sed_coord in old_sed_coords:
            new_sed_coord=new_sed.SEDCoord(
                id=old_sed_coord.id,
                sed=new_sd,
                coord=new_atlas.ThreeDCoord.objects.get(id=old_sed_coord.coord.id),
                rcbf = old_sed_coord.rcbf,
                statistic_value = old_sed_coord.statistic_value,
                statistic = old_sed_coord.statistic,
                hemisphere = old_sed_coord.hemisphere,
                named_brain_region = old_sed_coord.named_brain_region,
                extra_data = old_sed_coord.extra_data
            )
            new_sed_coord.save()
        import_figures(old_sed, new_sd, legacy_img_dir, new_media_dir)
        import_related_literature(new_sd, old_sed)
        import_related_brain_regions(new_sd, old_sed)
        import_tags(new_sd, old_sed)


def import_ssrs(legacy_img_dir, new_media_dir):
    print('importing ssrs')
    old_ssrs=legacy_document.SSR.objects.using('legacy').all()
    for old_ssr in old_ssrs:
        new_sr=new_ssr.SSR(
            id=old_ssr.id,
            type='generic',
            collator = User.objects.get(id=old_ssr.collator.id),
            title = old_ssr.title,
            brief_description = old_ssr.brief_description,
            narrative = old_ssr.narrative,
            draft = old_ssr.draft,
            public = old_ssr.public,
            creation_time = old_ssr.creation_time,
            last_modified_time = old_ssr.last_modified_time,
            last_modified_by=User.objects.get(id=old_ssr.collator.id),
        )
        new_sr.save()
        import_figures(old_ssr, new_sr, legacy_img_dir, new_media_dir)
        import_tags(new_sr, old_ssr)


def import_vars(new_obj, old_obj):
    old_vars = legacy_document.Variable.objects.using('legacy').filter(module=old_obj)
    for old_var in old_vars:
        new_var = new_model.Variable(
            id=old_var.id,
            module=new_obj,
            var_type=old_var.var_type,
            data_type=old_var.data_type,
            name=old_var.name,
            description=old_var.description
        )
        new_var.save()


def import_models(legacy_img_dir, new_media_dir):
    print('importing models')
    old_models=legacy_document.Model.objects.using('legacy').all()
    for old_model in old_models:
        new_mod=new_model.Model(
            id=old_model.id,
            collator = User.objects.get(id=old_model.collator.id),
            title = old_model.title,
            brief_description = old_model.brief_description,
            narrative = old_model.narrative,
            draft = old_model.draft,
            public = old_model.public,
            creation_time = old_model.creation_time,
            last_modified_time = old_model.last_modified_time,
            last_modified_by=User.objects.get(id=old_model.collator.id),
            execution_url = old_model.execution_url,
            documentation_url = old_model.documentation_url,
            description_url = old_model.description_url,
            simulation_url = old_model.simulation_url
        )
        new_mod.save()
        # figures
        import_figures(old_model, new_mod, legacy_img_dir, new_media_dir)
        # authors
        for old_author in old_model.authors.db_manager('legacy').all():
            new_author=new_literature.Author.objects.get(id=old_author.author.id)
            ordered_author=new_model.ModelAuthor(author=new_author,order=old_author.order)
            ordered_author.save()
            new_mod.authors.add(ordered_author)
        # literature
        import_related_literature(new_mod, old_model)
        # related bops
        for old_related_bop in old_model.related_bops.db_manager('legacy').all():
            new_related_bop=new_bop.RelatedBOP(
                id=old_related_bop.id,
                document=new_mod,
                bop=new_bop.BOP.objects.get(id=old_related_bop.bop.id),
                relevance_narrative=old_related_bop.relationship
            )
            new_related_bop.save()
        # building_seds
        import_building_seds(new_mod, old_model)
        # testing_seds
        for old_testsed in old_model.testing_seds.db_manager('legacy').all():
            new_testsed=new_sed.TestSED(
                id=old_testsed.id,
                model=new_mod,
                sed=new_sed.SED.objects.get(id=old_testsed.sed.id),
                relationship=old_testsed.relationship,
                relevance_narrative=old_testsed.brief_description
            )
            new_testsed.save()
            new_testsedssr=new_sed.TestSEDSSR(
                test_sed=new_testsed,
                ssr=new_ssr.SSR.objects.get(id=old_testsed.ssr.id)
            )
            new_testsedssr.save()

        # predictions
        for old_prediction in old_model.predictions.db_manager('legacy').all():
            new_prediction=new_ssr.Prediction(
                id=old_prediction.id,
                model=new_mod,
                collator = User.objects.get(id=old_prediction.collator.id),
                title = old_prediction.title,
                brief_description = old_prediction.brief_description,
                narrative = old_prediction.narrative,
                draft = old_prediction.draft,
                public = old_prediction.public,
                creation_time = old_prediction.creation_time,
                last_modified_time = old_prediction.last_modified_time,
                last_modified_by=User.objects.get(id=old_prediction.collator.id),
            )
            new_prediction.save()
            old_prediction_ssrs=old_prediction.ssrs.db_manager('legacy').all()
            for ssr in old_prediction_ssrs:
                new_predictionssr=new_ssr.PredictionSSR(
                    prediction=new_prediction,
                    ssr=new_ssr.SSR.objects.get(id=ssr.id)
                )
                new_predictionssr.save()
            import_tags(new_prediction, old_prediction)

        cursor=connection.cursor()
        cursor.execute('UPDATE %s.bodb_variable SET var_type="Input" WHERE var_type="input"' % settings.DATABASES['default']['NAME'])
        cursor.execute('UPDATE %s.bodb_variable SET var_type="Output" WHERE var_type="output"' % settings.DATABASES['default']['NAME'])
        cursor.execute('UPDATE %s.bodb_variable SET var_type="State" WHERE var_type="state"' % settings.DATABASES['default']['NAME'])
        cursor.close()

        # related brain regions
        import_related_brain_regions(new_mod, old_model)

        # tags
        import_tags(new_mod, old_model)

        # submodules
        import_submodules(old_model, new_mod, legacy_img_dir, new_media_dir)

        # inputs, outputs, states
        import_vars(new_mod, old_model)


def import_submodules(old_parent, new_parent, legacy_img_dir, new_media_dir):
    for old_submodule in old_parent.submodules.db_manager('legacy').all():
        old_module=old_submodule.module
        new_module=new_model.Module(
            id=old_module.id,
            parent=new_parent,
            collator = User.objects.get(id=old_module.collator.id),
            title = old_module.title,
            brief_description = old_module.brief_description,
            narrative = old_module.narrative,
            draft = old_module.draft,
            public = old_module.public,
            creation_time = old_module.creation_time,
            last_modified_time = old_module.last_modified_time,
            last_modified_by=User.objects.get(id=old_module.collator.id)
        )
        new_module.save()
        # figures
        import_figures(old_module, new_module, legacy_img_dir, new_media_dir)
        # inputs, outputs, states
        import_vars(new_module, old_module)
        import_submodules(old_module,new_module,legacy_img_dir,new_media_dir)


def import_related_models():
    print('importing related models')
    old_bops=legacy_document.BOP.objects.using('legacy').all()
    for old_bop in old_bops:
        for old_related_model in old_bop.related_models.db_manager('legacy').all():
            new_related_model=new_model.RelatedModel(
                document=new_bop.BOP.objects.get(id=old_bop.id),
                model=new_model.Model.objects.get(id=old_related_model.model.id),
                relationship=old_related_model.relationship
            )
            new_related_model.save()
    old_models=legacy_document.Model.objects.using('legacy').all()
    for old_model in old_models:
        for old_related_model in old_model.related_models.db_manager('legacy').all():
            new_related_model=new_model.RelatedModel(
                document=new_model.Model.objects.get(id=old_model.id),
                model=new_model.Model.objects.get(id=old_related_model.model.id),
                relationship=old_related_model.relationship
            )
            new_related_model.save()


def import_messages():
    print('importing messages')
    old_msgs=legacy_messaging.Message.objects.using('legacy').all()
    for old_msg in old_msgs:
        new_msg=new_messaging.Message(
            id=old_msg.id,
            recipient=User.objects.get(id=old_msg.recipient.id),
            subject=old_msg.subject,
            text=old_msg.text,
            read=old_msg.read,
            sent=old_msg.sent
        )
        if old_msg.sender is not None:
            new_msg.sender=User.objects.get(id=old_msg.sender.id)
        new_msg.save()

    print('importing user subscriptions')
    old_usr_subs=legacy_messaging.UserSubscription.objects.using('legacy').all()
    for old_usr_sub in old_usr_subs:
        new_usr_sub=new_messaging.UserSubscription(
            id=old_usr_sub.id,
            subscribed_to_user=User.objects.get(id=old_usr_sub.subscribed_to_user.id),
            user = User.objects.get(id=old_usr_sub.user.id),
            model_type = old_usr_sub.model_type,
            keywords = old_usr_sub.keywords
        )
        new_usr_sub.save()

    print('importing subscriptions')
    old_subs=legacy_messaging.Subscription.objects.using('legacy').filter(usersubscription__isnull=True)
    for old_sub in old_subs:
        new_sub=new_messaging.Subscription(
            id=old_sub.id,
            user = User.objects.get(id=old_sub.user.id),
            model_type = old_sub.model_type,
            keywords = old_sub.keywords
        )
        new_sub.save()


def import_workspaces():
    print('importing workspaces')
    old_workspaces=legacy_workspace.Workspace.objects.using('legacy').all()
    for old_workspace in old_workspaces:
        workspace_forum=Forum()
        workspace_forum.save()
        new_space=new_workspace.Workspace(
            id=old_workspace.id,
            created_by=User.objects.get(id=old_workspace.admin.id),
            group=Group.objects.get(id=old_workspace.group.id),
            title=old_workspace.title,
            description=old_workspace.description,
            created_date=old_workspace.created_date,
            forum=workspace_forum
        )
        new_space.save()
        for model in old_workspace.related_models.db_manager('legacy').all():
            new_space.related_models.add(new_model.Model.objects.get(id=model.id))
        for bop in old_workspace.related_bops.db_manager('legacy').all():
            new_space.related_bops.add(new_bop.BOP.objects.get(id=bop.id))
        for sed in old_workspace.related_seds.db_manager('legacy').all():
            new_space.related_seds.add(new_sed.SED.objects.get(id=sed.id))
        for ssr in old_workspace.related_ssrs.db_manager('legacy').all():
            new_space.related_ssrs.add(new_ssr.SSR.objects.get(id=ssr.id))
        new_space.admin_users.add(new_space.created_by)
        for permission_code,permission_name in new_workspace.Workspace._meta.permissions:
            assign_perm(permission_code,new_space.created_by,new_space)

    for old_user in User.objects.using('legacy').all():
        new_user=User.objects.get(id=old_user.id)
        if legacy_workspace.BodbProfile.objects.using('legacy').filter(user=old_user).count():
            old_profile=legacy_workspace.BodbProfile.objects.using('legacy').get(user=old_user)
            new_profile=new_user.get_profile()
            new_profile.active_workspace=new_workspace.Workspace.objects.get(id=old_profile.active_workspace.id)
            new_profile.save()


def import_saved_coord_selections():
    print('importing saved coord selections')
    old_selections=legacy_document.SavedSEDCoordSelection.objects.using('legacy').all()
    for old_selection in old_selections:
        new_selection=new_sed.SavedSEDCoordSelection(
            id=old_selection.id,
            user=User.objects.get(id=old_selection.user.id),
            name=old_selection.name,
            description=old_selection.description,
            last_modified_by=User.objects.get(id=old_selection.user.id)
        )
        new_selection.save()
        workspace=new_workspace.Workspace.objects.get(id=old_selection.workspace.id)
        workspace.saved_coordinate_selections.add(new_selection)

    print('importing selected coords')
    old_selected_coords=legacy_document.SelectedSEDCoord.objects.using('legacy').all()
    for old_selected_coord in old_selected_coords:
        new_selected_coord=new_sed.SelectedSEDCoord(
            id=old_selected_coord.id,
            sed_coordinate = new_sed.SEDCoord.objects.get(id=old_selected_coord.sed_coordinate.id),
            visible = old_selected_coord.visible,
            twod_shape = old_selected_coord.twod_shape,
            threed_shape = old_selected_coord.threed_shape,
            color = old_selected_coord.color,
            selected = old_selected_coord.selected,
            user = User.objects.get(id=old_selected_coord.user.id)
        )
        if old_selected_coord.saved_selection is not None:
            new_selected_coord.saved_selection=new_sed.SavedSEDCoordSelection.objects.get(id=old_selected_coord.saved_selection.id)
        new_selected_coord.save()

if __name__=='__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")
    migration('/home/jbonaiuto/Projects/bodb/uscbp/media/photologue/photos',
        '/home/jbonaiuto/Projects/bodb/new_version/bodb/media')