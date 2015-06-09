# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Forum'
        db.create_table(u'bodb_forum', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('bodb', ['Forum'])

        # Adding model 'Post'
        db.create_table(u'bodb_post', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Forum'], null=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['bodb.Post'])),
            ('posted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('bodb', ['Post'])

        # Adding model 'Message'
        db.create_table(u'bodb_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_recipient_set', to=orm['auth.User'])),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(related_name='message_sender_set', null=True, to=orm['auth.User'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Message'])

        # Adding model 'Subscription'
        db.create_table(u'bodb_subscription', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='subscription', null=True, to=orm['auth.User'])),
            ('model_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Subscription'])

        # Adding model 'UserSubscription'
        db.create_table(u'bodb_usersubscription', (
            (u'subscription_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Subscription'], unique=True, primary_key=True)),
            ('subscribed_to_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='user_subscription', to=orm['auth.User'])),
        ))
        db.send_create_signal('bodb', ['UserSubscription'])

        # Adding model 'Workspace'
        db.create_table(u'bodb_workspace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Forum'])),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Workspace'])

        # Adding M2M table for field admin_users on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_admin_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'user_id'])

        # Adding M2M table for field related_models on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_models')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('model', models.ForeignKey(orm['bodb.model'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'model_id'])

        # Adding M2M table for field related_bops on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_bops')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('bop', models.ForeignKey(orm['bodb.bop'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'bop_id'])

        # Adding M2M table for field related_seds on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_seds')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('sed', models.ForeignKey(orm['bodb.sed'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'sed_id'])

        # Adding M2M table for field related_ssrs on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_ssrs')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('ssr', models.ForeignKey(orm['bodb.ssr'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'ssr_id'])

        # Adding M2M table for field related_literature on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_literature')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'literature_id'])

        # Adding M2M table for field related_regions on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_related_regions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('brainregion', models.ForeignKey(orm['bodb.brainregion'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'brainregion_id'])

        # Adding M2M table for field saved_coordinate_selections on 'Workspace'
        m2m_table_name = db.shorten_name(u'bodb_workspace_saved_coordinate_selections')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('workspace', models.ForeignKey(orm['bodb.workspace'], null=False)),
            ('savedsedcoordselection', models.ForeignKey(orm['bodb.savedsedcoordselection'], null=False))
        ))
        db.create_unique(m2m_table_name, ['workspace_id', 'savedsedcoordselection_id'])

        # Adding model 'WorkspaceInvitation'
        db.create_table(u'bodb_workspaceinvitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Workspace'])),
            ('invited_user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invited_user', to=orm['auth.User'])),
            ('invited_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='invited_by', to=orm['auth.User'])),
            ('invitation_body', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('activation_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('sent', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['WorkspaceInvitation'])

        # Adding model 'WorkspaceBookmark'
        db.create_table(u'bodb_workspacebookmark', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Workspace'])),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('collator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='bookmark_last_modified_by', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('bodb', ['WorkspaceBookmark'])

        # Adding model 'WorkspaceActivityItem'
        db.create_table(u'bodb_workspaceactivityitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Workspace'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('bodb', ['WorkspaceActivityItem'])

        # Adding model 'AllocatedUserAccount'
        db.create_table(u'bodb_allocateduseraccount', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
        ))
        db.send_create_signal('bodb', ['AllocatedUserAccount'])

        # Adding model 'BodbProfile'
        db.create_table(u'bodb_bodbprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('avatar', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('new_message_notify', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('active_workspace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Workspace'], null=True)),
            ('loaded_coordinate_selection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.SavedSEDCoordSelection'], null=True)),
            ('affiliation', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('notification_preference', self.gf('django.db.models.fields.CharField')(default='both', max_length=100)),
        ))
        db.send_create_signal('bodb', ['BodbProfile'])

        # Adding M2M table for field favorites on 'BodbProfile'
        m2m_table_name = db.shorten_name(u'bodb_bodbprofile_favorites')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bodbprofile', models.ForeignKey(orm['bodb.bodbprofile'], null=False)),
            ('document', models.ForeignKey(orm['bodb.document'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bodbprofile_id', 'document_id'])

        # Adding M2M table for field favorite_literature on 'BodbProfile'
        m2m_table_name = db.shorten_name(u'bodb_bodbprofile_favorite_literature')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bodbprofile', models.ForeignKey(orm['bodb.bodbprofile'], null=False)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bodbprofile_id', 'literature_id'])

        # Adding M2M table for field favorite_regions on 'BodbProfile'
        m2m_table_name = db.shorten_name(u'bodb_bodbprofile_favorite_regions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bodbprofile', models.ForeignKey(orm['bodb.bodbprofile'], null=False)),
            ('brainregion', models.ForeignKey(orm['bodb.brainregion'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bodbprofile_id', 'brainregion_id'])

        # Adding model 'Author'
        db.create_table(u'bodb_author', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('homepage', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Author'])

        # Adding model 'LiteratureAuthor'
        db.create_table(u'bodb_literatureauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Author'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('bodb', ['LiteratureAuthor'])

        # Adding model 'Literature'
        db.create_table(u'bodb_literature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pubmed_id', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='English', max_length=100)),
            ('annotation', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('collator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
        ))
        db.send_create_signal('bodb', ['Literature'])

        # Adding M2M table for field authors on 'Literature'
        m2m_table_name = db.shorten_name(u'bodb_literature_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False)),
            ('literatureauthor', models.ForeignKey(orm['bodb.literatureauthor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['literature_id', 'literatureauthor_id'])

        # Adding model 'Journal'
        db.create_table(u'bodb_journal', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
            ('journal_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('volume', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('issue', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('pages', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
        ))
        db.send_create_signal('bodb', ['Journal'])

        # Adding model 'Book'
        db.create_table(u'bodb_book', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('volume', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('series', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('editors', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('bodb', ['Book'])

        # Adding model 'Chapter'
        db.create_table(u'bodb_chapter', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('volume', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('series', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('editors', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('book_title', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('bodb', ['Chapter'])

        # Adding model 'Conference'
        db.create_table(u'bodb_conference', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('volume', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('series', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('organization', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bodb', ['Conference'])

        # Adding model 'Thesis'
        db.create_table(u'bodb_thesis', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
            ('school', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bodb', ['Thesis'])

        # Adding model 'Unpublished'
        db.create_table(u'bodb_unpublished', (
            (u'literature_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Literature'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('bodb', ['Unpublished'])

        # Adding model 'Atlas'
        db.create_table(u'bodb_atlas', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bodb', ['Atlas'])

        # Adding model 'Species'
        db.create_table(u'bodb_species', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('genus_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('species_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('common_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Species'])

        # Adding model 'Nomenclature'
        db.create_table(u'bodb_nomenclature', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Literature'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Nomenclature'])

        # Adding M2M table for field species on 'Nomenclature'
        m2m_table_name = db.shorten_name(u'bodb_nomenclature_species')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('nomenclature', models.ForeignKey(orm['bodb.nomenclature'], null=False)),
            ('species', models.ForeignKey(orm['bodb.species'], null=False))
        ))
        db.create_unique(m2m_table_name, ['nomenclature_id', 'species_id'])

        # Adding model 'CoordinateSpace'
        db.create_table(u'bodb_coordinatespace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bodb', ['CoordinateSpace'])

        # Adding model 'ElectrodePositionSystem'
        db.create_table(u'bodb_electrodepositionsystem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('bodb', ['ElectrodePositionSystem'])

        # Adding model 'ElectrodePosition'
        db.create_table(u'bodb_electrodeposition', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('position_system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.ElectrodePositionSystem'])),
        ))
        db.send_create_signal('bodb', ['ElectrodePosition'])

        # Adding model 'ThreeDCoord'
        db.create_table(u'bodb_threedcoord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('x', self.gf('django.db.models.fields.FloatField')()),
            ('y', self.gf('django.db.models.fields.FloatField')()),
            ('z', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('bodb', ['ThreeDCoord'])

        # Adding model 'BrainRegion'
        db.create_table(u'bodb_brainregion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nomenclature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Nomenclature'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('brain_region_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('parent_region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.BrainRegion'], null=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['BrainRegion'])

        # Adding model 'BrainRegionVolume'
        db.create_table(u'bodb_brainregionvolume', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.BrainRegion'])),
            ('coord_space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.CoordinateSpace'])),
        ))
        db.send_create_signal('bodb', ['BrainRegionVolume'])

        # Adding M2M table for field coords on 'BrainRegionVolume'
        m2m_table_name = db.shorten_name(u'bodb_brainregionvolume_coords')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregionvolume', models.ForeignKey(orm['bodb.brainregionvolume'], null=False)),
            ('threedcoord', models.ForeignKey(orm['bodb.threedcoord'], null=False))
        ))
        db.create_unique(m2m_table_name, ['brainregionvolume_id', 'threedcoord_id'])

        # Adding model 'CoCoMacBrainRegion'
        db.create_table(u'bodb_cocomacbrainregion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cocomac_region', to=orm['bodb.BrainRegion'])),
            ('cocomac_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('bodb', ['CoCoMacBrainRegion'])

        # Adding model 'BrainNavigatorBrainRegion'
        db.create_table(u'bodb_brainnavigatorbrainregion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brainnav_region', to=orm['bodb.BrainRegion'])),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=6)),
        ))
        db.send_create_signal('bodb', ['BrainNavigatorBrainRegion'])

        # Adding model 'RelatedBrainRegion'
        db.create_table(u'bodb_relatedbrainregion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_region_document', to=orm['bodb.Document'])),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region', null=True, to=orm['bodb.BrainRegion'])),
            ('relationship', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['RelatedBrainRegion'])

        # Adding model 'LocalServerMapping'
        db.create_table(u'bodb_localservermapping', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('local_region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.BrainRegion'])),
            ('server_region_id', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('bodb', ['LocalServerMapping'])

        # Adding model 'BrainRegionRequest'
        db.create_table(u'bodb_brainregionrequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('abbreviation', self.gf('django.db.models.fields.TextField')()),
            ('parent', self.gf('django.db.models.fields.TextField')()),
            ('children', self.gf('django.db.models.fields.TextField')()),
            ('nomenclature', self.gf('django.db.models.fields.TextField')()),
            ('nomenclature_version', self.gf('django.db.models.fields.TextField')()),
            ('rationale', self.gf('django.db.models.fields.TextField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('activation_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
        ))
        db.send_create_signal('bodb', ['BrainRegionRequest'])

        # Adding model 'Document'
        db.create_table(u'bodb_document', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('collator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('brief_description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('narrative', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('draft', self.gf('django.db.models.fields.IntegerField')(default=False)),
            ('public', self.gf('django.db.models.fields.IntegerField')(default=False)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_modified_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='last_modified_by', null=True, to=orm['auth.User'])),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Forum'], null=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Document'])

        # Adding model 'DocumentFigure'
        db.create_table(u'bodb_documentfigure', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='figures', to=orm['bodb.Document'])),
            ('figure', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('caption', self.gf('django.db.models.fields.TextField')()),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('bodb', ['DocumentFigure'])

        # Adding model 'DocumentPublicRequest'
        db.create_table(u'bodb_documentpublicrequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Document'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('bodb', ['DocumentPublicRequest'])

        # Adding model 'SED'
        db.create_table(u'bodb_sed', (
            (u'document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Document'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('bodb', ['SED'])

        # Adding M2M table for field literature on 'SED'
        m2m_table_name = db.shorten_name(u'bodb_sed_literature')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('sed', models.ForeignKey(orm['bodb.sed'], null=False)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['sed_id', 'literature_id'])

        # Adding model 'ERPSED'
        db.create_table(u'bodb_erpsed', (
            (u'sed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.SED'], unique=True, primary_key=True)),
            ('cognitive_paradigm', self.gf('django.db.models.fields.TextField')()),
            ('sensory_modality', self.gf('django.db.models.fields.TextField')()),
            ('response_modality', self.gf('django.db.models.fields.TextField')()),
            ('control_condition', self.gf('django.db.models.fields.TextField')()),
            ('experimental_condition', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('bodb', ['ERPSED'])

        # Adding model 'ElectrodeCap'
        db.create_table(u'bodb_electrodecap', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('manufacturer', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('num_channels', self.gf('django.db.models.fields.IntegerField')()),
            ('image_filename', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('bodb', ['ElectrodeCap'])

        # Adding model 'ERPComponent'
        db.create_table(u'bodb_erpcomponent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('erp_sed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='components', to=orm['bodb.ERPSED'])),
            ('component_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('latency_peak', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3)),
            ('latency_peak_type', self.gf('django.db.models.fields.CharField')(default='exact', max_length=100)),
            ('latency_onset', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3, blank=True)),
            ('amplitude_peak', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3, blank=True)),
            ('amplitude_mean', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3, blank=True)),
            ('electrode_cap', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.ElectrodeCap'], null=True, blank=True)),
            ('channel_number', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('electrode_position', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.ElectrodePosition'], null=True, blank=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('interpretation', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('bodb', ['ERPComponent'])

        # Adding model 'BrainImagingSED'
        db.create_table(u'bodb_brainimagingsed', (
            (u'sed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.SED'], unique=True, primary_key=True)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('control_condition', self.gf('django.db.models.fields.TextField')()),
            ('experimental_condition', self.gf('django.db.models.fields.TextField')()),
            ('coord_space', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.CoordinateSpace'], null=True)),
            ('core_header_1', self.gf('django.db.models.fields.CharField')(default='hemisphere', max_length=20)),
            ('core_header_2', self.gf('django.db.models.fields.CharField')(default='x y z', max_length=20)),
            ('core_header_3', self.gf('django.db.models.fields.CharField')(default='rCBF', max_length=20)),
            ('core_header_4', self.gf('django.db.models.fields.CharField')(default='T', max_length=20)),
            ('extra_header', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['BrainImagingSED'])

        # Adding model 'SEDCoord'
        db.create_table(u'bodb_sedcoord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='coordinates', to=orm['bodb.BrainImagingSED'])),
            ('coord', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.ThreeDCoord'])),
            ('rcbf', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3)),
            ('statistic_value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=3)),
            ('statistic', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('hemisphere', self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True)),
            ('named_brain_region', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('extra_data', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['SEDCoord'])

        # Adding model 'BredeBrainImagingSED'
        db.create_table(u'bodb_bredebrainimagingsed', (
            (u'brainimagingsed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.BrainImagingSED'], unique=True, primary_key=True)),
            ('woexp', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('bodb', ['BredeBrainImagingSED'])

        # Adding model 'SavedSEDCoordSelection'
        db.create_table(u'bodb_savedsedcoordselection', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_modified_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='coord_selection_last_modified_by', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('bodb', ['SavedSEDCoordSelection'])

        # Adding model 'SelectedSEDCoord'
        db.create_table(u'bodb_selectedsedcoord', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('saved_selection', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.SavedSEDCoordSelection'], null=True, blank=True)),
            ('sed_coordinate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.SEDCoord'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('twod_shape', self.gf('django.db.models.fields.CharField')(default='x', max_length=50)),
            ('threed_shape', self.gf('django.db.models.fields.CharField')(default='cube', max_length=50)),
            ('color', self.gf('django.db.models.fields.CharField')(default='ff0000', max_length=50)),
            ('selected', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal('bodb', ['SelectedSEDCoord'])

        # Adding model 'ConnectivitySED'
        db.create_table(u'bodb_connectivitysed', (
            (u'sed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.SED'], unique=True, primary_key=True)),
            ('source_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_region', to=orm['bodb.BrainRegion'])),
            ('target_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='target_region', to=orm['bodb.BrainRegion'])),
        ))
        db.send_create_signal('bodb', ['ConnectivitySED'])

        # Adding model 'CoCoMacConnectivitySED'
        db.create_table(u'bodb_cocomacconnectivitysed', (
            (u'connectivitysed_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.ConnectivitySED'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('bodb', ['CoCoMacConnectivitySED'])

        # Adding model 'BuildSED'
        db.create_table(u'bodb_buildsed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_build_sed_document', to=orm['bodb.Document'])),
            ('sed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='build_sed', to=orm['bodb.SED'])),
            ('relationship', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('relevance_narrative', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['BuildSED'])

        # Adding model 'TestSED'
        db.create_table(u'bodb_testsed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_test_sed_document', to=orm['bodb.Model'])),
            ('sed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='test_sed', null=True, to=orm['bodb.SED'])),
            ('ssr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.SSR'], null=True)),
            ('relationship', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('relevance_narrative', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['TestSED'])

        # Adding model 'BOP'
        db.create_table(u'bodb_bop', (
            (u'document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Document'], unique=True, primary_key=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['bodb.BOP'])),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('bodb', ['BOP'])

        # Adding M2M table for field literature on 'BOP'
        m2m_table_name = db.shorten_name(u'bodb_bop_literature')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bop', models.ForeignKey(orm['bodb.bop'], null=False)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bop_id', 'literature_id'])

        # Adding model 'RelatedBOP'
        db.create_table(u'bodb_relatedbop', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_bop_document', to=orm['bodb.Document'])),
            ('bop', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_bop', null=True, to=orm['bodb.BOP'])),
            ('relationship', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('relevance_narrative', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['RelatedBOP'])

        # Adding model 'Module'
        db.create_table(u'bodb_module', (
            (u'document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Document'], unique=True, primary_key=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['bodb.Module'])),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('bodb', ['Module'])

        # Adding model 'ModelAuthor'
        db.create_table(u'bodb_modelauthor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.Author'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('bodb', ['ModelAuthor'])

        # Adding model 'Model'
        db.create_table(u'bodb_model', (
            (u'module_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Module'], unique=True, primary_key=True)),
            ('execution_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('documentation_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('description_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('simulation_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('modeldb_accession_number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('bodb', ['Model'])

        # Adding M2M table for field authors on 'Model'
        m2m_table_name = db.shorten_name(u'bodb_model_authors')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('model', models.ForeignKey(orm['bodb.model'], null=False)),
            ('modelauthor', models.ForeignKey(orm['bodb.modelauthor'], null=False))
        ))
        db.create_unique(m2m_table_name, ['model_id', 'modelauthor_id'])

        # Adding M2M table for field literature on 'Model'
        m2m_table_name = db.shorten_name(u'bodb_model_literature')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('model', models.ForeignKey(orm['bodb.model'], null=False)),
            ('literature', models.ForeignKey(orm['bodb.literature'], null=False))
        ))
        db.create_unique(m2m_table_name, ['model_id', 'literature_id'])

        # Adding model 'Variable'
        db.create_table(u'bodb_variable', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('module', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_module', null=True, to=orm['bodb.Module'])),
            ('var_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('data_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['Variable'])

        # Adding model 'RelatedModel'
        db.create_table(u'bodb_relatedmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_model_document', to=orm['bodb.Document'])),
            ('model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_model', null=True, to=orm['bodb.Model'])),
            ('relationship', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('bodb', ['RelatedModel'])

        # Adding model 'SSR'
        db.create_table(u'bodb_ssr', (
            (u'document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Document'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('bodb', ['SSR'])

        # Adding model 'Prediction'
        db.create_table(u'bodb_prediction', (
            (u'document_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['bodb.Document'], unique=True, primary_key=True)),
            ('model', self.gf('django.db.models.fields.related.ForeignKey')(related_name='prediction', to=orm['bodb.Model'])),
            ('ssr', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bodb.SSR'], null=True)),
        ))
        db.send_create_signal('bodb', ['Prediction'])


    def backwards(self, orm):
        # Deleting model 'Forum'
        db.delete_table(u'bodb_forum')

        # Deleting model 'Post'
        db.delete_table(u'bodb_post')

        # Deleting model 'Message'
        db.delete_table(u'bodb_message')

        # Deleting model 'Subscription'
        db.delete_table(u'bodb_subscription')

        # Deleting model 'UserSubscription'
        db.delete_table(u'bodb_usersubscription')

        # Deleting model 'Workspace'
        db.delete_table(u'bodb_workspace')

        # Removing M2M table for field admin_users on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_admin_users'))

        # Removing M2M table for field related_models on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_models'))

        # Removing M2M table for field related_bops on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_bops'))

        # Removing M2M table for field related_seds on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_seds'))

        # Removing M2M table for field related_ssrs on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_ssrs'))

        # Removing M2M table for field related_literature on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_literature'))

        # Removing M2M table for field related_regions on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_related_regions'))

        # Removing M2M table for field saved_coordinate_selections on 'Workspace'
        db.delete_table(db.shorten_name(u'bodb_workspace_saved_coordinate_selections'))

        # Deleting model 'WorkspaceInvitation'
        db.delete_table(u'bodb_workspaceinvitation')

        # Deleting model 'WorkspaceBookmark'
        db.delete_table(u'bodb_workspacebookmark')

        # Deleting model 'WorkspaceActivityItem'
        db.delete_table(u'bodb_workspaceactivityitem')

        # Deleting model 'AllocatedUserAccount'
        db.delete_table(u'bodb_allocateduseraccount')

        # Deleting model 'BodbProfile'
        db.delete_table(u'bodb_bodbprofile')

        # Removing M2M table for field favorites on 'BodbProfile'
        db.delete_table(db.shorten_name(u'bodb_bodbprofile_favorites'))

        # Removing M2M table for field favorite_literature on 'BodbProfile'
        db.delete_table(db.shorten_name(u'bodb_bodbprofile_favorite_literature'))

        # Removing M2M table for field favorite_regions on 'BodbProfile'
        db.delete_table(db.shorten_name(u'bodb_bodbprofile_favorite_regions'))

        # Deleting model 'Author'
        db.delete_table(u'bodb_author')

        # Deleting model 'LiteratureAuthor'
        db.delete_table(u'bodb_literatureauthor')

        # Deleting model 'Literature'
        db.delete_table(u'bodb_literature')

        # Removing M2M table for field authors on 'Literature'
        db.delete_table(db.shorten_name(u'bodb_literature_authors'))

        # Deleting model 'Journal'
        db.delete_table(u'bodb_journal')

        # Deleting model 'Book'
        db.delete_table(u'bodb_book')

        # Deleting model 'Chapter'
        db.delete_table(u'bodb_chapter')

        # Deleting model 'Conference'
        db.delete_table(u'bodb_conference')

        # Deleting model 'Thesis'
        db.delete_table(u'bodb_thesis')

        # Deleting model 'Unpublished'
        db.delete_table(u'bodb_unpublished')

        # Deleting model 'Atlas'
        db.delete_table(u'bodb_atlas')

        # Deleting model 'Species'
        db.delete_table(u'bodb_species')

        # Deleting model 'Nomenclature'
        db.delete_table(u'bodb_nomenclature')

        # Removing M2M table for field species on 'Nomenclature'
        db.delete_table(db.shorten_name(u'bodb_nomenclature_species'))

        # Deleting model 'CoordinateSpace'
        db.delete_table(u'bodb_coordinatespace')

        # Deleting model 'ElectrodePositionSystem'
        db.delete_table(u'bodb_electrodepositionsystem')

        # Deleting model 'ElectrodePosition'
        db.delete_table(u'bodb_electrodeposition')

        # Deleting model 'ThreeDCoord'
        db.delete_table(u'bodb_threedcoord')

        # Deleting model 'BrainRegion'
        db.delete_table(u'bodb_brainregion')

        # Deleting model 'BrainRegionVolume'
        db.delete_table(u'bodb_brainregionvolume')

        # Removing M2M table for field coords on 'BrainRegionVolume'
        db.delete_table(db.shorten_name(u'bodb_brainregionvolume_coords'))

        # Deleting model 'CoCoMacBrainRegion'
        db.delete_table(u'bodb_cocomacbrainregion')

        # Deleting model 'BrainNavigatorBrainRegion'
        db.delete_table(u'bodb_brainnavigatorbrainregion')

        # Deleting model 'RelatedBrainRegion'
        db.delete_table(u'bodb_relatedbrainregion')

        # Deleting model 'LocalServerMapping'
        db.delete_table(u'bodb_localservermapping')

        # Deleting model 'BrainRegionRequest'
        db.delete_table(u'bodb_brainregionrequest')

        # Deleting model 'Document'
        db.delete_table(u'bodb_document')

        # Deleting model 'DocumentFigure'
        db.delete_table(u'bodb_documentfigure')

        # Deleting model 'DocumentPublicRequest'
        db.delete_table(u'bodb_documentpublicrequest')

        # Deleting model 'SED'
        db.delete_table(u'bodb_sed')

        # Removing M2M table for field literature on 'SED'
        db.delete_table(db.shorten_name(u'bodb_sed_literature'))

        # Deleting model 'ERPSED'
        db.delete_table(u'bodb_erpsed')

        # Deleting model 'ElectrodeCap'
        db.delete_table(u'bodb_electrodecap')

        # Deleting model 'ERPComponent'
        db.delete_table(u'bodb_erpcomponent')

        # Deleting model 'BrainImagingSED'
        db.delete_table(u'bodb_brainimagingsed')

        # Deleting model 'SEDCoord'
        db.delete_table(u'bodb_sedcoord')

        # Deleting model 'BredeBrainImagingSED'
        db.delete_table(u'bodb_bredebrainimagingsed')

        # Deleting model 'SavedSEDCoordSelection'
        db.delete_table(u'bodb_savedsedcoordselection')

        # Deleting model 'SelectedSEDCoord'
        db.delete_table(u'bodb_selectedsedcoord')

        # Deleting model 'ConnectivitySED'
        db.delete_table(u'bodb_connectivitysed')

        # Deleting model 'CoCoMacConnectivitySED'
        db.delete_table(u'bodb_cocomacconnectivitysed')

        # Deleting model 'BuildSED'
        db.delete_table(u'bodb_buildsed')

        # Deleting model 'TestSED'
        db.delete_table(u'bodb_testsed')

        # Deleting model 'BOP'
        db.delete_table(u'bodb_bop')

        # Removing M2M table for field literature on 'BOP'
        db.delete_table(db.shorten_name(u'bodb_bop_literature'))

        # Deleting model 'RelatedBOP'
        db.delete_table(u'bodb_relatedbop')

        # Deleting model 'Module'
        db.delete_table(u'bodb_module')

        # Deleting model 'ModelAuthor'
        db.delete_table(u'bodb_modelauthor')

        # Deleting model 'Model'
        db.delete_table(u'bodb_model')

        # Removing M2M table for field authors on 'Model'
        db.delete_table(db.shorten_name(u'bodb_model_authors'))

        # Removing M2M table for field literature on 'Model'
        db.delete_table(db.shorten_name(u'bodb_model_literature'))

        # Deleting model 'Variable'
        db.delete_table(u'bodb_variable')

        # Deleting model 'RelatedModel'
        db.delete_table(u'bodb_relatedmodel')

        # Deleting model 'SSR'
        db.delete_table(u'bodb_ssr')

        # Deleting model 'Prediction'
        db.delete_table(u'bodb_prediction')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'avatar_type': ('django.db.models.fields.CharField', [], {'default': "'n'", 'max_length': '1'}),
            'bronze': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'consecutive_days_visit_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'country': ('django_countries.fields.CountryField', [], {'max_length': '2', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'display_tag_filter_strategy': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_isvalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_key': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'email_signature': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email_tag_filter_strategy': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'gold': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'gravatar': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored_tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'interesting_tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_fake': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'languages': ('django.db.models.fields.CharField', [], {'default': "'en-us'", 'max_length': '128'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'new_response_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'questions_per_page': ('django.db.models.fields.SmallIntegerField', [], {'default': '10'}),
            'real_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'reputation': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'seen_response_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'show_country': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_marked_tags': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'silver': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'social_sharing_mode': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'w'", 'max_length': '2'}),
            'subscribed_tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'twitter_access_token': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256'}),
            'twitter_handle': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'bodb.allocateduseraccount': {
            'Meta': {'object_name': 'AllocatedUserAccount'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'bodb.atlas': {
            'Meta': {'object_name': 'Atlas'},
            'file': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bodb.author': {
            'Meta': {'object_name': 'Author'},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'bodb.bodbprofile': {
            'Meta': {'object_name': 'BodbProfile'},
            'active_workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Workspace']", 'null': 'True'}),
            'affiliation': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'favorite_literature': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Literature']", 'symmetrical': 'False'}),
            'favorite_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.BrainRegion']", 'symmetrical': 'False'}),
            'favorites': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Document']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaded_coordinate_selection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.SavedSEDCoordSelection']", 'null': 'True'}),
            'new_message_notify': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'notification_preference': ('django.db.models.fields.CharField', [], {'default': "'both'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        'bodb.book': {
            'Meta': {'ordering': "['year']", 'object_name': 'Book', '_ormbases': ['bodb.Literature']},
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'editors': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'volume': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bodb.bop': {
            'Meta': {'object_name': 'BOP', '_ormbases': ['bodb.Document']},
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Document']", 'unique': 'True', 'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'literature': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Literature']", 'symmetrical': 'False'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['bodb.BOP']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'bodb.brainimagingsed': {
            'Meta': {'ordering': "['title']", 'object_name': 'BrainImagingSED', '_ormbases': ['bodb.SED']},
            'control_condition': ('django.db.models.fields.TextField', [], {}),
            'coord_space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.CoordinateSpace']", 'null': 'True'}),
            'core_header_1': ('django.db.models.fields.CharField', [], {'default': "'hemisphere'", 'max_length': '20'}),
            'core_header_2': ('django.db.models.fields.CharField', [], {'default': "'x y z'", 'max_length': '20'}),
            'core_header_3': ('django.db.models.fields.CharField', [], {'default': "'rCBF'", 'max_length': '20'}),
            'core_header_4': ('django.db.models.fields.CharField', [], {'default': "'T'", 'max_length': '20'}),
            'experimental_condition': ('django.db.models.fields.TextField', [], {}),
            'extra_header': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'sed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.SED']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bodb.brainnavigatorbrainregion': {
            'Meta': {'object_name': 'BrainNavigatorBrainRegion'},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brainnav_region'", 'to': "orm['bodb.BrainRegion']"}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bodb.brainregion': {
            'Meta': {'ordering': "['nomenclature', 'name']", 'object_name': 'BrainRegion'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'brain_region_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'nomenclature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Nomenclature']"}),
            'parent_region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.BrainRegion']", 'null': 'True', 'blank': 'True'})
        },
        'bodb.brainregionrequest': {
            'Meta': {'object_name': 'BrainRegionRequest'},
            'abbreviation': ('django.db.models.fields.TextField', [], {}),
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'children': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'nomenclature': ('django.db.models.fields.TextField', [], {}),
            'nomenclature_version': ('django.db.models.fields.TextField', [], {}),
            'parent': ('django.db.models.fields.TextField', [], {}),
            'rationale': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'bodb.brainregionvolume': {
            'Meta': {'object_name': 'BrainRegionVolume'},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.BrainRegion']"}),
            'coord_space': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.CoordinateSpace']"}),
            'coords': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.ThreeDCoord']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bodb.bredebrainimagingsed': {
            'Meta': {'ordering': "['title']", 'object_name': 'BredeBrainImagingSED', '_ormbases': ['bodb.BrainImagingSED']},
            u'brainimagingsed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.BrainImagingSED']", 'unique': 'True', 'primary_key': 'True'}),
            'woexp': ('django.db.models.fields.IntegerField', [], {})
        },
        'bodb.buildsed': {
            'Meta': {'ordering': "['sed__title']", 'object_name': 'BuildSED'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_build_sed_document'", 'to': "orm['bodb.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relationship': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'relevance_narrative': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'build_sed'", 'to': "orm['bodb.SED']"})
        },
        'bodb.chapter': {
            'Meta': {'ordering': "['year']", 'object_name': 'Chapter', '_ormbases': ['bodb.Literature']},
            'book_title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'editors': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'volume': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bodb.cocomacbrainregion': {
            'Meta': {'object_name': 'CoCoMacBrainRegion'},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cocomac_region'", 'to': "orm['bodb.BrainRegion']"}),
            'cocomac_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bodb.cocomacconnectivitysed': {
            'Meta': {'ordering': "['title']", 'object_name': 'CoCoMacConnectivitySED', '_ormbases': ['bodb.ConnectivitySED']},
            u'connectivitysed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.ConnectivitySED']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bodb.conference': {
            'Meta': {'ordering': "['year']", 'object_name': 'Conference', '_ormbases': ['bodb.Literature']},
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'volume': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'bodb.connectivitysed': {
            'Meta': {'ordering': "['title']", 'object_name': 'ConnectivitySED', '_ormbases': ['bodb.SED']},
            u'sed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.SED']", 'unique': 'True', 'primary_key': 'True'}),
            'source_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_region'", 'to': "orm['bodb.BrainRegion']"}),
            'target_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'target_region'", 'to': "orm['bodb.BrainRegion']"})
        },
        'bodb.coordinatespace': {
            'Meta': {'ordering': "['name']", 'object_name': 'CoordinateSpace'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.document': {
            'Meta': {'ordering': "['title']", 'object_name': 'Document'},
            'brief_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'collator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'draft': ('django.db.models.fields.IntegerField', [], {'default': 'False'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Forum']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'last_modified_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'narrative': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'public': ('django.db.models.fields.IntegerField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.documentfigure': {
            'Meta': {'ordering': "('order',)", 'object_name': 'DocumentFigure'},
            'caption': ('django.db.models.fields.TextField', [], {}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'figures'", 'to': "orm['bodb.Document']"}),
            'figure': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'bodb.documentpublicrequest': {
            'Meta': {'object_name': 'DocumentPublicRequest'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'bodb.electrodecap': {
            'Meta': {'object_name': 'ElectrodeCap'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_filename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'num_channels': ('django.db.models.fields.IntegerField', [], {}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'bodb.electrodeposition': {
            'Meta': {'object_name': 'ElectrodePosition'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'position_system': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.ElectrodePositionSystem']"})
        },
        'bodb.electrodepositionsystem': {
            'Meta': {'object_name': 'ElectrodePositionSystem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.erpcomponent': {
            'Meta': {'object_name': 'ERPComponent'},
            'amplitude_mean': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3', 'blank': 'True'}),
            'amplitude_peak': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3', 'blank': 'True'}),
            'channel_number': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'component_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'electrode_cap': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.ElectrodeCap']", 'null': 'True', 'blank': 'True'}),
            'electrode_position': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.ElectrodePosition']", 'null': 'True', 'blank': 'True'}),
            'erp_sed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'components'", 'to': "orm['bodb.ERPSED']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interpretation': ('django.db.models.fields.TextField', [], {}),
            'latency_onset': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3', 'blank': 'True'}),
            'latency_peak': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3'}),
            'latency_peak_type': ('django.db.models.fields.CharField', [], {'default': "'exact'", 'max_length': '100'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'bodb.erpsed': {
            'Meta': {'ordering': "['title']", 'object_name': 'ERPSED', '_ormbases': ['bodb.SED']},
            'cognitive_paradigm': ('django.db.models.fields.TextField', [], {}),
            'control_condition': ('django.db.models.fields.TextField', [], {}),
            'experimental_condition': ('django.db.models.fields.TextField', [], {}),
            'response_modality': ('django.db.models.fields.TextField', [], {}),
            u'sed_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.SED']", 'unique': 'True', 'primary_key': 'True'}),
            'sensory_modality': ('django.db.models.fields.TextField', [], {})
        },
        'bodb.forum': {
            'Meta': {'object_name': 'Forum'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'bodb.journal': {
            'Meta': {'ordering': "['year']", 'object_name': 'Journal', '_ormbases': ['bodb.Literature']},
            'issue': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'journal_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'}),
            'pages': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'volume': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'bodb.literature': {
            'Meta': {'ordering': "['year']", 'object_name': 'Literature'},
            'annotation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.LiteratureAuthor']", 'symmetrical': 'False'}),
            'collator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'English'", 'max_length': '100'}),
            'pubmed_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        'bodb.literatureauthor': {
            'Meta': {'ordering': "['order']", 'object_name': 'LiteratureAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {})
        },
        'bodb.localservermapping': {
            'Meta': {'object_name': 'LocalServerMapping'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.BrainRegion']"}),
            'server_region_id': ('django.db.models.fields.IntegerField', [], {})
        },
        'bodb.message': {
            'Meta': {'ordering': "['-sent']", 'object_name': 'Message'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_recipient_set'", 'to': u"orm['auth.User']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'message_sender_set'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'bodb.model': {
            'Meta': {'object_name': 'Model', '_ormbases': ['bodb.Module']},
            'authors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.ModelAuthor']", 'symmetrical': 'False'}),
            'description_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'documentation_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'execution_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'literature': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Literature']", 'symmetrical': 'False'}),
            'modeldb_accession_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'module_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Module']", 'unique': 'True', 'primary_key': 'True'}),
            'simulation_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'bodb.modelauthor': {
            'Meta': {'ordering': "['order']", 'object_name': 'ModelAuthor'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Author']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {})
        },
        'bodb.module': {
            'Meta': {'object_name': 'Module', '_ormbases': ['bodb.Document']},
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Document']", 'unique': 'True', 'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['bodb.Module']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'bodb.nomenclature': {
            'Meta': {'ordering': "['name']", 'object_name': 'Nomenclature'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Literature']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'species': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Species']", 'symmetrical': 'False'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'bodb.post': {
            'Meta': {'object_name': 'Post'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Forum']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['bodb.Post']"}),
            'posted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'bodb.prediction': {
            'Meta': {'ordering': "['title']", 'object_name': 'Prediction', '_ormbases': ['bodb.Document']},
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Document']", 'unique': 'True', 'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'prediction'", 'to': "orm['bodb.Model']"}),
            'ssr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.SSR']", 'null': 'True'})
        },
        'bodb.relatedbop': {
            'Meta': {'ordering': "['bop__title']", 'object_name': 'RelatedBOP'},
            'bop': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_bop'", 'null': 'True', 'to': "orm['bodb.BOP']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_bop_document'", 'to': "orm['bodb.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relationship': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'relevance_narrative': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bodb.relatedbrainregion': {
            'Meta': {'ordering': "['brain_region__nomenclature', 'brain_region__name']", 'object_name': 'RelatedBrainRegion'},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region'", 'null': 'True', 'to': "orm['bodb.BrainRegion']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_region_document'", 'to': "orm['bodb.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'relationship': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bodb.relatedmodel': {
            'Meta': {'ordering': "['model__title']", 'object_name': 'RelatedModel'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_model_document'", 'to': "orm['bodb.Document']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_model'", 'null': 'True', 'to': "orm['bodb.Model']"}),
            'relationship': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'bodb.savedsedcoordselection': {
            'Meta': {'object_name': 'SavedSEDCoordSelection'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coord_selection_last_modified_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'bodb.sed': {
            'Meta': {'ordering': "['title']", 'object_name': 'SED', '_ormbases': ['bodb.Document']},
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Document']", 'unique': 'True', 'primary_key': 'True'}),
            'literature': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Literature']", 'symmetrical': 'False'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'bodb.sedcoord': {
            'Meta': {'object_name': 'SEDCoord'},
            'coord': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.ThreeDCoord']"}),
            'extra_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'hemisphere': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'named_brain_region': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rcbf': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3'}),
            'sed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'coordinates'", 'to': "orm['bodb.BrainImagingSED']"}),
            'statistic': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'statistic_value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '3'})
        },
        'bodb.selectedsedcoord': {
            'Meta': {'object_name': 'SelectedSEDCoord'},
            'color': ('django.db.models.fields.CharField', [], {'default': "'ff0000'", 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'saved_selection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.SavedSEDCoordSelection']", 'null': 'True', 'blank': 'True'}),
            'sed_coordinate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.SEDCoord']"}),
            'selected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'threed_shape': ('django.db.models.fields.CharField', [], {'default': "'cube'", 'max_length': '50'}),
            'twod_shape': ('django.db.models.fields.CharField', [], {'default': "'x'", 'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'bodb.species': {
            'Meta': {'object_name': 'Species'},
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'genus_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'species_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.ssr': {
            'Meta': {'ordering': "['title']", 'object_name': 'SSR', '_ormbases': ['bodb.Document']},
            u'document_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Document']", 'unique': 'True', 'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'bodb.subscription': {
            'Meta': {'object_name': 'Subscription'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'model_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'subscription'", 'null': 'True', 'to': u"orm['auth.User']"})
        },
        'bodb.testsed': {
            'Meta': {'object_name': 'TestSED'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_test_sed_document'", 'to': "orm['bodb.Model']"}),
            'relationship': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'relevance_narrative': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'test_sed'", 'null': 'True', 'to': "orm['bodb.SED']"}),
            'ssr': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.SSR']", 'null': 'True'})
        },
        'bodb.thesis': {
            'Meta': {'ordering': "['year']", 'object_name': 'Thesis', '_ormbases': ['bodb.Literature']},
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'}),
            'school': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.threedcoord': {
            'Meta': {'object_name': 'ThreeDCoord'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {}),
            'z': ('django.db.models.fields.FloatField', [], {})
        },
        'bodb.unpublished': {
            'Meta': {'ordering': "['year']", 'object_name': 'Unpublished', '_ormbases': ['bodb.Literature']},
            u'literature_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Literature']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bodb.usersubscription': {
            'Meta': {'object_name': 'UserSubscription', '_ormbases': ['bodb.Subscription']},
            'subscribed_to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'user_subscription'", 'to': u"orm['auth.User']"}),
            u'subscription_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['bodb.Subscription']", 'unique': 'True', 'primary_key': 'True'})
        },
        'bodb.variable': {
            'Meta': {'object_name': 'Variable'},
            'data_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_module'", 'null': 'True', 'to': "orm['bodb.Module']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'var_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'bodb.workspace': {
            'Meta': {'object_name': 'Workspace'},
            'admin_users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workspace_admin'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Forum']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'related_bops': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.BOP']", 'symmetrical': 'False'}),
            'related_literature': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Literature']", 'symmetrical': 'False'}),
            'related_models': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.Model']", 'symmetrical': 'False'}),
            'related_regions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.BrainRegion']", 'symmetrical': 'False'}),
            'related_seds': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.SED']", 'symmetrical': 'False'}),
            'related_ssrs': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.SSR']", 'symmetrical': 'False'}),
            'saved_coordinate_selections': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['bodb.SavedSEDCoordSelection']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'bodb.workspaceactivityitem': {
            'Meta': {'object_name': 'WorkspaceActivityItem'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Workspace']"})
        },
        'bodb.workspacebookmark': {
            'Meta': {'object_name': 'WorkspaceBookmark'},
            'collator': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'bookmark_last_modified_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'last_modified_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Workspace']"})
        },
        'bodb.workspaceinvitation': {
            'Meta': {'object_name': 'WorkspaceInvitation'},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invitation_body': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'invited_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invited_by'", 'to': u"orm['auth.User']"}),
            'invited_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invited_user'", 'to': u"orm['auth.User']"}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['bodb.Workspace']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['bodb']