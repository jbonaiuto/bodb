import operator
from django.db.models import Q
from bodb.models import Document, SED, SEDCoord
from bodb.search.document import DocumentWithLiteratureSearch
from registration.models import User
from taggit.utils import parse_tags

def runSEDSearch(search_data, userId):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create SED search
    searcher=SEDSearch(search_data)

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

    q = reduce(op,filters) & Document.get_security_q(user) & Q(connectivitysed__cocomacconnectivitysed__isnull=True) & \
        Q(brainimagingsed__bredebrainimagingsed__isnull=True)
    results=SED.objects.filter(q).order_by('title').select_related('collator').distinct()
    return results


class SEDSearch(DocumentWithLiteratureSearch):
    # search by SED type
    def search_type(self, userId):
        if self.type:
            return Q(type=self.type)
        return Q()

    def search_source_region(self, userId):
        if self.type=='connectivity' and self.source_region:
            op=operator.or_
            if self.source_region_options=='all':
                op=operator.and_
            words=parse_tags(self.source_region)
            keyword_filters=[Q(Q(connectivitysed__source_region__name__icontains=word) |\
                               Q(connectivitysed__source_region__abbreviation__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_source_region_nomenclature(self, userId):
        if self.type=='connectivity' and self.source_region_nomenclature:
            op=operator.or_
            if self.source_region_nomenclature_options=='all':
                op=operator.and_
            words=parse_tags(self.source_region_nomenclature)
            keyword_filters=[Q(connectivitysed__source_region__nomenclature__name__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_target_region(self, userId):
        if self.type=='connectivity' and self.target_region:
            op=operator.or_
            if self.target_region_options=='all':
                op=operator.and_
            words=parse_tags(self.target_region)
            keyword_filters=[Q(Q(connectivitysed__target_region__name__icontains=word) |\
                               Q(connectivitysed__target_region__abbreviation__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_target_region_nomenclature(self, userId):
        if self.type=='connectivity' and self.target_region_nomenclature:
            op=operator.or_
            if self.target_region_nomenclature_options=='all':
                op=operator.and_
            words=parse_tags(self.target_region_nomenclature)
            keyword_filters=[Q(connectivitysed__target_region__nomenclature__name__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_connection_region(self, userId):
        if self.type=='connectivity' and self.connection_region:
            op=operator.or_
            if self.connection_region_options=='all':
                op=operator.and_
            words=parse_tags(self.connection_region)
            keyword_filters=[Q(Q(connectivitysed__source_region__name__icontains=word) |\
                            Q(connectivitysed__source_region__abbreviation__icontains=word) | Q(connectivitysed__target_region__name__icontains=word) |\
                            Q(connectivitysed__target_region__abbreviation__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_connection_region_nomenclature(self, userId):
        if self.type=='connectivity' and self.connection_region_nomenclature:
            op=operator.or_
            if self.connection_region_nomenclature_options=='all':
                op=operator.and_
            words=parse_tags(self.connection_region_nomenclature)
            keyword_filters=[Q(Q(connectivitysed__source_region__nomenclature__name__icontains=word) |\
                            Q(connectivitysed__target_region__nomenclature__name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by control condition
    def search_control_condition(self, userId):
        if self.type=='brain imaging' and self.control_condition:
            op=operator.or_
            if self.control_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.control_condition)
            keyword_filters=[Q(brainimagingsed__control_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by experimental condition
    def search_experimental_condition(self, userId):
        if self.type=='brain imaging' and self.experimental_condition:
            op=operator.or_
            if self.experimental_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.experimental_condition)
            keyword_filters=[Q(brainimagingsed__experimental_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    # search by method
    def search_method(self, userId):
        if self.type=='brain imaging' and self.method:
            return Q(brainimagingsed__method=self.method)
        return Q()

    # search by coordinate brain region
    def search_coordinate_brain_region(self, userId):
        if self.type=='brain imaging' and self.coordinate_brain_region:
            op=operator.or_
            if self.coordinate_brain_region_options=='all':
                op=operator.and_

            words=parse_tags(self.coordinate_brain_region)
            region_filters=[Q(Q(brainimagingsed__coordinates__named_brain_region=word) |
                              Q(brainimagingsed__coordinates__coord__brainregionvolume__brain_region__name=word) |
                              Q(brainimagingsed__coordinates__coord__brainregionvolume__brain_region__parent_region__name=word))
                            for word in words]
            return reduce(op,region_filters)
        return Q()

    # search by coordinate x
    def search_x_min(self, userId):
        if self.type=='brain imaging' and self.x_min:
            return Q(brainimagingsed__coordinates__coord__x__gte=self.x_min)
        return Q()

    # search by coordinate x
    def search_x_max(self, userId):
        if self.type=='brain imaging' and self.x_max:
            return Q(brainimagingsed__coordinates__coord__x__lte=self.x_max)
        return Q()

    # search by coordinate y
    def search_y_min(self, userId):
        if self.type=='brain imaging' and self.y_min:
            return Q(brainimagingsed__coordinates__coord__y__gte=self.y_min)
        return Q()

    # search by coordinate y
    def search_y_max(self, userId):
        if self.type=='brain imaging' and self.y_max:
            return Q(brainimagingsed__coordinates__coord__y__lte=self.y_max)
        return Q()

    # search by coordinate z
    def search_z_min(self, userId):
        if self.type=='brain imaging' and self.z_min:
            return Q(brainimagingsed__coordinates__coord__z__gte=self.z_min)
        return Q()

    # search by coordinate z
    def search_z_max(self, userId):
        if self.type=='brain imaging' and self.z_max:
            return Q(brainimagingsed__coordinates__coord__z__lte=self.z_max)
        return Q()

    def search_cognitive_paradigm(self, userId):
        if self.type=='event related potential' and self.cognitive_paradigm:
            op=operator.or_
            if self.cognitive_paradigm_options=='all':
                op=operator.and_
            words=parse_tags(self.cognitive_paradigm)
            keyword_filters=[Q(erpsed__cognitive_paradigm__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_sensory_modality(self, userId):
        if self.type=='event related potential' and self.sensory_modality:
            op=operator.or_
            if self.sensory_modality_options=='all':
                op=operator.and_
            words=parse_tags(self.sensory_modality)
            keyword_filters=[Q(erpsed__sensory_modality__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_response_modality(self, userId):
        if self.type=='event related potential' and self.response_modality:
            op=operator.or_
            if self.response_modality_options=='all':
                op=operator.and_
            words=parse_tags(self.response_modality)
            keyword_filters=[Q(erpsed__response_modality__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_erp_control_condition(self, userId):
        if self.type=='event related potential' and self.erp_control_condition:
            op=operator.or_
            if self.erp_control_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.erp_control_condition)
            keyword_filters=[Q(erpsed__control_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_erp_experimental_condition(self, userId):
        if self.type=='event related potential' and self.erp_experimental_condition:
            op=operator.or_
            if self.erp_experimental_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.erp_experimental_condition)
            keyword_filters=[Q(erpsed__experimental_condition__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_erp_component_name(self, userId):
        if self.type=='event related potential' and self.erp_component_name:
            op=operator.or_
            if self.erp_component_name_options=='all':
                op=operator.and_
            words=parse_tags(self.erp_component_name)
            keyword_filters=[Q(erpsed__components__component_name__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_latency_peak_min(self, userId):
        if self.type=='event related potential' and self.latency_peak_min:
            return Q(erpsed__components__latency_peak__gte=self.latency_peak_min)
        return Q()

    def search_latency_peak_max(self, userId):
        if self.type=='event related potential' and self.latency_peak_max:
            return Q(erpsed__components__latency_peak__lte=self.latency_peak_max)
        return Q()

    def search_latency_peak_type(self, userId):
        if self.type=='event related potential' and self.latency_peak_type:
            return Q(erpsed__components__latency_peak_type=self.latency_peak_type)
        return Q()

    def search_latency_onset_min(self, userId):
        if self.type=='event related potential' and self.latency_onset_min:
            return Q(erpsed__components__latency_onset__gte=self.latency_onset_min)
        return Q()

    def search_latency_onset_max(self, userId):
        if self.type=='event related potential' and self.latency_onset_max:
            return Q(erpsed__components__latency_onset__lte=self.latency_onset_max)
        return Q()

    def search_amplitude_peak_min(self, userId):
        if self.type=='event related potential' and self.amplitude_peak_min:
            return Q(erpsed__components__amplitude_peak__gte=self.amplitude_peak_min)
        return Q()

    def search_amplitude_peak_max(self, userId):
        if self.type=='event related potential' and self.amplitude_peak_max:
            return Q(erpsed__components__amplitude_peak__lte=self.amplitude_peak_max)
        return Q()

    def search_amplitude_mean_min(self, userId):
        if self.type=='event related potential' and self.amplitude_mean_min:
            return Q(erpsed__components__amplitude_mean__gte=self.amplitude_mean_min)
        return Q()

    def search_amplitude_mean_max(self, userId):
        if self.type=='event related potential' and self.amplitude_mean_max:
            return Q(erpsed__components__amplitude_mean__lte=self.amplitude_mean_max)
        return Q()

    def search_scalp_region(self, userId):
        if self.type=='event related potential' and self.scalp_region:
            op=operator.or_
            if self.scalp_region_options=='all':
                op=operator.and_
            words=parse_tags(self.scalp_region)
            keyword_filters=[Q(erpsed__components__scalp_region__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_electrode_cap(self, userId):
        if self.type=='event related potential' and self.electrode_cap:
            op=operator.or_
            if self.electrode_cap_options=='all':
                op=operator.and_
            words=parse_tags(self.electrode_cap)
            keyword_filters=[Q(erpsed__components__electrode_cap__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_electrode_name(self, userId):
        if self.type=='event related potential' and self.electrode_name:
            op=operator.or_
            if self.electrode_name_options=='all':
                op=operator.and_
            words=parse_tags(self.electrode_name)
            keyword_filters=[Q(erpsed__components__electrode_name__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_source(self, userId):
        if self.type=='event related potential' and self.source:
            op=operator.or_
            if self.source_options=='all':
                op=operator.and_
            words=parse_tags(self.source)
            keyword_filters=[Q(erpsed__components__source__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_neurophys_condition(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition:
            op=operator.or_
            if self.neurophys_condition_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_condition)
            name_filters=[Q(neurophysiologysed__neurophysiologycondition__name__icontains=word) for word in words]
            description_filters=[Q(neurophysiologysed__neurophysiologycondition__description__icontains=word) for word in words]
            return reduce(op,name_filters) | reduce(op,description_filters)
        return Q()

    def search_neurophys_unit_type(self, userId):
        if self.type=='neurophysiology' and self.neurophys_unit_type:
            op=operator.or_
            if self.neurophys_unit_type_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_unit_type)
            keyword_filters=[Q(neurophysiologysed__neurophysiologycondition__recordingtrial__unit__type__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_neurophys_unit_region(self, userId):
        if self.type=='neurophysiology' and self.neurophys_unit_region:
            op=operator.or_
            if self.neurophys_unit_region_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_unit_region)
            name_filters=[Q(neurophysiologysed__neurophysiologycondition__recordingtrial__unit__area__name__icontains=word) for word in words]
            abbreviation_filters=[Q(neurophysiologysed__neurophysiologycondition__recordingtrial__unit__area__abbreviation__icontains=word) for word in words]
            return reduce(op,name_filters) | reduce(op,abbreviation_filters)
        return Q()
    
    def search_neurophys_subject_species(self, userId):
        if self.type=='neurophysiology' and self.neurophys_subject_species:
            op=operator.or_
            if self.neurophys_subject_species_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_subject_species)
            keyword_filters=[Q(Q(neurophysiologysed__subject_species__genus_name__icontains=word) |
                               Q(neurophysiologysed__subject_species__species_name__icontains=word) |
                               Q(neurophysiologysed__subject_species__common_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()
    
    def search_neurophys_condition_type(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type:
            return Q(neurophysiologysed__neurophysiologycondition__type=self.neurophys_condition_type)
        return Q()
    
    def search_neurophys_condition_object(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_object:
            op=operator.or_
            if self.neurophys_condition_object_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_condition_object)
            keyword_filters=[Q(neurophysiologysed__neurophysiologycondition__graspcondition__object__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_neurophys_condition_grasp(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_grasp:
            op=operator.or_
            if self.neurophys_condition_grasp_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_condition_grasp)
            keyword_filters=[Q(neurophysiologysed__neurophysiologycondition__graspcondition__grasp__icontains=word) for word in words]
            return reduce(op,keyword_filters)
        return Q()
    
    def search_neurophys_condition_object_distance_min(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_object_distance_min:
            return Q(neurophysiologysed__neurophysiologycondition__graspcondition__object_distance__gte=self.neurophys_condition_object_distance_min)
        return Q()

    def search_neurophys_condition_object_distance_max(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_object_distance_max:
            return Q(neurophysiologysed__neurophysiologycondition__graspcondition__object_distance__lte=self.neurophys_condition_object_distance_max)
        return Q()
    
    def search_neurophys_condition_whole_body_visible(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_observe' and self.neurophys_condition_whole_body_visible:
            if self.neurophys_condition_whole_body_visible=='visible':
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__whole_body_visible=True)
            else:
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__whole_body_visible=False)
        return Q()
    
    def search_neurophys_condition_demonstrator_species(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_observe' and self.neurophys_condition_demonstrator_species:
            op=operator.or_
            if self.neurophys_condition_demonstrator_species_options=='all':
                op=operator.and_
            words=parse_tags(self.neurophys_condition_demonstrator_species)
            keyword_filters=[Q(Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__demonstrator_species__genus_name__icontains=word) |
                               Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__demonstrator_species__species_name__icontains=word) |
                               Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__demonstrator_species__common_name__icontains=word)) for word in words]
            return reduce(op,keyword_filters)
        return Q()

    def search_neurophys_condition_demonstration_type(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_observe' and self.neurophys_condition_demonstration_type:
            return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__demonstration_type=self.neurophys_condition_demonstration_type)
        return Q()
    
    def search_neurophys_condition_viewing_angle_min(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_observe' and self.neurophys_condition_viewing_angle_min:
            return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__viewing_angle__gte=self.neurophys_condition_viewing_angle_min)
        return Q()

    def search_neurophys_condition_viewing_angle_max(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_observe' and self.neurophys_condition_viewing_angle_max:
            return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspobservationcondition__viewing_angle__lte=self.neurophys_condition_viewing_angle_max)
        return Q()
    
    def search_neurophys_condition_hand_visible(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_perform' and self.neurophys_condition_hand_visible:
            if self.neurophys_condition_hand_visible=='visible':
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspperformancecondition__hand_visible=True)
            else:
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspperformancecondition__hand_visible=False)
        return Q()

    def search_neurophys_condition_object_visible(self, userId):
        if self.type=='neurophysiology' and self.neurophys_condition_type=='grasp_perform' and self.neurophys_condition_object_visible:
            if self.neurophys_condition_object_visible=='visible':
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspperformancecondition__object_visible=True)
            else:
                return Q(neurophysiologysed__neurophysiologycondition__graspcondition__graspperformancecondition__object_visible=False)
        return Q()
    
def runSEDCoordSearch(seds, search_data, userId):
    sedCoords={}
    for sed in seds:
        q=Q(sed__id=sed.id)

        filters=[]

        op=operator.or_
        if search_data['search_options']=='all':
            op=operator.and_

        # create SEDCoord search
        searcher=SEDCoordSearch(search_data)
        # construct search query
        for key in search_data.iterkeys():
            # if the searcher can search by this field
            if hasattr(searcher, 'search_%s' % key):
                # add field to query
                dispatch=getattr(searcher, 'search_%s' % key)
                filters.append(dispatch(userId))
        if len(filters):
            q&=reduce(op,filters)
        results=SEDCoord.objects.filter(q).select_related('sed','coord')
        sedCoords[sed.id]=results
    return sedCoords


class SEDCoordSearch(object):
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    # search by coordinate brain region
    def search_coordinate_brain_region(self, userId):
        if self.coordinate_brain_region:
            region_q=Q()
            region_q=region_q | Q(named_brain_region=self.coordinate_brain_region)
            region_q=region_q | Q(coord__brainregionvolume__brain_region__name=self.coordinate_brain_region)
            region_q=region_q | Q(coord__brainregionvolume__brain_region__parent_region__name=self.coordinate_brain_region)
            return region_q
        return Q()

    # search by coordinate x
    def search_x_min(self, userId):
        if self.x_min:
            return Q(coord__x__gte=self.x_min)
        return Q()

    # search by coordinate x
    def search_x_max(self, userId):
        if self.x_max:
            return Q(coord__x__lte=self.x_max)
        return Q()

    # search by coordinate y
    def search_y_min(self, userId):
        if self.y_min:
            return Q(coord__y__gte=self.y_min)
        return Q()

    # search by coordinate y
    def search_y_max(self, userId):
        if self.y_max:
            return Q(coord__y__lte=self.y_max)
        return Q()

    # search by coordinate z
    def search_z_min(self, userId):
        if self.z_min:
            return Q(coord__z__gte=self.z_min)
        return Q()

    # search by coordinate z
    def search_z_max(self, userId):
        if self.z_max:
            return Q(coord__z__lte=self.z_max)
        return Q()


