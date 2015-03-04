function processModelResults(data)
{

    $('[name=model_section]').each(function(index, element){
        $( this ).attr('style','display:block');
    });
    $('[name=model_list]').each(function(index, element){
        if(data['models'].length>0)
            $( this ).attr('style','display:block');
        else
            $( this ).attr('style','display:none');
    });
    $('[name=numModelResults]').each(function(index, element){
        $( this ).html(data['models_count']);
    });
    $('[name=modelResultStartIndex]').each(function(index, element){
        $(this).html(data['models_start_index']);
    });
    $('[name=modelResultEndIndex]').each(function(index, element){
        $(this).html(data['models_end_index']);
    });
    $('#model_current_page').html(data['models_page_number']);
    $('#model_total_pages').html(data['models_num_pages']);
    if(data['models_has_previous'])
    {
        $('#models_previous').attr('style','display:inline');
        $('#models_previous').html('<a href="" onclick="modelJumpPage('+data['models_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#models_previous').attr('style','display:none');
    if(data['models_has_next'])
    {
        $('#models_next').attr('style','display:inline');
        $('#models_next').html('<a href="" onclick="modelJumpPage('+data['models_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#models_next').attr('style','display:none');

    models=[];
    for(var i=0; i<data['models'].length; i++)
    {
        models.push({
            id: data['models'][i][3]['id'],
            title: data['models'][i][3]['title'],
            brief_description: data['models'][i][3]['brief_description'],
            is_favorite: data['models'][i][1],
            selected: data['models'][i][0],
            title_str: data['models'][i][3]['title_str'],
            draft: data['models'][i][3]['draft'],
            collator_id: data['models'][i][3]['collator_id'],
            collator: data['models'][i][3]['collator'],
            subscribed_to_user: data['models'][i][2]
        });
    }

    $('[name=models]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        eval(groupName+"nodes=[];");
        eval(groupName+"edges=[];");
        var tmplMarkup = $('#model-template').html();
        for(var i=0; i<models.length; i++)
        {
            models[i]['idx'] = $( this ).children().length+data['models_start_index']-1;
            var compiledTmpl = _.template(tmplMarkup, models[i]);
            $( this ).append(compiledTmpl);
            eval(groupName+"nodes.push({id: "+data['models'][i][3]['id']+", label:'"+addslashes(data['models'][i][3]['title'])+"', shape:'box', title:'"+addslashes(data['models'][i][3]['brief_description'])+"'});");
        }
        for(var model_id in data['model_seds'])
        {
            for(var i=0; i<data['model_seds'][model_id].length; i++)
            {
                var found=false;
                eval('for(var j=0; j<'+groupName+'nodes.length; j++){ if('+groupName+'nodes[j]["id"]=='+data['model_seds'][model_id][i]['sed_id']+'){ found=true; break; }}');
                if(!found)
                {
                    eval(groupName+"nodes.push({id: "+data['model_seds'][model_id][i]['sed_id']+", label:'"+addslashes(data['model_seds'][model_id][i]['title'])+"', title:'"+addslashes(data['model_seds'][model_id][i]['sed_desc'])+"'});");
                }
            }
        }
        for(var model_id in data['model_seds'])
        {
            for(var i=0; i<data['model_seds'][model_id].length; i++)
            {
                eval(groupName+"edges.push({from: "+data['model_seds'][model_id][i]['sed_id']+", to:"+model_id+", label: '"+addslashes(data['model_seds'][model_id][i]['relationship'])+"', title: '"+addslashes(data['model_seds'][model_id][i]['relevance_narrative'])+"'});");
            }
        }
    });
    $('[name=model_sort_dir]').each(function(index, element){
        if(this.id=='id_model_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=model_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_model_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_model_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_model_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_model_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_model_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });
    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processBOPResults(data)
{
    // BOP results
    $('[name=bop_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=bop_list]').each(function(index, element){
        if(data['bops'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numBOPResults]').each(function(index, element){
        $(this).html(data['bops_count']);
    });
    $('[name=bopResultStartIndex]').each(function(index, element){
        $(this).html(data['bops_start_index']);
    });
    $('[name=bopResultEndIndex]').each(function(index, element){
        $(this).html(data['bops_end_index']);
    });
    $('#bop_current_page').html(data['bops_page_number']);
    $('#bop_total_pages').html(data['bops_num_pages']);
    if(data['bops_has_previous'])
    {
        $('#bops_previous').attr('style','display:inline');
        $('#bops_previous').html('<a href="" onclick="bopJumpPage('+data['bops_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#bops_previous').attr('style','display:none');
    if(data['bops_has_next'])
    {
        $('#bops_next').attr('style','display:inline');
        $('#bops_next').html('<a href="" onclick="bopJumpPage('+data['bops_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#bops_next').attr('style','display:none');
    bops=[];
    for(var i=0; i<data['bops'].length; i++)
    {
        bops.push({
            id: data['bops'][i][3]['id'],
            title: data['bops'][i][3]['title'],
            brief_description: data['bops'][i][3]['brief_description'],
            is_favorite: data['bops'][i][1],
            selected: data['bops'][i][0],
            title_str: data['bops'][i][3]['title_str'],
            draft: data['bops'][i][3]['draft'],
            collator_id: data['bops'][i][3]['collator_id'],
            collator: data['bops'][i][3]['collator'],
            subscribed_to_user: data['bops'][i][2]
        });
    }
    $('[name=bops]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        eval(groupName+"nodes=[];");
        eval(groupName+"edges=[];");
        var tmplMarkup = $('#bop-template').html();
        for(var i=0; i<bops.length; i++)
        {
            bops[i]['idx']= $(this).children().length+data['bops_start_index']-1;
            var compiledTmpl = _.template(tmplMarkup, bops[i]);
            $(this).append(compiledTmpl);
            eval(groupName+"nodes.push({id: "+data['bops'][i][3]['id']+", label:'"+addslashes(data['bops'][i][3]['title'])+"', title:'"+addslashes(data['bops'][i][3]['brief_description'])+"'});");
        }
    });
    $('[name=bop_sort_dir]').each(function(index, element){
        if(this.id=='id_bop_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=bop_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_bop_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_bop_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_bop_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_bop_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_bop_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });
    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processSEDResults(data)
{
    // Generic SED results
    $('[name=sed_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=generic_sed_list]').each(function(index, element){
        if(data['generic_seds'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numGenericSEDResults]').each(function(index, element){
        $(this).html(data['generic_seds'].length)
    });
    generic_seds=[];
    for(var i=0; i<data['generic_seds'].length; i++)
    {
        generic_seds.push({
            id: data['generic_seds'][i][3]['id'],
            title: data['generic_seds'][i][3]['title'],
            sed_type: data['generic_seds'][i][3]['type'],
            brief_description: data['generic_seds'][i][3]['brief_description'],
            is_favorite: data['generic_seds'][i][1],
            selected: data['generic_seds'][i][0],
            title_str: data['generic_seds'][i][3]['title_str'],
            draft: data['generic_seds'][i][3]['draft'],
            collator_id: data['generic_seds'][i][3]['collator_id'],
            collator: data['generic_seds'][i][3]['collator'],
            subscribed_to_user: data['generic_seds'][i][2]
        });
    }
    $('[name=generic_seds]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#generic_sed-template').html();
        for(var i=0; i<generic_seds.length; i++)
        {
            generic_seds[i]['idx']=$(this).children().length+1;
            var compiledTmpl = _.template(tmplMarkup, generic_seds[i]);
            $(this).append(compiledTmpl);
        }
    });
    $('[name=generic_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_generic_sed_sort_'+data.generic_order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=generic_sed_list]').each(function(index, element){
        if(data.generic_direction=='ascending')
        {
            $(this).find('#id_generic_sed_sort_'+data.generic_order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_generic_sed_sort_'+data.generic_order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_generic_sed_sort_'+data.generic_order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_generic_sed_sort_'+data.generic_order_by).attr('value','ascending');
        }
        $(this).find('#id_generic_sed_sort_'+data.generic_order_by+'_dir').attr('style','display: inline');;
    });


    // ERP SED results
    $('[name=erp_sed_list]').each(function(index, element){
        if(data['erp_seds'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numERPSEDResults]').each(function(index, element){
        $(this).html(data['erp_seds'].length)
    });
    erp_seds=[];
    for(var i=0; i<data['erp_seds'].length; i++)
    {
        erp_seds.push({
            id: data['erp_seds'][i][3]['id'],
            title: data['erp_seds'][i][3]['title'],
            sed_type: data['erp_seds'][i][3]['type'],
            brief_description: data['erp_seds'][i][3]['brief_description'],
            components: data['erp_seds'][i][4],
            is_favorite: data['erp_seds'][i][1],
            selected: data['erp_seds'][i][0],
            title_str: data['erp_seds'][i][3]['title_str'],
            draft: data['erp_seds'][i][3]['draft'],
            collator_id: data['erp_seds'][i][3]['collator_id'],
            collator: data['erp_seds'][i][3]['collator'],
            subscribed_to_user: data['erp_seds'][i][2]
        });
    }
    $('[name=erp_seds]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        var tmplMarkup = $('#erp_sed_'+groupName+'-template').html();
        for(var i=0; i<erp_seds.length; i++)
        {
            erp_seds[i]['idx']=$(this).children().length;
            var compiledTmpl = _.template(tmplMarkup, erp_seds[i]);
            $(this).append(compiledTmpl);
        }
        eval('load'+groupName+'Popups();');
    });

    $('[name=erp_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_erp_sed_sort_'+data.erp_order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=erp_sed_list]').each(function(index, element){
        if(data.erp_direction=='ascending')
        {
            $(this).find('#id_erp_sed_sort_'+data.erp_order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_erp_sed_sort_'+data.erp_order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_erp_sed_sort_'+data.erp_order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_erp_sed_sort_'+data.erp_order_by).attr('value','ascending');
        }
        $(this).find('#id_erp_sed_sort_'+data.erp_order_by+'_dir').attr('style','display: inline');;
    });

    // Connectivity SED results
    $('[name=connectivity_sed_list]').each(function(index, element){
        if(data['connectivity_seds'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numConnectivitySEDResults]').each(function(index, element){
        $(this).html(data['connectivity_seds'].length)
    });
    connectivity_seds=[];
    for(var i=0; i<data['connectivity_seds'].length; i++)
    {
        connectivity_seds.push({
            id: data['connectivity_seds'][i][3]['id'],
            title: data['connectivity_seds'][i][3]['title'],
            sed_type: data['connectivity_seds'][i][3]['type'],
            brief_description: data['connectivity_seds'][i][3]['brief_description'],
            url_str: data['connectivity_seds'][i][3]['url_str'],
            is_favorite: data['connectivity_seds'][i][1],
            selected: data['connectivity_seds'][i][0],
            title_str: data['connectivity_seds'][i][3]['title_str'],
            draft: data['connectivity_seds'][i][3]['draft'],
            collator_id: data['connectivity_seds'][i][3]['collator_id'],
            collator: data['connectivity_seds'][i][3]['collator'],
            subscribed_to_user: data['connectivity_seds'][i][2]
        });
    }
    $('[name=connectivity_seds]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        eval(groupName+"nodes=[];");
        eval(groupName+"edges=[];");
        var tmplMarkup = $('#connectivity_sed_'+groupName+'-template').html();
        for(var i=0; i<data['connectivity_seds'].length; i++)
        {
            connectivity_seds[i]['idx']=$(this).children().length;
            var compiledTmpl = _.template(tmplMarkup, connectivity_seds[i]);
            $(this).append(compiledTmpl);
            eval(groupName+"edges.push({from: "+addslashes(data['connectivity_seds'][i][3]['source_region'])+", to:"+addslashes(data['connectivity_seds'][i][3]['target_region'])+", id:"+data['connectivity_seds'][i][3]['id']+", title:'"+addslashes(data['connectivity_seds'][i][3]['brief_description'])+"'});");
        }
        for(var region_id in data['connectivity_sed_regions'])
        {
            var title='Name: '+addslashes(data['connectivity_sed_regions'][region_id]['name'])+'<br>Abbreviation: '+addslashes(data['connectivity_sed_regions'][region_id]['abbreviation'])+'<br>Nomenclature: '+addslashes(data['connectivity_sed_regions'][region_id]['nomenclature']);
            eval(groupName+"nodes.push({id:"+region_id+", label:'"+addslashes(data['connectivity_sed_regions'][region_id]['str'])+"', title:'"+title+"'});");
        }
    });

    $('[name=connectivity_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_connectivity_sed_sort_'+data.connectivity_order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=connectivity_sed_list]').each(function(index, element){
        if(data.connectivity_direction=='ascending')
        {
            $(this).find('#id_connectivity_sed_sort_'+data.connectivity_order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_connectivity_sed_sort_'+data.connectivity_order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_connectivity_sed_sort_'+data.connectivity_order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_connectivity_sed_sort_'+data.connectivity_order_by).attr('value','ascending');
        }
        $(this).find('#id_connectivity_sed_sort_'+data.connectivity_order_by+'_dir').attr('style','display: inline');;
    });

    // Imaging SED results
    $('[name=imaging_sed_list]').each(function(index, element){
        if(data['imaging_seds'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numImagingSEDResults]').each(function(index, element){
        $(this).html(data['imaging_seds'].length)
    });
    imaging_seds=[];
    for(var i=0; i<data['imaging_seds'].length; i++)
    {
        imaging_seds.push({
            id: data['imaging_seds'][i][3]['id'],
            title: data['imaging_seds'][i][3]['title'],
            sed_type: data['imaging_seds'][i][3]['type'],
            url_str: data['imaging_seds'][i][3]['url_str'],
            brief_description: data['imaging_seds'][i][3]['brief_description'],
            coords: data['imaging_seds'][i][4],
            is_favorite: data['imaging_seds'][i][1],
            selected: data['imaging_seds'][i][0],
            title_str: data['imaging_seds'][i][3]['title_str'],
            draft: data['imaging_seds'][i][3]['draft'],
            collator_id: data['imaging_seds'][i][3]['collator_id'],
            collator: data['imaging_seds'][i][3]['collator'],
            subscribed_to_user: data['imaging_seds'][i][2]
        });
    }
    $('[name=imaging_seds]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#imaging_sed-template').html();
        for(var i=0; i<imaging_seds.length; i++)
        {
            imaging_seds[i]['idx']=$(this).children().length+1;
            var compiledTmpl = _.template(tmplMarkup, imaging_seds[i]);
            $(this).append(compiledTmpl);
        }
    });

    $('[name=imaging_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_imaging_sed_sort_'+data.imaging_order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=imaging_sed_list]').each(function(index, element){
        if(data.imaging_direction=='ascending')
        {
            $(this).find('#id_imaging_sed_sort_'+data.imaging_order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_imaging_sed_sort_'+data.imaging_order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_imaging_sed_sort_'+data.imaging_order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_imaging_sed_sort_'+data.imaging_order_by).attr('value','ascending');
        }
        $(this).find('#id_imaging_sed_sort_'+data.imaging_order_by+'_dir').attr('style','display: inline');;
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processSSRResults(data)
{
    // SSR results
    $('[name=ssr_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=ssr_list]').each(function(index, element){
        if(data['ssrs'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numSSRResults]').each(function(index, element){
        $(this).html(data['ssrs_count'])
    });
    $('[name=ssrResultStartIndex]').each(function(index, element){
        $(this).html(data['ssrs_start_index']);
    });
    $('[name=ssrResultEndIndex]').each(function(index, element){
        $(this).html(data['ssrs_end_index']);
    });
    $('#ssr_current_page').html(data['ssrs_page_number']);
    $('#ssr_total_pages').html(data['ssrs_num_pages']);
    if(data['ssrs_has_previous'])
    {
        $('#ssrs_previous').attr('style','display:inline');
        $('#ssrs_previous').html('<a href="" onclick="ssrJumpPage('+data['ssrs_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#ssrs_previous').attr('style','display:none');
    if(data['ssrs_has_next'])
    {
        $('#ssrs_next').attr('style','display:inline');
        $('#ssrs_next').html('<a href="" onclick="ssrJumpPage('+data['ssrs_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#ssrs_next').attr('style','display:none');
    ssrs=[];
    for(var i=0; i<data['ssrs'].length; i++)
    {
        ssrs.push({
            id: data['ssrs'][i][3]['id'],
            title: data['ssrs'][i][3]['title'],
            type: data['ssrs'][i][3]['type'],
            brief_description: data['ssrs'][i][3]['brief_description'],
            is_favorite: data['ssrs'][i][1],
            selected: data['ssrs'][i][0],
            title_str: data['ssrs'][i][3]['title_str'],
            draft: data['ssrs'][i][3]['draft'],
            collator_id: data['ssrs'][i][3]['collator_id'],
            collator: data['ssrs'][i][3]['collator'],
            subscribed_to_user: data['ssrs'][i][2]
        });
    }
    $('[name=ssrs]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#ssr-template').html();
        for(var i=0; i<data['ssrs'].length; i++)
        {
            ssrs[i]['idx']=$(this).children().length+data['ssrs_start_index'];
            var compiledTmpl = _.template(tmplMarkup, ssrs[i]);
            $(this).append(compiledTmpl);
        }
    });
    $('[name=ssr_sort_dir]').each(function(index, element){
        if(this.id=='id_ssr_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=ssr_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_ssr_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_ssr_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_ssr_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_ssr_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_ssr_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });
    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processLiteratureResults(data)
{
    // Literature results
    $('[name=literature_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=literature_list]').each(function(index, element){
        if(data['literatures'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numLiteratureResults]').each(function(index, element){
        $(this).html(data['literatures_count'])
    });
    $('[name=literatureResultStartIndex]').each(function(index, element){
        $(this).html(data['literatures_start_index']);
    });
    $('[name=literatureResultEndIndex]').each(function(index, element){
        $(this).html(data['literatures_end_index']);
    });
    $('#literature_current_page').html(data['literatures_page_number']);
    $('#literature_total_pages').html(data['literatures_num_pages']);
    if(data['literatures_has_previous'])
    {
        $('#literatures_previous').attr('style','display:inline');
        $('#literatures_previous').html('<a href="" onclick="literatureJumpPage('+data['literatures_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#literatures_previous').attr('style','display:none');
    if(data['literatures_has_next'])
    {
        $('#literatures_next').attr('style','display:inline');
        $('#literatures_next').html('<a href="" onclick="literatureJumpPage('+data['literatures_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#literatures_next').attr('style','display:none');
    lits=[];
    for(var i=0; i<data['literatures'].length; i++)
    {
        lits.push({
            id: data['literatures'][i][3]['id'],
            authors: data['literatures'][i][3]['authors'],
            year: data['literatures'][i][3]['year'],
            is_favorite: data['literatures'][i][1],
            selected: data['literatures'][i][0],
            title: data['literatures'][i][3]['title'],
            string: data['literatures'][i][3]['string'],
            collator_id: data['literatures'][i][3]['collator_id'],
            collator: data['literatures'][i][3]['collator'],
            subscribed_to_user: data['literatures'][i][2],
            url_str: data['literatures'][i][3]['url_str']
        });
    }
    $('[name=literatures]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#literature-template').html();
        for(var i=0; i<data['literatures'].length; i++)
        {
            lits[i]['idx']=$(this).children().length+data['literatures_start_index'];
            var compiledTmpl = _.template(tmplMarkup, lits[i]);
            $(this).append(compiledTmpl);
        }
    });
    $('[name=literature_sort_dir]').each(function(index, element){
        if(this.id=='id_literature_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=literature_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_literature_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_literature_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_literature_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_literature_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_literature_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processBrainRegionResults(data)
{
    // Brain region results
    $('[name=brain_region_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=brain_region_list]').each(function(index, element){
        if(data['brain_regions'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numBrainRegionResults]').each(function(index, element){
        $(this).html(data['brain_regions_count'])
    });
    $('[name=brainRegionResultStartIndex]').each(function(index, element){
        $(this).html(data['brain_regions_start_index']);
    });
    $('[name=brainRegionResultEndIndex]').each(function(index, element){
        $(this).html(data['brain_regions_end_index']);
    });
    $('#brain_region_current_page').html(data['brain_regions_page_number']);
    $('#brain_region_total_pages').html(data['brain_regions_num_pages']);
    if(data['brain_regions_has_previous'])
    {
        $('#brain_regions_previous').attr('style','display:inline');
        $('#brain_regions_previous').html('<a href="" onclick="brainRegionJumpPage('+data['brain_regions_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#brain_regions_previous').attr('style','display:none');
    if(data['brain_regions_has_next'])
    {
        $('#brain_regions_next').attr('style','display:inline');
        $('#brain_regions_next').html('<a href="" onclick="brainRegionJumpPage('+data['brain_regions_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#brain_regions_next').attr('style','display:none');
    regions=[];
    for(var i=0; i<data['brain_regions'].length; i++)
    {
        regions.push({
            id: data['brain_regions'][i][2]['id'],
            name: data['brain_regions'][i][2]['name'],
            abbreviation: data['brain_regions'][i][2]['abbreviation'],
            is_favorite: data['brain_regions'][i][1],
            selected: data['brain_regions'][i][0],
            type: data['brain_regions'][i][2]['type'],
            parent_region: data['brain_regions'][i][2]['parent_region'],
            nomenclature: data['brain_regions'][i][2]['nomenclature'],
            species: data['brain_regions'][i][2]['species']
        });
    }
    $('[name=brain_regions]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#brain_region-template').html();
        for(var i=0; i<data['brain_regions'].length; i++)
        {
            regions[i]['idx']=$(this).children().length+data['brain_regions_start_index'];
            var compiledTmpl = _.template(tmplMarkup, regions[i]);
            $(this).append(compiledTmpl);
        }
    });
    $('[name=brain_region_sort_dir]').each(function(index, element){
        if(this.id=='id_brain_region_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=brain_region_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_brain_region_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_brain_region_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_brain_region_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_brain_region_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_brain_region_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processUserResults(data)
{
    // User results
    $('[name=user_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=user_list]').each(function(index, element){
        if(data['users'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numUserResults]').each(function(index, element){
        $(this).html(data['users_count'])
    });
    $('[name=userResultStartIndex]').each(function(index, element){
        $(this).html(data['users_start_index']);
    });
    $('[name=userResultEndIndex]').each(function(index, element){
        $(this).html(data['users_end_index']);
    });
    $('#user_current_page').html(data['users_page_number']);
    $('#user_total_pages').html(data['users_num_pages']);
    if(data['users_has_previous'])
    {
        $('#users_previous').attr('style','display:inline');
        $('#users_previous').html('<a href="" onclick="userJumpPage('+data['users_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#users_previous').attr('style','display:none');
    if(data['users_has_next'])
    {
        $('#users_next').attr('style','display:inline');
        $('#users_next').html('<a href="" onclick="userJumpPage('+data['users_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#users_next').attr('style','display:none');
    users=[];
    for(var i=0; i<data['users'].length; i++)
    {
        users.push({
            id: data['users'][i][1]['id'],
            username: data['users'][i][1]['username'],
            first_name: data['users'][i][1]['first_name'],
            last_name: data['users'][i][1]['last_name'],
            email: data['users'][i][1]['email'],
            subscribed_to_user: data['users'][i][0]
        });
    }
    $('[name=users]').each(function(index, element){
        $(this).empty();
        var tmplMarkup = $('#user-template').html();
        for(var i=0; i<data['users'].length; i++)
        {
            users[i]['idx']=$(this).children().length+data['users_start_index'];
            var compiledTmpl = _.template(tmplMarkup, users[i]);
            $(this).append(compiledTmpl);
        }
    });

    $('[name=user_sort_dir]').each(function(index, element){
        if(this.id=='id_user_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=user_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_user_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_user_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_user_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_user_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_user_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processWorkspaceResults(data)
{
    // Workspace results
    $('[name=workspace_section]').each(function(index, element){
        $( this).attr('style','display:block');
    });
    $('[name=workspace_list]').each(function(index, element){
        if(data['workspaces'].length>0)
            $( this).attr('style','display:block');
        else
            $( this).attr('style','display:none');
    });
    $('[name=numWorkspaceResults]').each(function(index, element){
        $(this).html(data['workspaces_count'])
    });
    $('[name=workspaceResultStartIndex]').each(function(index, element){
        $(this).html(data['workspaces_start_index']);
    });
    $('[name=workspaceResultEndIndex]').each(function(index, element){
        $(this).html(data['workspaces_end_index']);
    });
    $('#workspace_current_page').html(data['workspaces_page_number']);
    $('#workspace_total_pages').html(data['workspaces_num_pages']);
    if(data['workspaces_has_previous'])
    {
        $('#workspaces_previous').attr('style','display:inline');
        $('#workspaces_previous').html('<a href="" onclick="workspaceJumpPage('+data['workspaces_previous_page_number']+'); return false;">previous</a>');
    }
    else
        $('#workspaces_previous').attr('style','display:none');
    if(data['workspaces_has_next'])
    {
        $('#workspaces_next').attr('style','display:inline');
        $('#workspaces_next').html('<a href="" onclick="workspaceJumpPage('+data['workspaces_next_page_number']+'); return false;">next</a>');
    }
    else
        $('#workspaces_next').attr('style','display:none');
    workspaces=[];
    for(var i=0; i<data['workspaces'].length; i++)
    {
        workspaces.push({
            id: data['workspaces'][i][1]['id'],
            title: data['workspaces'][i][1]['title'],
            description: data['workspaces'][i][1]['description'],
            created_by: data['workspaces'][i][1]['created_by'],
            created_by_id: data['workspaces'][i][1]['created_by_id'],
            subscribed_to_user: data['workspaces'][i][0]
        });
    }
    $('[name=workspaces]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<workspaces.length; i++)
        {
            workspaces[i]['idx']=$(this).children().length+data['workspaces_start_index'];
            var tmplMarkup = $('#workspace-template').html();
            var compiledTmpl = _.template(tmplMarkup, workspaces[i]);
            $(this).append(compiledTmpl);
        }
    });

    $('[name=workspace_sort_dir]').each(function(index, element){
        if(this.id=='id_workspace_sort_'+data.order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=workspace_list]').each(function(index, element){
        if(data.direction=='ascending')
        {
            $(this).find('#id_workspace_sort_'+data.order_by+'_dir').attr('src',data.up_image);
            $(this).find('#id_workspace_sort_'+data.order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_workspace_sort_'+data.order_by+'_dir').attr('src',data.down_image);
            $(this).find('#id_workspace_sort_'+data.order_by).attr('value','ascending');
        }
        $(this).find('#id_workspace_sort_'+data.order_by+'_dir').attr('style','display: inline');
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}