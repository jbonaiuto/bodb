from shutil import copyfile
from django.db import connections
from neo import io, os
import scipy.io
from django.db.models import Q
from bodb.models import NeurophysiologySED, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition, NeurophysiologyCondition
from registration.models import User
from uscbp import settings

def remove_all(db='default'):
    for condition in NeurophysiologyCondition.objects.using(db).all():
        if os.path.exists(os.path.join(settings.MEDIA_ROOT,'video','neurophys_condition_%d.mp4' % condition.id)):
            os.remove(os.path.join(settings.MEDIA_ROOT,'video','neurophys_condition_%d.mp4' % condition.id))
    cursor=connections[db].cursor()
    cursor.execute('DELETE FROM %s.bodb_event WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_recordingtrial WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_unit WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspobservationcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspperformancecondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_neurophysiologycondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    for sed in NeurophysiologySED.objects.using(db).all():
        cursor.execute('DELETE FROM %s.bodb_recentlyviewedentry WHERE document_id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
        cursor.execute('DELETE FROM %s.bodb_neurophysiologysed WHERE sed_ptr_id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
        cursor.execute('DELETE FROM %s.bodb_sed WHERE document_ptr_id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
        cursor.execute('DELETE FROM %s.bodb_document WHERE id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
    cursor.close()

def import_kraskov_data(mat_file, video_dir, db='default'):
    seds={}

    bodb_video_dir=os.path.join(settings.MEDIA_ROOT,'video')
    if not os.path.exists(bodb_video_dir):
        os.mkdir(bodb_video_dir)

    collator=User.objects.using(db).get(username='jbonaiuto')
    if User.objects.using(db).filter(username='akraskov').count():
        collator=User.objects.using(db).get(username='akraskov')

    seds['m1_ptn']=NeurophysiologySED()
    seds['m1_ptn'].collator=collator
    seds['m1_ptn'].type='neurophysiology'
    seds['m1_ptn'].last_modified_by=collator
    seds['m1_ptn'].title='M1 PTN - Observation/Execution of Grasps'
    seds['m1_ptn'].brief_description='Recording of M1 pyramidal tract neurons (PTNs) while monkeys observed or performed object-directed grasps'
    seds['m1_ptn'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    seds['m1_ptn'].save(using=db)
    seds['m1_ptn'].tags.add('mirror neurons')
    seds['m1_ptn'].tags.add('macaque')
    seds['m1_ptn'].tags.add('monkey')
    seds['m1_ptn'].tags.add('action observation')
    seds['m1_ptn'].tags.add('grasping')

    seds['m1_uid']=NeurophysiologySED()
    seds['m1_uid'].collator=collator
    seds['m1_uid'].type='neurophysiology'
    seds['m1_uid'].last_modified_by=collator
    seds['m1_uid'].title='M1 Observation/Execution of Grasps'
    seds['m1_uid'].brief_description='Recording of unidentified M1 neurons while monkeys observed or performed object-directed grasps'
    seds['m1_uid'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    seds['m1_uid'].save(using=db)
    seds['m1_uid'].tags.add('mirror neurons')
    seds['m1_uid'].tags.add('macaque')
    seds['m1_uid'].tags.add('monkey')
    seds['m1_uid'].tags.add('action observation')
    seds['m1_uid'].tags.add('grasping')

    seds['f5_ptn']=NeurophysiologySED()
    seds['f5_ptn'].collator=collator
    seds['f5_ptn'].type='neurophysiology'
    seds['f5_ptn'].last_modified_by=collator
    seds['f5_ptn'].title='F5 PTN - Observation/Execution of Grasps'
    seds['f5_ptn'].brief_description='Recording of F5 pyramidal tract neurons (PTNs) while monkeys observed or performed object-directed grasps'
    seds['f5_ptn'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    seds['f5_ptn'].save(using=db)
    seds['f5_ptn'].tags.add('mirror neurons')
    seds['f5_ptn'].tags.add('macaque')
    seds['f5_ptn'].tags.add('monkey')
    seds['f5_ptn'].tags.add('action observation')
    seds['f5_ptn'].tags.add('grasping')

    seds['f5_uid']=NeurophysiologySED()
    seds['f5_uid'].collator=collator
    seds['f5_uid'].type='neurophysiology'
    seds['f5_uid'].last_modified_by=collator
    seds['f5_uid'].title='F5 Observation/Execution of Grasps'
    seds['f5_uid'].brief_description='Recording of unidentified F5 neurons while monkeys observed or performed object-directed grasps'
    seds['f5_uid'].subject_species=Species.objects.using(db).get(genus_name='Macaca',species_name='mulatta')
    seds['f5_uid'].save(using=db)
    seds['f5_uid'].tags.add('mirror neurons')
    seds['f5_uid'].tags.add('macaque')
    seds['f5_uid'].tags.add('monkey')
    seds['f5_uid'].tags.add('action observation')
    seds['f5_uid'].tags.add('grasping')

    sed_conditions={}
    for sed_id, sed in seds.iteritems():
        if not sed_id in sed_conditions:
            sed_conditions[sed_id]={}
            
        sed_conditions[sed_id]['obs_ring']=GraspObservationCondition()
        sed_conditions[sed_id]['obs_ring'].sed=sed
        sed_conditions[sed_id]['obs_ring'].name='Observe ring hook grasp'
        sed_conditions[sed_id]['obs_ring'].description='Monkeys observed the human experimenter grasping a ring using a hook grip with just the index finger'
        sed_conditions[sed_id]['obs_ring'].type='grasp_observe'
        sed_conditions[sed_id]['obs_ring'].object='ring'
        sed_conditions[sed_id]['obs_ring'].object_distance=63.8
        sed_conditions[sed_id]['obs_ring'].whole_body_visible=True
        sed_conditions[sed_id]['obs_ring'].grasp='hook'
        sed_conditions[sed_id]['obs_ring'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        sed_conditions[sed_id]['obs_ring'].demonstration_type='live'
        sed_conditions[sed_id]['obs_ring'].viewing_angle=180.0
        sed_conditions[sed_id]['obs_ring'].save(using=db)
    
        sed_conditions[sed_id]['mov_ring']=GraspPerformanceCondition()
        sed_conditions[sed_id]['mov_ring'].sed=sed
        sed_conditions[sed_id]['mov_ring'].name='Execute ring hook grasp'
        sed_conditions[sed_id]['mov_ring'].description='Monkeys grasped a ring using a hook grip with just the index finger'
        sed_conditions[sed_id]['mov_ring'].type='grasp_perform'
        sed_conditions[sed_id]['mov_ring'].object='ring'
        sed_conditions[sed_id]['mov_ring'].object_distance=34.3
        sed_conditions[sed_id]['mov_ring'].grasp='hook'
        sed_conditions[sed_id]['mov_ring'].hand_visible=True
        sed_conditions[sed_id]['mov_ring'].object_visible=True
        sed_conditions[sed_id]['mov_ring'].save(using=db)

        copyfile(os.path.join(video_dir,'ring.mp4'),os.path.join(bodb_video_dir,'neurophys_condition_%d.mp4' % sed_conditions[sed_id]['mov_ring'].id))
    
        sed_conditions[sed_id]['obs_sphere']=GraspObservationCondition()
        sed_conditions[sed_id]['obs_sphere'].sed=sed
        sed_conditions[sed_id]['obs_sphere'].name='Observe sphere whole hand grasp'
        sed_conditions[sed_id]['obs_sphere'].description='Monkeys observed the human experimenter grasping a sphere using the whole hand'
        sed_conditions[sed_id]['obs_sphere'].type='grasp_observe'
        sed_conditions[sed_id]['obs_sphere'].object='sphere'
        sed_conditions[sed_id]['obs_sphere'].grasp='whole hand'
        sed_conditions[sed_id]['obs_sphere'].object_distance=63.8
        sed_conditions[sed_id]['obs_sphere'].whole_body_visible=True
        sed_conditions[sed_id]['obs_sphere'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        sed_conditions[sed_id]['obs_sphere'].demonstration_type='live'
        sed_conditions[sed_id]['obs_sphere'].viewing_angle=180.0
        sed_conditions[sed_id]['obs_sphere'].save(using=db)
    
        sed_conditions[sed_id]['mov_sphere']=GraspPerformanceCondition()
        sed_conditions[sed_id]['mov_sphere'].sed=sed
        sed_conditions[sed_id]['mov_sphere'].name='Execute sphere whole hand'
        sed_conditions[sed_id]['mov_sphere'].description='Monkeys grasped a sphere using the whole hand'
        sed_conditions[sed_id]['mov_sphere'].type='grasp_perform'
        sed_conditions[sed_id]['mov_sphere'].object='sphere'
        sed_conditions[sed_id]['mov_sphere'].object_distance=34.3
        sed_conditions[sed_id]['mov_sphere'].grasp='whole hand'
        sed_conditions[sed_id]['mov_sphere'].hand_visible=True
        sed_conditions[sed_id]['mov_sphere'].object_visible=True
        sed_conditions[sed_id]['mov_sphere'].save(using=db)

        copyfile(os.path.join(video_dir,'sphere.mp4'),os.path.join(bodb_video_dir,'neurophys_condition_%d.mp4' % sed_conditions[sed_id]['mov_sphere'].id))
    
        sed_conditions[sed_id]['obs_trapezoid']=GraspObservationCondition()
        sed_conditions[sed_id]['obs_trapezoid'].sed=sed
        sed_conditions[sed_id]['obs_trapezoid'].name='Observe trapezoid precision grasp'
        sed_conditions[sed_id]['obs_trapezoid'].description='Monkeys observed the human experimenter grasping a trapezoid using a precision grasp with the thumb and forefinger'
        sed_conditions[sed_id]['obs_trapezoid'].type='grasp_observe'
        sed_conditions[sed_id]['obs_trapezoid'].object='trapezoid'
        sed_conditions[sed_id]['obs_trapezoid'].grasp='precision'
        sed_conditions[sed_id]['obs_trapezoid'].object_distance=63.8
        sed_conditions[sed_id]['obs_trapezoid'].whole_body_visible=True
        sed_conditions[sed_id]['obs_trapezoid'].demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        sed_conditions[sed_id]['obs_trapezoid'].demonstration_type='live'
        sed_conditions[sed_id]['obs_trapezoid'].viewing_angle=180.0
        sed_conditions[sed_id]['obs_trapezoid'].save(using=db)
    
        sed_conditions[sed_id]['mov_trapezoid']=GraspPerformanceCondition()
        sed_conditions[sed_id]['mov_trapezoid'].sed=sed
        sed_conditions[sed_id]['mov_trapezoid'].name='Execute trapezoid precision grasp'
        sed_conditions[sed_id]['mov_trapezoid'].description='Monkeys grasped a trapezoid using a precision grasp with the thumb and forefinger'
        sed_conditions[sed_id]['mov_trapezoid'].type='grasp_perform'
        sed_conditions[sed_id]['mov_trapezoid'].object='trapezoid'
        sed_conditions[sed_id]['mov_trapezoid'].object_distance=34.3
        sed_conditions[sed_id]['mov_trapezoid'].grasp='precision'
        sed_conditions[sed_id]['mov_trapezoid'].hand_visible=True
        sed_conditions[sed_id]['mov_trapezoid'].object_visible=True
        sed_conditions[sed_id]['mov_trapezoid'].save(using=db)

        copyfile(os.path.join(video_dir,'trapezoid.mp4'),os.path.join(bodb_video_dir,'neurophys_condition_%d.mp4' % sed_conditions[sed_id]['mov_trapezoid'].id))

    # create event types (if not already exist)
    # load file
    mat_file=scipy.io.loadmat(mat_file)

    trial_numbers={}

    for i in range(len(mat_file['U'][0])):
        print('importing unit %d' % i)
        area_idx=-1
        unittype_idx=-1
        index_idx=-1
        events_idx=-1

        # get indices of area, unit type, index, and events
        for idx,(dtype,o) in enumerate(mat_file['U'][0][i].dtype.descr):
            if dtype=='area':
                area_idx=idx
            elif dtype=='unittype':
                unittype_idx=idx
            elif dtype=='index':
                index_idx=idx
            elif dtype=='events':
                events_idx=idx

        # create unit
        unit=Unit()
        area=mat_file['U'][0][i][area_idx][0]
        region=BrainRegion.objects.using(db).filter(Q(Q(name=area) | Q(abbreviation=area)))
        unit.area=region[0]
        unit.type=mat_file['U'][0][i][unittype_idx][0]
        unit.save(using=db)

        if not unit.id in trial_numbers:
            trial_numbers[unit.id]={}

        sed_id=''
        if area=='M1':
            if unit.type=='PTN':
                sed_id='m1_ptn'
            elif unit.type=='UID':
                sed_id='m1_uid'
            else:
                print('SED not found: %s, %s' % (area,unit.type))
        elif area=='F5':
            if unit.type=='PTN':
                sed_id='f5_ptn'
            elif unit.type=='UID':
                sed_id='f5_uid'
            else:
                print('SED not found: %s, %s' % (area,unit.type))
        else:
            print('SED not found: %s, %s' % (area,unit.type))
                
        index=mat_file['U'][0][i][index_idx]
        events=mat_file['U'][0][i][events_idx]

        trialtype_idx=-1
        object_idx=-1
        trial_start_idx=-1
        go_idx=-1
        mo_idx=-1
        do_idx=-1
        ho_idx=-1
        hoff_idx=-1
        trial_end_idx=-1
        for idx,(dtype,o) in enumerate(events[0].dtype.descr):
            if dtype=='trialtype':
                trialtype_idx=idx
            elif dtype=='object':
                object_idx=idx
            elif dtype=='TrialStart':
                trial_start_idx=idx
            elif dtype=='Go':
                go_idx=idx
            elif dtype=='MO':
                mo_idx=idx
            elif dtype=='DO':
                do_idx=idx
            elif dtype=='HO':
                ho_idx=idx
            elif dtype=='HOff':
                hoff_idx=idx
            elif dtype=='TrialEnd':
                trial_end_idx=idx

        trial_types=events[0][0][trialtype_idx][0]
        objects=events[0][0][object_idx][0]
        trial_start_times=events[0][0][trial_start_idx][0]
        go_events=events[0][0][go_idx][0]
        mo_events=events[0][0][mo_idx][0]
        do_events=events[0][0][do_idx][0]
        ho_events=events[0][0][ho_idx][0]
        hoff_events=events[0][0][hoff_idx][0]
        trial_end_times=events[0][0][trial_end_idx][0]

        # iterate through trials
        for j in range(len(trial_types)):
            # create trial
            trial=RecordingTrial(unit=unit)
            if trial_types[j]=='h':
                if objects[j]==1:
                    trial.condition=sed_conditions[sed_id]['obs_ring']
                elif objects[j]==2:
                    trial.condition=sed_conditions[sed_id]['obs_sphere']
                elif objects[j]==4:
                    trial.condition=sed_conditions[sed_id]['obs_trapezoid']
            elif trial_types[j]=='m':
                if objects[j]==1:
                    trial.condition=sed_conditions[sed_id]['mov_ring']
                elif objects[j]==2:
                    trial.condition=sed_conditions[sed_id]['mov_sphere']
                elif objects[j]==4:
                    trial.condition=sed_conditions[sed_id]['mov_trapezoid']
            if not trial.condition.id in trial_numbers[unit.id]:
                trial_numbers[unit.id][trial.condition.id]=0
            trial_numbers[unit.id][trial.condition.id]+=1
            trial.trial_number=trial_numbers[unit.id][trial.condition.id]
            trial.start_time=trial_start_times[j]
            trial.end_time=trial_end_times[j]

            next_trial_start_time=None
            if j<len(trial_types)-1:
                next_trial_start_time=trial_start_times[j+1]

            previous_trial=None
            if trial_numbers[unit.id][trial.condition.id]>1:
                previous_trial=RecordingTrial.objects.using(db).get(unit=unit, condition=trial.condition,
                    trial_number=trial_numbers[unit.id][trial.condition.id]-1)

            # load spikes
            spike_times=[]
            for k in range(len(index)):
                if previous_trial is None:
                    if index[k,0]>=trial.start_time-1.0:
                        if next_trial_start_time is None:
                            if index[k,0]<trial.end_time+1.0:
                                spike_times.append(index[k,0])
                        elif index[k,0]<trial.end_time+1.0 and index[k,0]<next_trial_start_time:
                            spike_times.append(index[k,0])
                elif index[k,0]>=trial.start_time-1.0 and index[k,0]>=previous_trial.end_time:
                    if next_trial_start_time is None:
                        if index[k,0]<trial.end_time+1.0:
                            spike_times.append(index[k,0])
                    elif index[k,0]<trial.end_time+1.0 and index[k,0]<next_trial_start_time:
                        spike_times.append(index[k,0])

            trial.spike_times=','.join([str(x) for x in sorted(spike_times)])
            trial.save(using=db)

            # create trial events
            go_event=Event(name='go', description='go signal', trial=trial, time=go_events[j])
            go_event.save(using=db)

            mo_event=Event(name='mo', description='movement onset', trial=trial, time=mo_events[j])
            mo_event.save(using=db)

            do_event=Event(name='do', description='object displacement onset', trial=trial, time=do_events[j])
            do_event.save(using=db)

            ho_event=Event(name='ho', description='stable hold onset', trial=trial, time=ho_events[j])
            ho_event.save(using=db)

            hoff_event=Event(name='hoff', description='hold offset', trial=trial, time=hoff_events[j])
            hoff_event.save(using=db)


def import_bonini_data(nex_files, skip_first_start, db='default'):
    collator=User.objects.using(db).get(username='jbonaiuto')

    event_map={
        'EVT01': ('go','go signal'),
        'EVT02': ('co','object contact'),
        'EVT03': ('co','object contact'),
        'EVT04': ('co','object contact'),
        'EVT05': ('do','object displacement onset'),
        'EVT07': ('rew','reward onset'),
        'EVT09': ('fix','fixation onset'),
        'EVT13': ('lon','light on'),
        'EVT17': ('mo','movement onset'),
        'EVT32': ('loff','light off'),
        'EVT28': ('mo','movement onset'),
    }
    sed_title='F5 mirror neuron depth recording - Observation/Execution of Grasps'
    if NeurophysiologySED.objects.using(db).filter(title=sed_title).count():
        sed=NeurophysiologySED.objects.using(db).filter(title=sed_title)[0]
    else:
        sed=NeurophysiologySED()
        sed.collator=collator
        sed.type='neurophysiology'
        sed.last_modified_by=User.objects.get(username='jbonaiuto')
        sed.title=sed_title
        sed.brief_description='Recording of unidentified F5 neurons while monkeys observed or performed object-directed grasps'
        sed.subject_species=Species.objects.get(genus_name='Macaca',species_name='mulatta')
        sed.save(using=db)
    print('importing sed %d' % sed.id)

    if GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe ring hook grasp').count():
        obs_ring_condition=GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe ring hook grasp')[0]
    else:
        obs_ring_condition=GraspObservationCondition()
        obs_ring_condition.sed=sed
        obs_ring_condition.name='Observe ring hook grasp'
        obs_ring_condition.description='Monkeys observed the human experimenter grasping a ring using a hook grip with just the index finger'
        obs_ring_condition.type='grasp_observe'
        obs_ring_condition.object='ring'
        obs_ring_condition.grasp='hook'
        # What is the distance?
        obs_ring_condition.object_distance=63.8
        # Is the whole body visible?
        obs_ring_condition.whole_body_visible=True
        obs_ring_condition.demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_ring_condition.demonstration_type='live'
        obs_ring_condition.viewing_angle=180.0
        obs_ring_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute ring hook grasp - go').count():
        mov_ring_go_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute ring hook grasp - go')[0]
    else:
        mov_ring_go_light_condition=GraspPerformanceCondition()
        mov_ring_go_light_condition.sed=sed
        mov_ring_go_light_condition.name='Execute ring hook grasp - go'
        mov_ring_go_light_condition.description='Monkeys grasped a ring using a hook grip with just the index finger'
        mov_ring_go_light_condition.type='grasp_perform'
        mov_ring_go_light_condition.object='ring'
        # What is the distance?
        mov_ring_go_light_condition.object_distance=34.3
        mov_ring_go_light_condition.grasp='hook'
        # Is the hand visible?
        mov_ring_go_light_condition.hand_visible=True
        # Is the object visible?
        mov_ring_go_light_condition.object_visible=True
        mov_ring_go_light_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute ring hook grasp in the dark - go').count():
        mov_ring_go_dark_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute ring hook grasp in the dark - go')[0]
    else:
        mov_ring_go_dark_condition=GraspPerformanceCondition()
        mov_ring_go_dark_condition.sed=sed
        mov_ring_go_dark_condition.name='Execute ring hook grasp in the dark - go'
        mov_ring_go_dark_condition.description='Monkeys grasped a ring in the dark using a hook grip with just the index finger'
        mov_ring_go_dark_condition.type='grasp_perform'
        mov_ring_go_dark_condition.object='ring'
        # What is the distance?
        mov_ring_go_dark_condition.object_distance=34.3
        mov_ring_go_dark_condition.grasp='hook'
        # Is the hand visible?
        mov_ring_go_dark_condition.hand_visible=False
        # Is the object visible?
        mov_ring_go_dark_condition.object_visible=False
        mov_ring_go_dark_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe ring - nogo').count():
        mov_ring_nogo_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe ring - nogo')[0]
    else:
        mov_ring_nogo_light_condition=GraspPerformanceCondition()
        mov_ring_nogo_light_condition.sed=sed
        mov_ring_nogo_light_condition.name='Observe ring - nogo'
        mov_ring_nogo_light_condition.description='Monkeys observed a ring'
        mov_ring_nogo_light_condition.type='grasp_perform'
        mov_ring_nogo_light_condition.object='ring'
        # What is the distance?
        mov_ring_nogo_light_condition.object_distance=34.3
        mov_ring_nogo_light_condition.grasp='hook'
        # Is the hand visible?
        mov_ring_nogo_light_condition.hand_visible=True
        # Is the object visible?
        mov_ring_nogo_light_condition.object_visible=True
        mov_ring_nogo_light_condition.save(using=db)

    # What type of grasp was used for the small cone
    if GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe small cone whole hand grasp').count():
        obs_small_cone_condition=GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe small cone whole hand grasp')[0]
    else:
        obs_small_cone_condition=GraspObservationCondition()
        obs_small_cone_condition.sed=sed
        obs_small_cone_condition.name='Observe small cone whole hand grasp'
        obs_small_cone_condition.description='Monkeys observed the human experimenter grasping a small cone using the whole hand'
        obs_small_cone_condition.type='grasp_observe'
        obs_small_cone_condition.object='small cone'
        # Is this right?
        obs_small_cone_condition.grasp='whole hand'
        # What is the distance?
        obs_small_cone_condition.object_distance=63.8
        # Is the whole body visible?
        obs_small_cone_condition.whole_body_visible=True
        obs_small_cone_condition.demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_small_cone_condition.demonstration_type='live'
        obs_small_cone_condition.viewing_angle=180.0
        obs_small_cone_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute small cone whole hand grasp - go').count():
        mov_small_cone_go_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute small cone whole hand grasp - go')[0]
    else:
        mov_small_cone_go_light_condition=GraspPerformanceCondition()
        mov_small_cone_go_light_condition.sed=sed
        mov_small_cone_go_light_condition.name='Execute small cone whole hand grasp - go'
        mov_small_cone_go_light_condition.description='Monkeys grasped a small cone using a the whole hand'
        mov_small_cone_go_light_condition.type='grasp_perform'
        mov_small_cone_go_light_condition.object='small cone'
        # What is the distance?
        mov_small_cone_go_light_condition.object_distance=34.3
        # Is this right?
        mov_small_cone_go_light_condition.grasp='whole hand'
        # Is the hand visible?
        mov_small_cone_go_light_condition.hand_visible=True
        # Is the object visible?
        mov_small_cone_go_light_condition.object_visible=True
        mov_small_cone_go_light_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute small cone whole hand grasp in the dark - go').count():
        mov_small_cone_go_dark_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute small cone whole hand grasp in the dark - go')[0]
    else:
        mov_small_cone_go_dark_condition=GraspPerformanceCondition()
        mov_small_cone_go_dark_condition.sed=sed
        mov_small_cone_go_dark_condition.name='Execute small cone whole hand grasp in the dark - go'
        mov_small_cone_go_dark_condition.description='Monkeys grasped a small cone in the dark using a the whole hand'
        mov_small_cone_go_dark_condition.type='grasp_perform'
        mov_small_cone_go_dark_condition.object='small cone'
        # What is the distance?
        mov_small_cone_go_dark_condition.object_distance=34.3
        # Is this right?
        mov_small_cone_go_dark_condition.grasp='whole hand'
        # Is the hand visible?
        mov_small_cone_go_dark_condition.hand_visible=False
        # Is the object visible?
        mov_small_cone_go_dark_condition.object_visible=False
        mov_small_cone_go_dark_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe small cone - nogo').count():
        mov_small_cone_nogo_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe small cone - nogo')[0]
    else:
        mov_small_cone_nogo_light_condition=GraspPerformanceCondition()
        mov_small_cone_nogo_light_condition.sed=sed
        mov_small_cone_nogo_light_condition.name='Observe small cone - nogo'
        mov_small_cone_nogo_light_condition.description='Monkeys observed a small cone'
        mov_small_cone_nogo_light_condition.type='grasp_perform'
        mov_small_cone_nogo_light_condition.object='small cone'
        # What is the distance?
        mov_small_cone_nogo_light_condition.object_distance=34.3
        # Is this right?
        mov_small_cone_nogo_light_condition.grasp='whole hand'
        # Is the hand visible?
        mov_small_cone_nogo_light_condition.hand_visible=True
        # Is the object visible?
        mov_small_cone_nogo_light_condition.object_visible=True
        mov_small_cone_nogo_light_condition.save(using=db)

    # What type of grasp was used for the big cone
    if GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe big cone whole hand grasp').count():
        obs_big_cone_condition=GraspObservationCondition.objects.using(db).filter(sed=sed,name='Observe big cone whole hand grasp')[0]
    else:
        obs_big_cone_condition=GraspObservationCondition()
        obs_big_cone_condition.sed=sed
        obs_big_cone_condition.name='Observe big cone whole hand grasp'
        obs_big_cone_condition.description='Monkeys observed the human experimenter grasping a big cone using the whole hand'
        obs_big_cone_condition.type='grasp_observe'
        obs_big_cone_condition.object='big cone'
        # Is this right?
        obs_big_cone_condition.grasp='whole hand'
        # What is the distance?
        obs_big_cone_condition.object_distance=63.8
        # Is the whole body visible?
        obs_big_cone_condition.whole_body_visible=True
        obs_big_cone_condition.demonstrator_species=Species.objects.using(db).get(genus_name='Homo',species_name='sapiens')
        obs_big_cone_condition.demonstration_type='live'
        obs_big_cone_condition.viewing_angle=180.0
        obs_big_cone_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute big cone whole hand grasp - go').count():
        mov_big_cone_go_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute big cone whole hand grasp - go')[0]
    else:
        mov_big_cone_go_light_condition=GraspPerformanceCondition()
        mov_big_cone_go_light_condition.sed=sed
        mov_big_cone_go_light_condition.name='Execute big cone whole hand grasp - go'
        mov_big_cone_go_light_condition.description='Monkeys grasped a big cone using a the whole hand'
        mov_big_cone_go_light_condition.type='grasp_perform'
        mov_big_cone_go_light_condition.object='big cone'
        # What is the distance?
        mov_big_cone_go_light_condition.object_distance=34.3
        # Is this right?
        mov_big_cone_go_light_condition.grasp='whole hand'
        # Is the hand visible?
        mov_big_cone_go_light_condition.hand_visible=True
        # Is the object visible?
        mov_big_cone_go_light_condition.object_visible=True
        mov_big_cone_go_light_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute big cone whole hand grasp in the dark - go').count():
        mov_big_cone_go_dark_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Execute big cone whole hand grasp in the dark - go')[0]
    else:
        mov_big_cone_go_dark_condition=GraspPerformanceCondition()
        mov_big_cone_go_dark_condition.sed=sed
        mov_big_cone_go_dark_condition.name='Execute big cone whole hand grasp in the dark - go'
        mov_big_cone_go_dark_condition.description='Monkeys grasped a big cone in the dark using a the whole hand'
        mov_big_cone_go_dark_condition.type='grasp_perform'
        mov_big_cone_go_dark_condition.object='big cone'
        # What is the distance?
        mov_big_cone_go_dark_condition.object_distance=34.3
        # Is this right?
        mov_big_cone_go_dark_condition.grasp='whole hand'
        # Is the hand visible?
        mov_big_cone_go_dark_condition.hand_visible=False
        # Is the object visible?
        mov_big_cone_go_dark_condition.object_visible=False
        mov_big_cone_go_dark_condition.save(using=db)

    if GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe big cone - nogo').count():
        mov_big_cone_nogo_light_condition=GraspPerformanceCondition.objects.using(db).filter(sed=sed,name='Observe big cone - nogo')[0]
    else:
        mov_big_cone_nogo_light_condition=GraspPerformanceCondition()
        mov_big_cone_nogo_light_condition.sed=sed
        mov_big_cone_nogo_light_condition.name='Observe big cone - nogo'
        mov_big_cone_nogo_light_condition.description='Monkeys observed a big cone'
        mov_big_cone_nogo_light_condition.type='grasp_perform'
        mov_big_cone_nogo_light_condition.object='big cone'
        # What is the distance?
        mov_big_cone_nogo_light_condition.object_distance=34.3
        # Is this right?
        mov_big_cone_nogo_light_condition.grasp='whole hand'
        # Is the hand visible?
        mov_big_cone_nogo_light_condition.hand_visible=True
        # Is the object visible?
        mov_big_cone_nogo_light_condition.object_visible=True
        mov_big_cone_nogo_light_condition.save(using=db)


    # Are units from sessions on different days with the same name the same unit?
    unit_ids={}
    for nex_idx, nex_file in enumerate(nex_files):
        r=io.NeuroExplorerIO(filename=nex_file)
        block=r.read(cascade=True, lazy=False)[0]
        for seg_idx, seg in enumerate(block.segments):
            print('importing segment %d' % seg_idx)

            events={}
            for idx,event_array in enumerate(seg.eventarrays):
                events[event_array.annotations['channel_name']]=idx

            for unit_idx,st in enumerate(seg.spiketrains):
                print('importing unit %s' % st.name)
                if st.name in unit_ids:
                    unit=Unit.objects.get(id=unit_ids[st.name])
                else:
                    unit=Unit()
                    area='F5'
                    region=BrainRegion.objects.filter(Q(Q(name=area) | Q(abbreviation=area)))
                    unit.area=region[0]
                    unit.type='UID'
                    unit.save()
                    unit_ids[st.name]=unit.id

                last_epoch_start=0
                # Iterature through epochs:
                for epoch_idx, epocharray in enumerate(seg.epocharrays):
                    print('importing epoch %d' % epoch_idx)
                    epoch_duration=epocharray.durations.rescale('s').magnitude.item(0)
                    epoch_type=epocharray.annotations['channel_name']
                    if not epoch_type=='AllFile':
                        trial_start_times=[]
                        trial_end_times=[]

                        for time_idx,time in enumerate(seg.eventarrays[events['Start']].times):
                            if time_idx>0 or not skip_first_start[nex_idx]:
                                if last_epoch_start<=time<last_epoch_start+epoch_duration:
                                    trial_start_times.append(time.rescale('s').magnitude.item(0))
                        for time in seg.eventarrays[events['Stop']].times:
                            if last_epoch_start<=time<last_epoch_start+epoch_duration:
                                trial_end_times.append(time.rescale('s').magnitude.item(0))

                        start_time=last_epoch_start
                        # iterate through trials
                        for trial_idx in range(len(trial_start_times)):
                            # create trial
                            trial=RecordingTrial(unit=unit)
                            trial.trial_number=trial_idx+1
                            #trial.start_time=trial_start_times[trial_idx]
                            trial.start_time=start_time
                            if trial_idx<len(trial_end_times):
                                trial.end_time=trial_end_times[trial_idx]
                            else:
                                trial.end_time=last_epoch_start+epoch_duration
                            start_time=trial.end_time
                            print('importing trial %d, %.3f-%.3f' % (trial_idx,trial.start_time,trial.end_time))

                            spike_times=[]
                            for spike_time in st.rescale('s').magnitude:
                                if trial.start_time <= spike_time < trial.end_time:
                                    spike_times.append(spike_time)
                            trial.spike_times=','.join([str(x) for x in sorted(spike_times)])

                            trial.save()

                            for event,evt_idx in events.iteritems():
                                for evt_time in seg.eventarrays[evt_idx].times:
                                    if trial.start_time <= evt_time < trial.end_time:
                                        # create trial events
                                        new_event=Event(name=event, description='', trial=trial, time=evt_time.rescale('s').magnitude.item(0))
                                        new_event.save()

                            deleted=False
#                            if Event.objects.filter(name='EVT08',trial=trial).count():
#                                print('Error - deleting trial')
#                                trial.delete()
#                                deleted=True
                            #elif epoch_type=='OBSERVATION_TASK':
                            if epoch_type=='OBSERVATION_TASK':
                                # Look for object marker event
                                if Event.objects.filter(name='EVT18',trial=trial).count():
                                    trial.condition=obs_small_cone_condition
                                elif Event.objects.filter(name='EVT19',trial=trial).count():
                                    trial.condition=obs_ring_condition
                                elif Event.objects.filter(name='EVT20',trial=trial).count():
                                    trial.condition=obs_big_cone_condition
                                else:
                                    trial.delete()
                                    deleted=True
                            elif epoch_type=='VISUOMOTOR_TASK':
                                if Event.objects.filter(name='ev_01_LightON_visualCOR_RNG',trial=trial).count():
                                    trial.condition=mov_ring_nogo_light_condition
                                elif Event.objects.filter(name='ev_02_LightON_motorCORc1_RNG',trial=trial).count():
                                    trial.condition=mov_ring_go_light_condition
                                elif Event.objects.filter(name='ev_04_Pull_CORc2_RNG',trial=trial).count():
                                    trial.condition=mov_ring_go_dark_condition
                                elif Event.objects.filter(name='ev_05_LightON_visualCOR_SML',trial=trial).count():
                                    trial.condition=mov_small_cone_nogo_light_condition
                                elif Event.objects.filter(name='ev_06_LightON_motorCORc1_SML',trial=trial).count():
                                    trial.condition=mov_small_cone_go_light_condition
                                elif Event.objects.filter(name='ev_08_Pull_CORc2_SML',trial=trial).count():
                                    trial.condition=mov_small_cone_go_dark_condition
                                elif Event.objects.filter(name='ev_09_LightON_visualCOR_BIG',trial=trial).count:
                                    trial.conditon=mov_big_cone_nogo_light_condition
                                elif Event.objects.filter(name='ev_10_LightON_motorCORc1_BIG',trial=trial).count:
                                    trial.condition=mov_big_cone_go_light_condition
                                elif Event.objects.filter(name='ev_10_LightON_motorCORc1_BIG',trial=trial).count:
                                    trial.condition=mov_big_cone_go_dark_condition
                                else:
                                    trial.delete()
                                    deleted=True

                            if not deleted:
                                trial.save()
                                events_to_delete=[]
                                for event in Event.objects.filter(trial=trial):
                                    old_evt_name=event.name
                                    if old_evt_name in event_map:
                                        event.name=event_map[old_evt_name][0]
                                        event.description=event_map[old_evt_name][1]
                                        event.save()
                                    else:
                                        events_to_delete.append(event.id)
                                Event.objects.filter(id__in=events_to_delete).delete()

                        last_epoch_start=last_epoch_start+epoch_duration


if __name__=='__main__':
    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uscbp.settings")

    #from django.core.management import execute_from_command_line
    #sed=NeurophysiologySED.objects.all()[0]
    #unit=Unit.objects.get(id=5)
    #condition=NeurophysiologyCondition.objects.get(name='Observe small cone whole hand grasp')
    #unit.plot_condition_spikes([condition.id], 0.05)

    remove_all()
    import_kraskov_data('../neurophysSED/kraskov_data/units4BODB.mat','../neurophysSED/kraskov_data/')
    #import_bonini_data(['../neurophysSED/bonini_data/01_PIC_F5_09022012_mot_mirror_mrgSORTED.nex',
    #                    '../neurophysSED/bonini_data/02_Pic_F5_10022012_mot_mirror_mrgSORTED.nex'],[True, False])
