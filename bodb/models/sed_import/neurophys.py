from django.db import connections
import scipy.io
from django.db.models import Q
from bodb.models import NeurophysiologySED, Unit, BrainRegion, RecordingTrial, Event, GraspObservationCondition, Species, GraspPerformanceCondition
from registration.models import User
from uscbp import settings

def remove_all(db='default'):
    cursor=connections[db].cursor()
    cursor.execute('DELETE FROM %s.bodb_event WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_recordingtrial WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_unit WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspobservationcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspperformancecondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_graspcondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    cursor.execute('DELETE FROM %s.bodb_neurophysiologycondition WHERE 1=1' % (settings.DATABASES[db]['NAME']))
    for sed in NeurophysiologySED.objects.using(db).all():
        cursor.execute('DELETE FROM %s.bodb_neurophysiologysed WHERE sed_ptr_id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
        cursor.execute('DELETE FROM %s.bodb_sed WHERE document_ptr_id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
        cursor.execute('DELETE FROM %s.bodb_document WHERE id=%d' % (settings.DATABASES[db]['NAME'],sed.id))
    cursor.close()

def import_kraskov_data(mat_file, db='default'):
    seds={}

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

