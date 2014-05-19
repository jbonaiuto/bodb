function processModelResults(data)
{
    if(data['models'].length>0)
    {
        $('[name=model_section]').each(function(index, element){
            $( this ).attr('style','display:block');
        });
        $('[name=model_list]').each(function(index, element){
            $( this ).attr('style','display:block');
        });
        $('[name=numModelResults]').each(function(index, element){
            $( this ).html(data['models'].length);
        });
    }
    else
    {
        $('[name=model_section]').each(function(index, element){
            $( this ).attr('style','display:none');
        });
        $('[name=model_list]').each(function(index, element){
            $( this ).attr('style','display:none');
        });
    }
    $('[name=models]').each(function(index, element){
        $( this ).empty();
        for(var i=0; i<data['models'].length; i++)
        {
            var count = $( this ).children().length;
            var tmplMarkup = $('#model-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['models'][i][3]['id'], title: data['models'][i][3]['title'],
                    brief_description: data['models'][i][3]['brief_description'], is_favorite: data['models'][i][1],
                    selected: data['models'][i][0], title_str: data['models'][i][3]['title_str'],
                    draft: data['models'][i][3]['draft'], collator_id: data['models'][i][3]['collator_id'],
                    collator: data['models'][i][3]['collator'], subscribed_to_user: data['models'][i][2]});
            $( this ).append(compiledTmpl);
        }
    });
    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processBOPResults(data)
{
    // BOP results
    if(data['bops'].length>0)
    {
        $('[name=bop_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=bop_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numBOPResults]').each(function(index, element){
            $(this).html(data['bops'].length)
        });
    }
    else
    {
        $('[name=bop_section]').each(function(index, element){
            $( this).attr('style','display:none');
        });
        $('[name=bop_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=bops]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['bops'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#bop-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['bops'][i][3]['id'], title: data['bops'][i][3]['title'],
                    brief_description: data['bops'][i][3]['brief_description'], is_favorite: data['bops'][i][1],
                    selected: data['bops'][i][0], title_str: data['bops'][i][3]['title_str'],
                    draft: data['bops'][i][3]['draft'], collator_id: data['bops'][i][3]['collator_id'],
                    collator: data['bops'][i][3]['collator'], subscribed_to_user: data['bops'][i][2]});
            $(this).append(compiledTmpl);
        }
    });
    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processSEDResults(data)
{
    // Generic SED results
    if(data['generic_seds'].length>0)
    {
        $('[name=sed_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=generic_sed_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numGenericSEDResults]').each(function(index, element){
            $(this).html(data['generic_seds'].length)
        });
    }
    else
    {
        $('[name=generic_sed_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=generic_seds]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['generic_seds'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#generic_sed-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['generic_seds'][i][3]['id'], title: data['generic_seds'][i][3]['title'],
                    type: data['generic_seds'][i][3]['type'],
                    brief_description: data['generic_seds'][i][3]['brief_description'],
                    is_favorite: data['generic_seds'][i][1], selected: data['generic_seds'][i][0],
                    title_str: data['generic_seds'][i][3]['title_str'], draft: data['generic_seds'][i][3]['draft'],
                    collator_id: data['generic_seds'][i][3]['collator_id'],
                    collator: data['generic_seds'][i][3]['collator'],
                    subscribed_to_user: data['generic_seds'][i][2]});
            $(this).append(compiledTmpl);
        }
    });

    // ERP SED results
    if(data['erp_seds'].length>0)
    {
        $('[name=sed_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=erp_sed_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numERPSEDResults]').each(function(index, element){
            $(this).html(data['erp_seds'].length)
        });
    }
    else
    {
        $('[name=erp_sed_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=erp_seds]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        for(var i=0; i<data['erp_seds'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#erp_sed_'+groupName+'-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['erp_seds'][i][3]['id'], title: data['erp_seds'][i][3]['title'],
                    type: data['erp_seds'][i][3]['type'],
                    brief_description: data['erp_seds'][i][3]['brief_description'],
                    components: data['erp_seds'][i][4], is_favorite: data['erp_seds'][i][1],
                    selected: data['erp_seds'][i][0], title_str: data['erp_seds'][i][3]['title_str'],
                    draft: data['erp_seds'][i][3]['draft'], collator_id: data['erp_seds'][i][3]['collator_id'],
                    collator: data['erp_seds'][i][3]['collator'], subscribed_to_user: data['erp_seds'][i][2]});
            $(this).append(compiledTmpl);
        }
        eval('load'+groupName+'Popups();');
    });

    // Connectivity SED results
    if(data['connectivity_seds'].length>0)
    {
        $('[name=sed_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=connectivity_sed_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numConnectivitySEDResults]').each(function(index, element){
            $(this).html(data['connectivity_seds'].length)
        });
    }
    else
    {
        $('[name=connectivity_sed_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=connectivity_seds]').each(function(index, element){
        var groupName=$(this).find('#groupName').attr('value');
        $(this).empty();
        $(this).html('<input type="hidden" id="groupName" value="'+groupName+'"/>');
        for(var i=0; i<data['connectivity_seds'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#connectivity_sed_'+groupName+'-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['connectivity_seds'][i][3]['id'],
                    title: data['connectivity_seds'][i][3]['title'], type: data['connectivity_seds'][i][3]['type'],
                    brief_description: data['connectivity_seds'][i][3]['brief_description'],
                    url_str: data['connectivity_seds'][i][3]['url_str'], is_favorite: data['connectivity_seds'][i][1],
                    selected: data['connectivity_seds'][i][0], title_str: data['connectivity_seds'][i][3]['title_str'],
                    draft: data['connectivity_seds'][i][3]['draft'],
                    collator_id: data['connectivity_seds'][i][3]['collator_id'],
                    collator: data['connectivity_seds'][i][3]['collator'],
                    subscribed_to_user: data['connectivity_seds'][i][2]});
            $(this).append(compiledTmpl);
        }
    });

    // Imaging SED results
    if(data['imaging_seds'].length>0)
    {
        $('[name=sed_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=imaging_sed_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numImagingSEDResults]').each(function(index, element){
            $(this).html(data['imaging_seds'].length)
        });
    }
    else
    {
        $('[name=imaging_sed_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=imaging_seds]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['imaging_seds'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#imaging_sed-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['imaging_seds'][i][3]['id'], title: data['imaging_seds'][i][3]['title'],
                    type: data['imaging_seds'][i][3]['type'], url_str: data['imaging_seds'][i][3]['url_str'],
                    brief_description: data['imaging_seds'][i][3]['brief_description'],
                    coords: data['imaging_seds'][i][4], is_favorite: data['imaging_seds'][i][1],
                    selected: data['imaging_seds'][i][0], title_str: data['imaging_seds'][i][3]['title_str'],
                    draft: data['imaging_seds'][i][3]['draft'], collator_id: data['imaging_seds'][i][3]['collator_id'],
                    collator: data['imaging_seds'][i][3]['collator'], subscribed_to_user: data['imaging_seds'][i][2]});
            $(this).append(compiledTmpl);
        }
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processSSRResults(data)
{
    // SSR results
    if(data['ssrs'].length>0)
    {
        $('[name=ssr_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=ssr_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numSSRResults]').each(function(index, element){
            $(this).html(data['ssrs'].length)
        });
    }
    else
    {
        $('[name=ssr_section]').each(function(index, element){
            $( this).attr('style','display:none');
        });
        $('[name=ssr_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=ssrs]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['ssrs'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#ssr-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['ssrs'][i][3]['id'], title: data['ssrs'][i][3]['title'],
                    brief_description: data['ssrs'][i][3]['brief_description'], is_favorite: data['ssrs'][i][1],
                    selected: data['ssrs'][i][0], title_str: data['ssrs'][i][3]['title_str'],
                    draft: data['ssrs'][i][3]['draft'], collator_id: data['ssrs'][i][3]['collator_id'],
                    collator: data['ssrs'][i][3]['collator'], subscribed_to_user: data['ssrs'][i][2]});
            $(this).append(compiledTmpl);
        }
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processLiteratureResults(data)
{
    // Literature results
    if(data['literatures'].length>0)
    {
        $('[name=literature_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=literature_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numLiteratureResults]').each(function(index, element){
            $(this).html(data['literatures'].length)
        });
    }
    else
    {
        $('[name=literature_section]').each(function(index, element){
            $( this).attr('style','display:none');
        });
        $('[name=literature_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=literatures]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['literatures'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#literature-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['literatures'][i][3]['id'], authors: data['literatures'][i][3]['authors'],
                    year: data['literatures'][i][3]['year'], is_favorite: data['literatures'][i][1],
                    selected: data['literatures'][i][0], title: data['literatures'][i][3]['title'],
                    string: data['literatures'][i][3]['string'], collator_id: data['literatures'][i][3]['collator_id'],
                    collator: data['literatures'][i][3]['collator'], subscribed_to_user: data['literatures'][i][2]});
            $(this).append(compiledTmpl);
        }
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processBrainRegionResults(data)
{
    // Brain region results
    if(data['brain_regions'].length>0)
    {
        $('[name=brain_region_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=brain_region_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numBrainRegionResults]').each(function(index, element){
            $(this).html(data['brain_regions'].length)
        });
    }
    else
    {
        $('[name=brain_region_section]').each(function(index, element){
            $( this).attr('style','display:none');
        });
        $('[name=brain_region_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=brain_regions]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['brain_regions'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#brain_region-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['brain_regions'][i][2]['id'], name: data['brain_regions'][i][2]['name'],
                    abbreviation: data['brain_regions'][i][2]['abbreviation'],
                    is_favorite: data['brain_regions'][i][1], selected: data['brain_regions'][i][0],
                    type: data['brain_regions'][i][2]['type'],
                    parent_region: data['brain_regions'][i][2]['parent_region'],
                    nomenclature: data['brain_regions'][i][2]['nomenclature'],
                    species: data['brain_regions'][i][2]['species']});
            $(this).append(compiledTmpl);
        }
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}

function processUserResults(data)
{
    // User results
    if(data['users'].length>0)
    {
        $('[name=user_section]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=user_list]').each(function(index, element){
            $( this).attr('style','display:block');
        });
        $('[name=numUserResults]').each(function(index, element){
            $(this).html(data['users'].length)
        });
    }
    else
    {
        $('[name=user_section]').each(function(index, element){
            $( this).attr('style','display:none');
        });
        $('[name=user_list]').each(function(index, element){
            $( this).attr('style','display:none');
        });
    }
    $('[name=users]').each(function(index, element){
        $(this).empty();
        for(var i=0; i<data['users'].length; i++)
        {
            var count = $(this).children().length;
            var tmplMarkup = $('#user-template').html();
            var compiledTmpl = _.template(tmplMarkup,
                { idx : count+1, id: data['users'][i][1]['id'], username: data['users'][i][1]['username'],
                    first_name: data['users'][i][1]['first_name'], last_name: data['users'][i][1]['last_name'],
                    email: data['users'][i][1]['email'], subscribed_to_user: data['users'][i][0]});
            $(this).append(compiledTmpl);
        }
    });

    document.getElementById('searchingMsg').style.display = 'none';
    document.getElementById('searchingOver').style.display = 'none';
}