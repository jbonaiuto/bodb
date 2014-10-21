var last_to_realign='';

function realignUnitConditionPlot(unit_id, condition_id, csrf_token)
{
    document.getElementById('realigningMsg').style.display='block';
    document.getElementById('realigningOver').style.display='block';
    last_to_realign='unit_'+unit_id+'_condition_'+condition_id;
    var event=document.getElementById('unit_'+unit_id+'_condition_'+condition_id+'_realign').value;
    var data={'unit': unit_id, 'condition': condition_id, 'event': event, 'csrfmiddlewaretoken': csrf_token};
    var args={type:"POST", url:"/bodb/sed/neurophysiology/unit_realign/", data: data, complete: doneRealignUnitConditionPlot };
    $.ajax(args);
    return false;
}

function doneRealignUnitConditionPlot(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if (status=="success")
    {
        document.getElementById('unit_'+data.unit+'_condition_'+data.condition+'_plot').src=data.diagram_url;
        if('unit_'+data.unit+'_condition_'+data.condition==last_to_realign)
        {
            document.getElementById('realigningMsg').style.display='none';
            document.getElementById('realigningOver').style.display='none';
        }
    }
    else
        alert(txt);
}