function showPopup(windowName, width, height, href)
{
    if (href.indexOf('?') == -1)
        href += '?_popup=1';
    else
        href  += '&_popup=1';
    var win = window.open(href, windowName, 'height='+height+',width='+width+',resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function clearSpan(doc, spanId)
{
    if(doc.getElementById(spanId)!=null)
        doc.getElementById(spanId).innerHTML='';
    return false;
}

function checkboxSetAll(name, val)
{
    checkboxes=document.getElementsByName(name);
    for(var i=0; i<checkboxes.length; i++)
    {
        checkboxes[i].checked=val;
    }
    return false;
}

function deleteInlineForm(prefix, idx){
    document.getElementById('id_'+prefix+'-'+idx+'-DELETE').value='on';
    document.getElementById(prefix+'-'+idx).style.display='none';
    return false;
}

function addInlineForm(div_id, prefix, form_prefix){
    var count = $('#'+div_id).children().length;
    var tmplMarkup = $('#'+prefix+'-template').html();
    var compiledTmpl = _.template(tmplMarkup, { id : count });
    $('#'+div_id).append(compiledTmpl);
    // update form count
    $('#id_'+form_prefix+'-TOTAL_FORMS').attr('value', count+1);
    return false;
}

function addSEDMultiple(type, sed_id, data){
    var count = $('#'+type+'_seds').children().length;
    var tmplMarkup = $('#'+type+'_sed-template').html();
    var compiledTmpl = _.template(tmplMarkup, { id : count, sed: sed_id, title: data[0], brief_description: data[1], type: data[2] });
    $('#'+type+'_seds').append(compiledTmpl);
    // update form count
    $('#id_'+type+'_sed-TOTAL_FORMS').attr('value', count+1);
    return false;
}

/**
 * Validates one field (only current constraint is that something is entered). Returns 1 if error, 0 if no error
 * @param fieldName - name of the field
 * @param label - field label
 * @param errorSpanName - name of the span element to add error messages to
 */
function validateField(fieldName, label, errorSpanName)
{
    var fieldElem=document.getElementById('id_'+fieldName);
    if(fieldElem!=null && (fieldElem.value==null || fieldElem.value.length==0))
    {
        if(document.getElementById(errorSpanName).innerHTML.length>0)
            document.getElementById(errorSpanName).innerHTML+='<br>';
        document.getElementById(errorSpanName).innerHTML+=label+' required';
        return 1;
    }
    return 0;
}

function validateURLField(fieldName, label, errorSpanName)
{
    var fieldElem=document.getElementById('id_'+fieldName);
    if(fieldElem!=null)
    {
        if(fieldElem.value!=null && fieldElem.value.length>0)
        {
            if(/^(http|https|ftp):\/\/[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,5}(:[0-9]{1,5})?(\/.*)?$/i.test(fieldElem.value)){
                return 0;
            } else {
                if(document.getElementById(errorSpanName).innerHTML.length>0)
                    document.getElementById(errorSpanName).innerHTML+='<br>';
                document.getElementById(errorSpanName).innerHTML+=label+': valid URL required';
                return 1;
            }
        }
    }
    return 0;
}

/**
 * Validates all the fields in an inline form. Returns number of errors
 * @param formName - name of the form
 * @param fields - list of fields in the forms
 * @param labels - list of labels for the fields in the form
 */
function validateInlineForm(formName, fields, labels)
{
    var errors=0;
    var numForms=document.getElementById('id_'+formName+'-TOTAL_FORMS').value;
    for(var i=0; i<numForms; i++)
    {
        var deleteElem=document.getElementById('id_'+formName+'-'+i+'-DELETE');
        if(deleteElem==null || deleteElem.value!='on')
        {
            clearSpan(document, formName+'_'+i+'_errors');

            for(var j=0; j<fields.length; j++)
            {
                errors+=validateField(formName+'-'+i+'-'+fields[j], labels[j], formName+'_'+i+'_errors');
            }
        }
    }
    return errors;
}

function switchTab(divid, offids)
{
    for (var i=0; i<offids.length; i++)
    {
        if(offids[i]!=divid)
        {
            if(document.getElementById(offids[i]+'Div')!=null)
            {
                document.getElementById(offids[i]+'Div').style.display = 'none';
                if(document.getElementById(offids[i]+'Tab')!=null)
                    document.getElementById(offids[i]+'Tab').className = 'unselectedTab';
                if(document.getElementById(offids[i]+'Header')!=null)
                    clearSpan(document, offids[i]+'Header');
            }
        }
    }
    document.getElementById(divid+'Div').style.display = 'block';
    if(document.getElementById(divid+'Tab')!=null)
        document.getElementById(divid+'Tab').className = 'selectedTab';
    if(document.getElementById(divid+'Header')!=null)
        document.getElementById(divid+'Header').innerHTML='</b><b class="c2f"></b><b class="c3f"></b><b class="c4f"></b>';
    return false;
}

function openHelp(helpPage)
{
    window.open('http://neuroinformatics.usc.edu/resources/'+helpPage, 'BODB Help - '+helpPage, 'width=800,height=400,resizable=1,scrollbars=1');
    return false;
}

function getTRTag(idx)
{
    if(idx%2==0)
        return 'even_row';
    else
        return 'odd_row';
}

function toggleSEDSelect(sedId, csrf_token)
{
    var data = { 'sedId': sedId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/sed/"+sedId+"/toggle_select/", data: data, complete: doneToggleSEDSelect };
    $.ajax(args);
    return false;
}

function toggleSSRSelect(ssrId, csrf_token)
{
    var data = { 'ssrId': ssrId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/ssr/"+ssrId+"/toggle_select/", data: data, complete: doneToggleSSRSelect };
    $.ajax(args);
    return false;
}

function toggleFavorite(id, iconId, csrf_token)
{
    var data = { 'id': id, 'icon_id': iconId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/favorite/toggle/", data: data, complete: doneToggleFavorite };
    $.ajax(args);
    return false;
}

function doneToggleFavorite(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if(status=="success")
    {
        var elems=document.getElementsByName(data.icon_id);
        for(var i=0; i<elems.length; i++)
        {
            if(data.action=='added')
                elems[i].src='/static/bodb/images/star.png';
            else
                elems[i].src='/static/bodb/images/grey_star.png';
        }
    }
    return false;
}

function sedCoordSelect(selected, coordId, csrf_token)
{
    var data = { 'coordId': coordId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/sed/coord/"+coordId+"/select/", data: data, complete: doneCoordSelect };
    if(!selected)
        args = { type: "POST", url: "/bodb/sed/coord/"+coordId+"/unselect/", data: data, complete: doneCoordSelect };
    $.ajax(args);
    return false;
}

function doneCoordSelect(res, status)
{
    if (status!="success")
        alert(res.responseText);
    else
    {
        var txt = res.responseText;
        var data = eval('('+txt+')');
        var msg='Coordinated unselected';
        if(data.selected)
            msg='Coordinate selected';
        var elems=document.getElementsByName('coord_'+data.sed_id+'_'+data.id+'_message');
        for(var i=0; i<elems.length; i++)
        {
            elems[i].innerHTML=msg;
            elems[i].style.display='block';
            $('#'+elems[i].id).fadeOut(5000, function(){});
        }
    }
    return false;

}

function setAllCoordinatesSelected(selected, csrf_token)
{
    checkboxes=document.getElementsByName('sed_coord_select');
    for(var i=0; i<checkboxes.length; i++)
    {
        if(checkboxes[i].checked!=selected)
        {
            checkboxes[i].checked=selected;
            sedCoordSelect(selected, checkboxes[i].value, csrf_token);
        }
    }
    return false;
}

function managePermissions(documentId)
{
    return showPopup('Manage permissions',600,500,'/bodb/document/'+documentId+'/permissions/');
}

function publicRequest(documentId, csrf_token)
{
    var data = { 'documentId': documentId, 'csrfmiddlewaretoken': csrf_token };
    var args = { type: "POST", url: "/bodb/document/public_request/", data: data, complete: donePublicRequest };
    $.ajax(args);
    return false;
}

function donePublicRequest(res, status)
{
    if (status!="success")
        alert(res.responseText);
    else
        document.getElementById('public_request').innerHTML='Public request sent.';
    return false;
}

function exportReferences(csrf_token)
{
    var format=$('.lit_export_format')[0].value;
    var ids=new Array();
    var lit_elems=document.getElementsByName('literature');
    var idx=0;
    for(var i=0; i<lit_elems.length; i++)
    {
        if(ids.indexOf(lit_elems[i].value)<0)
        {
            ids[idx]=lit_elems[i].value;
            idx++;
        }
    }
    if(idx>0)
    {
        var data = { 'format': format, 'ids': ids, 'csrfmiddlewaretoken': csrf_token };
        var args = { type: "POST", url: "/bodb/literature/export/", data: data, complete : doneReferenceExport };
        $.ajax(args);
    }
    return false;
}
function doneReferenceExport(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if(status=="success")
    {
        document.getElementById("fileForm").action='/media/export/'+data.file_name;
        document.getElementById("fileForm").submit();
    }
    return false;
}

function generateConnDiagram(connSEDIds, graphTool, graphId, csrf_token)
{
    var data={'graphTool': graphTool, 'connSEDIds': connSEDIds, 'graphID': graphId, 'csrfmiddlewaretoken': csrf_token};
    var args={type:"POST", url:"/bodb/sed/connectivityDiagram/", data: data, complete: doneConnDiagram };
    document.getElementById(graphId+'Msg').innerHTML="<div align='center' style='color:red;'>Generating diagram...</div>";
    $.ajax(args);
    return false;
}

function doneConnDiagram(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if (status=="success")
    {
        document.getElementById(data.graphId).src='/media/'+data.connDiagram;
        document.getElementById(data.graphId+'Map').innerHTML=data.connMap;
        document.getElementById(data.graphId+'Msg').innerHTML="Click on a node to view brain region details. Click on an edge to view connection details";
        document.getElementById(data.graphId+'Div').style.display='block';
        $('input:button').button();
        $('#'+data.graphId).zoomable();
        $('#'+data.graphId).smartZoom({'containerClass':'zoomableContainer'});
    }
    else
        alert(txt);
}

function generateBOPDiagram(graphTool, graphId, csrf_token)
{
    var bopIds=[];
    var bopCheckboxes=$('.selectedBOPCheckbox');
    for(var i=0; i<bopCheckboxes.length; i++)
        bopIds.push(bopCheckboxes[i].value);
    var data={'graphTool': graphTool, 'bopIds': bopIds, 'graphID': graphId, 'csrfmiddlewaretoken': csrf_token};
    var args={type:"POST", url:"/bodb/bopDiagram/", data: data, complete: doneBOPDiagram };
    document.getElementById(graphId+'Msg').innerHTML="<div align='center' style='color:red;'>Generating diagram...</div>";
    $.ajax(args);
    return false;
}

function doneBOPDiagram(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if (status=="success")
    {
        var date = new Date();
        document.getElementById(data.graphId).src='/media/'+data.bopDiagram;
        document.getElementById(data.graphId+'Map').innerHTML=data.bopMap;
        document.getElementById(data.graphId+'Msg').innerHTML="Click on a node to view BOP details.";
        document.getElementById(data.graphId+'Div').style.display='block';
        $('input:button').button();
        $('#'+data.graphId).zoomable();
    }
    else
        alert(txt);
}

function generateModelDiagram(graphTool, graphId, csrf_token)
{
    var modelIds=[];
    var modelCheckboxes=$('.selectedModelCheckbox');
    for(var i=0; i<modelCheckboxes.length; i++)
        modelIds.push(modelCheckboxes[i].value);
    var data={'graphTool': graphTool, 'modelIds': modelIds, 'graphID': graphId, 'csrfmiddlewaretoken': csrf_token};
    var args={type:"POST", url:"/bodb/modelDiagram/", data: data, complete: doneModelDiagram };
    document.getElementById(graphId+'Msg').innerHTML="<div align='center' style='color:red;'>Generating diagram...</div>";
    $.ajax(args);
    return false;
}

function doneModelDiagram(res, status)
{
    var txt = res.responseText;
    var data = eval('('+txt+')');
    if (status=="success")
    {
        var date = new Date();
        document.getElementById(data.graphId).src='/media/'+data.modelDiagram;
        document.getElementById(data.graphId+'Map').innerHTML=data.modelMap;
        document.getElementById(data.graphId+'Msg').innerHTML="Click on a node to view Model or SED details.";
        document.getElementById(data.graphId+'Div').style.display='block';
        $('input:button').button();
        $('#'+data.graphId).zoomable();
    }
    else
        alert(txt);
}