from django.conf.urls import patterns, url
from bodb.feeds import LatestModels, LatestBOPs, LatestSEDs, LatestSSRs
from bodb.views.admin import AdminDetailView, CreateUserView, UserDetailView, CreateGroupView, GroupDetailView, UpdateUserView, UpdateGroupView, UserToggleActiveView, UserToggleStaffView, UserToggleAdminView, DeleteGroupView, GetUserIconUrlView
from bodb.views.bop import CreateBOPView, SimilarBOPView, BOPAPIListView, BOPAPIDetailView, BOPDetailView, UpdateBOPView, DeleteBOPView, BOPTaggedView, ToggleSelectBOPView
from bodb.views.brain_region import BrainRegionRequestListView, CreateBrainRegionRequestView, CheckBrainRegionRequestExistsView, BrainRegionAPIListView, BrainRegionAPIDetailView, BrainRegionView, BrainRegionRequestDenyView, BrainRegionRequestApproveView, ToggleSelectBrainRegionView
from bodb.views.discussion import ForumPostView
from bodb.views.document import ManageDocumentPermissionsView, DocumentPublicRequestView, DocumentAPIListView, DocumentAPIDetailView, DocumentDetailView
from bodb.views.literature import CreateLiteratureView, LiteratureDetailView, UpdateLiteratureView, DeleteLiteratureView, ExportLiteratureView, ToggleSelectLiteratureView, LiteraturePubmedView
from bodb.views.main import IndexView, AboutView, InsertView, DraftListView, FavoriteListView, ToggleFavoriteView, TagView, BrainSurferView, ToggleFavoriteBrainRegionView, ToggleFavoriteLiteratureView, RecentEntriesListView
from bodb.views.messaging import UserMessageListView, CreateUserMessageView, ReadReplyUserMessageView, DeleteUserMessageView
from bodb.views.model import CreateModelView, SimilarModelView, ModelAPIListView, ModelAPIDetailView, ModelDetailView, ModuleDetailView, UpdateModelView, DeleteModelView, UpdateModuleView, DeleteModuleView, ModelTaggedView, BenchmarkModelView, ReverseBenchmarkModelView, ToggleSelectModelView, CreateModelWizardView, MODEL_WIZARD_FORMS
from bodb.views.prediction import PredictionDetailView, UpdatePredictionView, DeletePredictionView, PredictionTaggedView, PredictionAPIListView, PredictionAPIDetailView
from bodb.views.report import BOPReportView, ModelReportView, SEDReportView, SSRReportView, ModuleReportView
from bodb.views.search import SearchView, BOPSearchView, SEDSearchView, LiteratureSearchView, BrainRegionSearchView, ModelSearchView, PubmedSearchView, ModelDBSearchView
from bodb.views.sed import CreateSEDView, SEDAPIListView, ERPSEDAPIListView, BrainImagingSEDAPIListView, ConnectivitySEDAPIListView, SEDAPIDetailView, SEDDetailView, SimilarSEDView, UpdateSEDView, DeleteSEDView, SEDTaggedView, CreateERPSEDView, UpdateERPSEDView, DeleteERPSEDView, CreateBrainImagingSEDView, CleanBrainImagingSEDView, UpdateBrainImagingSEDView, DeleteBrainImagingSEDView, ToggleSelectSEDView, SaveCoordinateSelectionView, CloseCoordinateSelectionView, CoordinateSelectionView, DeleteCoordinateSelectionView, SelectSEDCoordView, UnselectSEDCoordView, SelectSelectedSEDCoordView, UnselectSelectedSEDCoordView, DeleteConnectivitySEDView, UpdateConnectivitySEDView, CreateConnectivitySEDView, ElectrodePositionsView
from bodb.views.ssr import SSRAPIListView, SSRAPIDetailView, SSRDetailView, UpdateSSRView, DeleteSSRView, SSRTaggedView, ToggleSelectSSRView, CreateSSRView, SortSSRListView
from bodb.views.subscription import CreateSubscriptionView, CreateUserSubscriptionView
from bodb.views.workspace import ActivateWorkspaceView, WorkspaceDetailView, ActiveWorkspaceDetailView, WorkspaceUserToggleAdminView, WorkspaceInvitationResponseView, WorkspaceUserRemoveView, CreateWorkspaceView, WorkspaceTitleAvailableView, DeleteWorkspaceView, UpdateWorkspaceView, SaveWorkspaceCoordinateSelectionView, WorkspaceInvitationView, WorkspaceUserDetailView, UpdateWorkspaceUserView, WorkspaceInvitationResendView, CreateWorkspaceBookmarkView, DeleteWorkspaceBookmarkView

from django.conf.urls import include

import autocomplete_light
autocomplete_light.autodiscover()

from tastypie.api import Api
from bodb.api import *

v1_api = Api(api_name='v1')
v1_api.register(SEDResource())
v1_api.register(BOPResource())
v1_api.register(BODBModelResource())
v1_api.register(SSRResource())
v1_api.register(PredictionResource())
v1_api.register(BrainRegionResource())
v1_api.register(RelatedBrainRegionResource())
v1_api.register(TestSEDResource())
v1_api.register(BuildSEDResource())
v1_api.register(BrainImaginingSEDResource())
v1_api.register(ERPSEDResource())
v1_api.register(ConnectivitySEDResource())

feeds = {
    'latestModels': LatestModels,
    'latestBOPs': LatestBOPs,
    'latestSEDs': LatestSEDs,
    'latestSSRs': LatestSSRs,
    }

urlpatterns = patterns('',
                       
    url(r'^todo/', include('todo.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^api/', include(v1_api.urls)),
)

urlpatterns = urlpatterns + patterns('',
    (r'^feeds/latestModels/$', LatestModels()),
    url(r'^about/$', AboutView.as_view(), {}, 'about'),
    url(r'^insert/$', InsertView.as_view(), {}, 'insert'),
    url(r'^brainSurfer/$', BrainSurferView.as_view(), {}, name='brain_surfer'),

    url(r'^bop/(?P<pk>\d+)/$', BOPDetailView.as_view(), {}, 'bop_view'),
    url(r'^bop/(?P<pk>\d+)/delete/$', DeleteBOPView.as_view(), {}, 'bop_delete'),
    url(r'^bop/(?P<pk>\d+)/edit/$', UpdateBOPView.as_view(), {}, 'bop_edit'),
    url(r'^bop/(?P<pk>\d+)/report/$', BOPReportView.as_view(), {}, 'bop_report'),
    url(r'^bop/(?P<pk>\d+)/toggle_select/$', ToggleSelectBOPView.as_view(), {}, 'bop_toggle_select'),
    url(r'^bop/new/$', CreateBOPView.as_view(), {}, 'bop_add'),
    url(r'^bop/search/$', BOPSearchView.as_view(), {}, 'bop_search'),
    url(r'^bop/similar/$', SimilarBOPView.as_view(), {}, 'bop_similar'),
    url(r'^bop/tag/(?P<name>[^/]+)/$', BOPTaggedView.as_view(), {}, 'bop_tagged'),

    url(r'^brain_region/(?P<pk>\d+)/$', BrainRegionView.as_view(), {}, 'brain_region_view'),
    url(r'^brain_region/(?P<pk>\d+)/toggle_select/$', ToggleSelectBrainRegionView.as_view(), {},
        'brain_region_toggle_select'),
    url(r'^brain_region/requests/$', BrainRegionRequestListView.as_view(), {}, 'brain_region_requests'),
    url(r'^brain_region/request/$', CreateBrainRegionRequestView.as_view(), {}, 'brain_region_request'),
    url(r'^brain_region/request/deny/(?P<activation_key>\w+)/$', BrainRegionRequestDenyView.as_view(),
        {}, 'brain_region_request_deny'),
    url(r'^brain_region/request/approve/(?P<activation_key>\w+)/$', BrainRegionRequestApproveView.as_view(),
        {}, 'brain_region_request_approve'),
    url(r'^brain_region/request_exists/$', CheckBrainRegionRequestExistsView.as_view(), {},
        'ajax_brain_region_request_exists'),
    url(r'^brain_region/search/$', BrainRegionSearchView.as_view(), {}, 'brain_region_search'),

    url(r'^coord_selection/(?P<pk>\d+)/$', CoordinateSelectionView.as_view(), {}, 'coord_selection_view'),
    url(r'^coord_selection/(?P<pk>\d+)/delete/$', DeleteCoordinateSelectionView.as_view(), {},
        'coord_selection_delete'),
    url(r'^coord_selection/close/$', CloseCoordinateSelectionView.as_view(), {}, 'coord_selection_add'),
    url(r'^coord_selection/save/$', SaveCoordinateSelectionView.as_view(), {}, 'coord_selection_save'),

    url(r'^document/(?P<pk>\d+)/$', DocumentDetailView.as_view(), {}, 'document_view'),
    url(r'^document/(?P<pk>\d+)/permissions/$', ManageDocumentPermissionsView.as_view(), {}, 'manage_permissions'),
    url(r'^document/public_request/$', DocumentPublicRequestView.as_view(), {}, 'public_request'),

    url(r'^drafts/$', DraftListView.as_view(), {}, 'drafts_view'),

    url(r'^favorite/toggle/$', ToggleFavoriteView.as_view(), {}, 'toggle_favorite'),
    url(r'^favorite/brain_region/toggle/$', ToggleFavoriteBrainRegionView.as_view(), {},
        'toggle_favorite_brain_region'),
    url(r'^favorite/literature/toggle/$', ToggleFavoriteLiteratureView.as_view(), {}, 'toggle_favorite_literature'),
    url(r'^favorites/$', FavoriteListView.as_view(), {}, 'favorites'),

    url(r'^literature/(?P<pk>\d+)/$', LiteratureDetailView.as_view(), {}, 'lit_view'),
    url(r'^literature/(?P<pk>\d+)/delete/$', DeleteLiteratureView.as_view(), {}, 'lit_delete'),
    url(r'^literature/(?P<pk>\d+)/edit/$', UpdateLiteratureView.as_view(), {}, 'lit_edit'),
    url(r'^literature/(?P<pk>\d+)/toggle_select/$', ToggleSelectLiteratureView.as_view(), {}, 'lit_toggle_select'),
    url(r'^literature/pubmed/(?P<id>\d+)/$', LiteraturePubmedView.as_view(), {}, 'lit_pubmed_view'),
    url(r'^literature/export/$', ExportLiteratureView.as_view(), {}, 'lit_export'),
    url(r'^literature/new/$', CreateLiteratureView.as_view(), {}, 'lit_add'),
    url(r'^literature/search/$', LiteratureSearchView.as_view(), {}, 'lit_search'),

    url(r'^model/(?P<pk>\d+)/$', ModelDetailView.as_view(), {}, 'model_view'),
    url(r'^model/(?P<pk>\d+)/delete/$', DeleteModelView.as_view(), {}, 'model_delete'),
    url(r'^model/(?P<pk>\d+)/edit/$', UpdateModelView.as_view(), {}, 'model_edit'),
    url(r'^model/(?P<pk>\d+)/report/$', ModelReportView.as_view(), {}, 'model_report'),
    url(r'^model/(?P<pk>\d+)/toggle_select/$', ToggleSelectModelView.as_view(), {}, 'model_toggle_select'),
    url(r'^model/benchmark/$', BenchmarkModelView.as_view(), {}, 'model_benchmark'),
    url(r'^model/new/$', CreateModelView.as_view(), {}, 'model_add'),
    url(r'^model/new/wizard/$', CreateModelWizardView.as_view(MODEL_WIZARD_FORMS), {}, 'model_add_wizard'),
    url(r'^model/reverse_benchmark/$', ReverseBenchmarkModelView.as_view(), {}, 'model_reverse_benchmark'),
    url(r'^model/similar/$', SimilarModelView.as_view(), {}, 'model_similar'),
    url(r'^model/search/$', ModelSearchView.as_view(), {}, 'model_search'),
    url(r'^model/tag/(?P<name>[^/]+)/$', ModelTaggedView.as_view(), {}, 'model_tagged'),

    url(r'^module/(?P<pk>\d+)/$', ModuleDetailView.as_view(), {}, 'module_view'),
    url(r'^module/(?P<pk>\d+)/delete/$', DeleteModuleView.as_view(), {}, 'module_delete'),
    url(r'^module/(?P<pk>\d+)/edit/$', UpdateModuleView.as_view(), {}, 'module_edit'),
    url(r'^module/(?P<pk>\d+)/report/$', ModuleReportView.as_view(), {}, 'module_report'),

    url(r'^prediction/(?P<pk>\d+)/$', PredictionDetailView.as_view(), {}, 'prediction_view'),
    url(r'^prediction/(?P<pk>\d+)/delete/$', DeletePredictionView.as_view(), {}, 'prediction_delete'),
    url(r'^prediction/(?P<pk>\d+)/edit/$', UpdatePredictionView.as_view(), {}, 'prediction_edit'),
    url(r'^prediction/tag/(?P<name>[^/]+)/$', PredictionTaggedView.as_view(), {}, 'prediction_tagged'),

    url(r'^search/$', SearchView.as_view(), {}, 'search'),
    url(r'^search/modeldb/$', ModelDBSearchView.as_view(), {}, 'modeldb_search'),
    url(r'^search/pubmed/$', PubmedSearchView.as_view(), {}, 'pubmed_search'),

    url(r'^sed/(?P<pk>\d+)/$', SEDDetailView.as_view(), {}, 'sed_view'),
    url(r'^sed/(?P<pk>\d+)/delete/$', DeleteSEDView.as_view(), {}, 'sed_delete'),
    url(r'^sed/(?P<pk>\d+)/edit/$', UpdateSEDView.as_view(), {}, 'sed_edit'),
    url(r'^sed/(?P<pk>\d+)/report/$', SEDReportView.as_view(), {}, 'sed_report'),
    url(r'^sed/(?P<pk>\d+)/toggle_select/$', ToggleSelectSEDView.as_view(), {}, 'sed_toggle_select'),
    url(r'^sed/similar/$', SimilarSEDView.as_view(), {}, 'sed_similar'),
    url(r'^sed/search/$', SEDSearchView.as_view(), {}, 'sed_search'),
    url(r'^sed/tag/(?P<name>[^/]+)/$', SEDTaggedView.as_view(), {}, 'sed_tagged'),

    url(r'^sed/connectivity/(?P<pk>\d+)/delete/$', DeleteConnectivitySEDView.as_view(), {}, 'connectivity_sed_delete'),
    url(r'^sed/connectivity/(?P<pk>\d+)/edit/$', UpdateConnectivitySEDView.as_view(), {}, 'connectivity_sed_edit'),
    url(r'^sed/connectivity/new/$', CreateConnectivitySEDView.as_view(), {}, 'connectivity_sed_add'),

    url(r'^sed/selectedcoord/(?P<pk>\d+)/select/$', SelectSelectedSEDCoordView.as_view(), {},
        'sed_select_selected_coord'),
    url(r'^sed/selectedcoord/(?P<pk>\d+)/unselect/$', UnselectSelectedSEDCoordView.as_view(), {},
        'sed_unselect_selected_coord'),
    url(r'^sed/coord/(?P<pk>\d+)/select/$', SelectSEDCoordView.as_view(), {}, 'sed_select_coord'),
    url(r'^sed/coord/(?P<pk>\d+)/unselect/$', UnselectSEDCoordView.as_view(), {}, 'sed_unselect_coord'),

    url(r'^sed/generic/new/$', CreateSEDView.as_view(), {}, 'generic_sed_add'),

    url(r'^sed/electrode_positions/(?P<pk>\d+)/$', ElectrodePositionsView.as_view(), {}, 'sed_electrode_positions'),

    url(r'^sed/erp/(?P<pk>\d+)/delete/$', DeleteERPSEDView.as_view(), {}, 'erp_sed_delete'),
    url(r'^sed/erp/(?P<pk>\d+)/edit/$', UpdateERPSEDView.as_view(), {}, 'erp_sed_edit'),
    url(r'^sed/erp/new/$', CreateERPSEDView.as_view(), {}, 'erp_sed_add'),

    url(r'^sed/imaging/(?P<pk>\d+)/clean/$', CleanBrainImagingSEDView.as_view(), name='imaging_sed_clean'),
    url(r'^sed/imaging/(?P<pk>\d+)/delete/$', DeleteBrainImagingSEDView.as_view(), name='imaging_sed_delete'),
    url(r'^sed/imaging/(?P<pk>\d+)/edit/$', UpdateBrainImagingSEDView.as_view(), name='imaging_sed_edit'),
    url(r'^sed/imaging/new/$', CreateBrainImagingSEDView.as_view(), {}, 'imaging_sed_add'),

    url(r'^ssr/(?P<pk>\d+)/$', SSRDetailView.as_view(), {}, 'ssr_view'),
    url(r'^ssr/(?P<pk>\d+)/delete/$', DeleteSSRView.as_view(), {}, 'ssr_delete'),
    url(r'^ssr/(?P<pk>\d+)/edit/$', UpdateSSRView.as_view(), {}, 'ssr_edit'),
    url(r'^ssr/new/$', CreateSSRView.as_view(), {}, 'ssr_add'),
    url(r'^ssr/(?P<pk>\d+)/report/$', SSRReportView.as_view(), {}, 'ssr_report'),
    url(r'^ssr/(?P<pk>\d+)/toggle_select/$', ToggleSelectSSRView.as_view(), {}, 'ssr_toggle_select'),
    url(r'^ssr/sort/$', SortSSRListView.as_view(), {}, 'sort_ssrs'),
    url(r'^ssr/tag/(?P<name>[^/]+)/$', SSRTaggedView.as_view(), {}, 'ssr_tagged'),

    url(r'^admin/$', AdminDetailView.as_view(), {}, 'admin'),
    url(r'^user/new/$', CreateUserView.as_view(), {}, 'user_add'),
    url(r'^user/(?P<pk>\d+)/$', UserDetailView.as_view(), {}, 'user_view'),
    url(r'^user/(?P<pk>\d+)/edit/$', UpdateUserView.as_view(), {}, 'user_edit'),
    url(r'^user/(?P<pk>\d+)/icon/$', GetUserIconUrlView.as_view(), {}, 'user_icon_url'),
    url(r'^user/(?P<pk>\d+)/toggle_active/$', UserToggleActiveView.as_view(), {}, 'user_active'),
    url(r'^user/(?P<pk>\d+)/toggle_staff/$', UserToggleStaffView.as_view(), {}, 'user_staff'),
    url(r'^user/(?P<pk>\d+)/toggle_admin/$', UserToggleAdminView.as_view(), {}, 'user_admin'),
    url(r'^group/new/$', CreateGroupView.as_view(), {}, 'group_add'),
    url(r'^group/(?P<pk>\d+)/edit/$', UpdateGroupView.as_view(), {}, 'group_edit'),
    url(r'^group/(?P<pk>\d+)/delete/$', DeleteGroupView.as_view(), {}, 'group_delete'),
    url(r'^group/(?P<pk>\d+)/$', GroupDetailView.as_view(), {}, 'group_view'),

    url(r'^messages/$', UserMessageListView.as_view(), {}, 'messages'),
    url(r'^message/new/$', CreateUserMessageView.as_view(), {}, 'message_add'),
    url(r'^message/(?P<pk>\d+)/delete/$', DeleteUserMessageView.as_view(), {}, 'message_delete'),
    url(r'^message/(?P<pk>\d+)/$', ReadReplyUserMessageView.as_view(), {}, 'message_view'),

    url(r'^recent/$', RecentEntriesListView.as_view(), {}, 'recently_viewed'),

    url(r'^subscription/new/', CreateSubscriptionView.as_view(), {}, 'subscription_new'),
    url(r'^subscription/user/new/', CreateUserSubscriptionView.as_view(), {}, 'user_subscription_new'),

    url(r'^tag/(?P<name>[^/]+)/$', TagView.as_view(), {}, 'tagged'),

    url(r'^forum/(?P<pk>\d+)/new_post/$', ForumPostView.as_view(), {}, 'forum_post_view'),

    url(r'^workspace/active/$', ActiveWorkspaceDetailView.as_view(), {}, 'active_workspace_view'),
    url(r'^workspace/(?P<pk>\d+)/$', WorkspaceDetailView.as_view(), {}, 'workspace_view'),
    url(r'^workspace/(?P<pk>\d+)/activate/$', ActivateWorkspaceView.as_view(), {}, 'workspace_activate'),
    url(r'^workspace/(?P<pk>\d+)/bookmark/new/$', CreateWorkspaceBookmarkView.as_view(), {}, 'workspace_bookmark_add'),
    url(r'^workspace/(?P<pk>\d+)/bookmark/(?P<pk2>\d+)/delete/$', DeleteWorkspaceBookmarkView.as_view(), {},
        'workspace_bookmark_delete'),
    url(r'^workspace/(?P<pk>\d+)/delete/$', DeleteWorkspaceView.as_view(), {}, 'workspace_activate'),
    url(r'^workspace/(?P<pk>\d+)/edit/$', UpdateWorkspaceView.as_view(), {}, 'workspace_edit'),
    url(r'^workspace/(?P<pk>\d+)/invitation/$', WorkspaceInvitationView.as_view(), {}, 'workspace_invitation'),
    url(r'^workspace/(?P<pk>\d+)/user/(?P<id>\d+)/$', WorkspaceUserDetailView.as_view(), {}, 'workspace_user_view'),
    url(r'^workspace/(?P<id>\d+)/user/(?P<pk>\d+)/edit/$', UpdateWorkspaceUserView.as_view(), {},
        'workspace_user_edit'),
    url(r'^workspace/(?P<pk>\d+)/user/remove/$', WorkspaceUserRemoveView.as_view(), {}, 'workspace_user_remove'),
    url(r'^workspace/(?P<pk>\d+)/user/toggle_admin/$', WorkspaceUserToggleAdminView.as_view(), {},
        'workspace_user_admin'),
    url(r'^workspace/(?P<pk>\d+)/coord_selection/save/$', SaveWorkspaceCoordinateSelectionView.as_view(), {},
        'workspace_coord_selection_save'),
    url(r'^workspace/new/$', CreateWorkspaceView.as_view(), {}, 'workspace_add'),
    url(r'^workspace_invite/(?P<pk>\d+)/resend/$', WorkspaceInvitationResendView.as_view(), {},
        'workspace_invitation_resend'),
    url(r'^workspace_invite/(?P<action>\w+)/(?P<activation_key>\w+)/$', WorkspaceInvitationResponseView.as_view(), {},
        'workspace_invitation_response'),
    url(r'^workspace/title_available/$', WorkspaceTitleAvailableView.as_view(), {}, 'workspace_title_available'),

    url(r'', IndexView.as_view(), {}, 'index'),
)

#urlpatterns = format_suffix_patterns(urlpatterns)
