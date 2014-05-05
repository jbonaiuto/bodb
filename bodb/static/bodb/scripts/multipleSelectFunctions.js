function toggleAllBOPSelect(checked, csrf_token)
{
    var boxes=document.getElementsByName('selectedBOPCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setBOPSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function setBOPSelect(bopId, checked, csrf_token)
{
    var data = { 'bopId': bopId, 'select': checked, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/bop/"+bopId+"/toggle_select/", data: data, complete: doneToggleBOPSelect };
    $.ajax(args)
    return false;
}

function toggleBOPSelect(bopId, csrf_token)
{
    var data = { 'bopId': bopId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/bop/"+bopId+"/toggle_select/", data: data, complete: doneToggleBOPSelect };
    $.ajax(args)
    return false;
}

function doneToggleBOPSelect(res, status)
{
    var txt = res.responseText;
    if(status!="success")
    {
        alert(txt);
    }
    else
    {
        var data = eval('('+txt+')');
        var elems=document.getElementsByName('bop_'+data.bop_id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            if(data.selected)
                elems[i].innerHTML='BOP added to the workspace';
            else
                elems[i].innerHTML='BOP removed from the workspace';
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
}

function toggleAllModelSelect(checked, csrf_token)
{
    var boxes=document.getElementsByName('selectedModelCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setModelSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function setModelSelect(modelId, checked, csrf_token)
{
    var data = { 'modelId': modelId, 'select':checked, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/model/"+modelId+"/toggle_select/", data: data, complete: doneToggleModelSelect };
    $.ajax(args)
    return false;
}

function toggleModelSelect(modelId, csrf_token)
{
    var data = { 'modelId': modelId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/model/"+modelId+"/toggle_select/", data: data, complete: doneToggleModelSelect };
    $.ajax(args)
    return false;
}

function doneToggleModelSelect(res, status)
{
    var txt = res.responseText;
    if(status!="success")
    {
        alert(txt);
    }
    else
    {
        var data = eval('('+txt+')');
        var elems=document.getElementsByName('model_'+data.model_id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            if(data.selected)
                elems[i].innerHTML='Model added to the workspace.';
            else
                elems[i].innerHTML='Model removed from the workspace.';
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
}

function toggleAllBrainRegionSelect(checked, csrf_token)
{
    var boxes=document.getElementsByName('selectedBrainRegionCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setBrainRegionSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function setBrainRegionSelect(regionId, checked, csrf_token)
{
    var data = { 'regionId': regionId, 'select':checked, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/brain_region/"+regionId+"/toggle_select/", data: data, complete: doneToggleBrainRegionSelect };
    $.ajax(args)
    return false;
}

function toggleBrainRegionSelect(regionId, csrf_token)
{
    var data = { 'regionId': regionId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/brain_region/"+regionId+"/toggle_select/", data: data, complete: doneToggleBrainRegionSelect };
    $.ajax(args)
    return false;
}

function doneToggleBrainRegionSelect(res, status)
{
    var txt = res.responseText;
    if(status!="success")
    {
        alert(txt);
    }
    else
    {
        var data = eval('('+txt+')');
        var elems=document.getElementsByName('brain_region_'+data.region_id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            if(data.selected)
                elems[i].innerHTML='Brain region added to the workspace.';
            else
                elems[i].innerHTML='Brain region removed from the workspace.';
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
}

function toggleAllSEDSelect(type, checked, csrf_token)
{
    var boxes=$('.selected'+type+'SEDCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setSEDSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function toggleAllSEDSSRSelect(type, checked, csrf_token)
{
    var boxes=$('.selected'+type+'SEDSSRCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setSSRSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function setSEDSelect(sedId, checked, csrf_token)
{
    var data = { 'sedId': sedId, 'select': checked, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/sed/"+sedId+"/toggle_select/", data: data, complete: doneToggleSEDSelect };
    $.ajax(args)
    return false;
}

function doneToggleSEDSelect(res, status)
{
    var txt = res.responseText;
    if(status!="success")
    {
        alert(txt);
    }
    else
    {
        var data = eval('('+txt+')');
        var elems=document.getElementsByName('selectedSEDCheckbox_'+data.sed_id);
        for(var i=0; i<elems.length; i++)
            elems[i].checked=data.selected;
        var elems=document.getElementsByName('sed_'+data.sed_id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            if(data.selected)
                elems[i].innerHTML='SED added to the workspace.';
            else
                elems[i].innerHTML='SED removed from the workspace.';
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
}

function toggleAllSSRSelect(checked, csrf_token)
{
    var boxes=document.getElementsByName('selectedSSRCheckbox');
    for(var i=0; i<boxes.length; i++)
    {
        boxes[i].checked=checked;
        setSSRSelect(boxes[i].value, checked, csrf_token);
    }
    return false;
}

function setSSRSelect(ssrId, checked, csrf_token)
{
    var data = { 'ssrId': ssrId, 'select': checked, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/ssr/"+ssrId+"/toggle_select/", data: data, complete: doneToggleSSRSelect };
    $.ajax(args)
    return false;
}


function doneToggleSSRSelect(res, status)
{
    var txt = res.responseText;
    if(status!="success")
    {
        alert(txt);
    }
    else
    {
        var data = eval('('+txt+')');
        var elems=document.getElementsByName('ssr_'+data.ssr_id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            if(data.selected)
                elems[i].innerHTML='SSR added to the workspace.';
            else
                elems[i].innerHTML='SSR removed from the workspace.';
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
}