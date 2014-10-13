import scipy.io
from django.db.models import Q
from bodb.models import NeurophysiologySED, NeurophysiologyCondition, Unit, BrainRegion, RecordingTrial, Event
from registration.models import User

def import_kraskov_data(mat_file, db='default'):
    sed=NeurophysiologySED()
    sed.collator=User.objects.get(username='jbonaiuto')
    sed.type='neurophysiology'
    sed.last_modified_by=User.objects.get(username='jbonaiuto')
    sed.title='M1 PTN - Observation/Execution of Grasps'
    sed.brief_description='Recording of M1 pyramidal tract neurons (PTNs) while monkeys observed or performed object-directed grasps'
    sed.save(using=db)

    obs_ring_condition=NeurophysiologyCondition()
    obs_ring_condition.sed=sed
    obs_ring_condition.name='Observe ring hook grasp'
    obs_ring_condition.description='Monkeys observed the human experimenter grasping a ring using a hook grip with just the index finger'
    obs_ring_condition.save(using=db)

    mov_ring_condition=NeurophysiologyCondition()
    mov_ring_condition.sed=sed
    mov_ring_condition.name='Execute ring hook grasp'
    mov_ring_condition.description='Monkeys grasped a ring using a hook grip with just the index finger'
    mov_ring_condition.save(using=db)

    obs_sphere_condition=NeurophysiologyCondition()
    obs_sphere_condition.sed=sed
    obs_sphere_condition.name='Observe sphere whole hand grasp'
    obs_sphere_condition.description='Monkeys observed the human experimenter grasping a sphere using the whole hand'
    obs_sphere_condition.save(using=db)

    mov_sphere_condition=NeurophysiologyCondition()
    mov_sphere_condition.sed=sed
    mov_sphere_condition.name='Execute sphere whole hand'
    mov_sphere_condition.description='Monkeys grasped a sphere using the whole hand'
    mov_sphere_condition.save(using=db)

    obs_trapezoid_condition=NeurophysiologyCondition()
    obs_trapezoid_condition.sed=sed
    obs_trapezoid_condition.name='Observe trapezoid precision grasp'
    obs_trapezoid_condition.description='Monkeys observed the human experimenter grasping a trapezoid using a precision grasp with the thumb and forefinger'
    obs_trapezoid_condition.save(using=db)

    mov_trapezoid_condition=NeurophysiologyCondition()
    mov_trapezoid_condition.sed=sed
    mov_trapezoid_condition.name='Execute trapezoid precision grasp'
    mov_trapezoid_condition.description='Monkeys grasped a trapezoid using a precision grasp with the thumb and forefinger'
    mov_trapezoid_condition.save(using=db)

    # create event types (if not already exist)
    # load file
    mat_file=scipy.io.loadmat(mat_file)

    for i in range(len(mat_file['U'][0])):
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
        region=BrainRegion.objects.filter(Q(Q(name=area) | Q(abbreviation=area)))
        unit.area=region[0]
        unit.type=mat_file['U'][0][i][unittype_idx][0]
        unit.save(using=db)

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
            trial.trial_number=j+1
            if trial_types[j]=='h':
                if objects[j]==1:
                    trial.condition=obs_ring_condition
                elif objects[j]==2:
                    trial.condition=obs_sphere_condition
                elif objects[j]==4:
                    trial.condition=obs_trapezoid_condition
            elif trial_types[j]=='m':
                if objects[j]==1:
                    trial.condition=mov_ring_condition
                elif objects[j]==2:
                    trial.condition=mov_sphere_condition
                elif objects[j]==4:
                    trial.condition=mov_trapezoid_condition
            trial.start_time=trial_start_times[j]
            trial.end_time=trial_end_times[j]

            next_trial_start_time=None
            if j<len(trial_types)-1:
                next_trial_start_time=trial_start_times[j+1]

            previous_trial=None
            if j>0:
                previous_trial=RecordingTrial.objects.get(unit=unit, trial_number=j)

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

