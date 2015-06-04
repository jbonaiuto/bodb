function objectSort(property, direction){
    var sortOrder=-1;
    if(direction=='ascending')
        sortOrder=1;
    return function(a,b) {
        var result=(a[property] < b[property]) ?-1 : (a[property] > b[property]) ? 1 : 0;
        return result*sortOrder;
    }
}

function sortBrainRegions(order_by, direction, up_image, down_image)
{
    regions.sort(objectSort(order_by,direction));
    addBrainRegions();
    $('[name=brain_region_sort_dir]').each(function(index, element){
        if(this.id=='id_brain_region_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=brain_region_list]').each(function(index, element){
        var direction=$(this).find('#id_brain_region_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_brain_region_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_brain_region_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_brain_region_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_brain_region_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_brain_region_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortUsers(order_by, direction, up_image, down_image)
{
    users.sort(objectSort(order_by,direction));
    addUsers();
    $('[name=user_sort_dir]').each(function(index, element){
        if(this.id=='id_user_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=user_list]').each(function(index, element){
        var direction=$(this).find('#id_user_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_user_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_user_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_user_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_user_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_user_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortBOPs(order_by, direction, up_image, down_image)
{
    bops.sort(objectSort(order_by,direction));
    addBOPs();
    $('[name=bop_sort_dir]').each(function(index, element){
        if(this.id=='id_bop_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=bop_list]').each(function(index, element){
        var direction=$(this).find('#id_bop_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_bop_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_bop_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_bop_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_bop_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_bop_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortRelatedBOPs(order_by, direction, up_image, down_image)
{
    related_bops.sort(objectSort(order_by,direction));
    addRelatedBOPs();
    $('[name=related_bop_sort_dir]').each(function(index, element){
        if(this.id=='id_related_bop_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_related_bop_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_related_bop_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_related_bop_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_related_bop_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_related_bop_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_related_bop_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortRelatedBrainRegions(order_by, direction, up_image, down_image)
{
    related_regions.sort(objectSort(order_by,direction));
    addRelatedBrainRegions();
    $('[name=related_brain_region_sort_dir]').each(function(index, element){
        if(this.id=='id_related_brain_region_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_related_brain_region_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_related_brain_region_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_related_brain_region_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_related_brain_region_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_related_brain_region_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_related_brain_region_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortLiterature(order_by, direction, up_image, down_image)
{
    lits.sort(objectSort(order_by,direction));
    addLiterature();
    $('[name=literature_sort_dir]').each(function(index, element){
        if(this.id=='id_literature_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=literature_list]').each(function(index, element){
        var direction=$(this).find('#id_literature_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_literature_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_literature_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_literature_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_literature_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_literature_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortModels(order_by, direction, up_image, down_image)
{
    models.sort(objectSort(order_by,direction));
    addModels();
    $('[name=model_sort_dir]').each(function(index, element){
        if(this.id=='id_model_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=model_list]').each(function(index, element){
        var direction=$(this).find('#id_model_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_model_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_model_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_model_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_model_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_model_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortRelatedModels(order_by, direction, up_image, down_image)
{
    related_models.sort(objectSort(order_by,direction));
    addRelatedModels();
    $('[name=related_model_sort_dir]').each(function(index, element){
        if(this.id=='id_related_model_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_related_model_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_related_model_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_related_model_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_related_model_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_related_model_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_related_model_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortPredictions(order_by, direction, up_image, down_image)
{
    predictions.sort(objectSort(order_by,direction));
    addPredictions();
    $('[name=prediction_sort_dir]').each(function(index, element){
        if(this.id=='id_prediction_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_prediction_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_prediction_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_prediction_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_prediction_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_prediction_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_prediction_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortImagingSEDs(order_by, direction, up_image, down_image)
{
    imaging_seds.sort(objectSort(order_by,direction));
    addImagingSEDs();
    $('[name=imaging_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_imaging_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=imaging_sed_list]').each(function(index, element){
        var direction=$(this).find('#id_imaging_sed_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_imaging_sed_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_imaging_sed_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_imaging_sed_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_imaging_sed_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_imaging_sed_sort_'+order_by+'_dir').attr('style','display: inline');;
    });
    return false;
}

function sortConnectivitySEDs(order_by, direction, up_image, down_image)
{
    connectivity_seds.sort(objectSort(order_by,direction));
    addConnectivitySEDs();
    $('[name=connectivity_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_connectivity_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=connectivity_sed_list]').each(function(index, element){
        var direction=$(this).find('#id_connectivity_sed_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_connectivity_sed_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_connectivity_sed_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_connectivity_sed_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_connectivity_sed_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_connectivity_sed_sort_'+order_by+'_dir').attr('style','display: inline');;
    });
    return false;
}

function sortERPSEDs(order_by, direction, up_image, down_image)
{
    erp_seds.sort(objectSort(order_by,direction));
    addERPSEDs();
    $('[name=erp_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_erp_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=erp_sed_list]').each(function(index, element){
        var direction=$(this).find('#id_erp_sed_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_erp_sed_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_erp_sed_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_erp_sed_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_erp_sed_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_erp_sed_sort_'+order_by+'_dir').attr('style','display: inline');;
    });
    return false;
}

function sortGenericSEDs(order_by, direction, up_image, down_image)
{
    generic_seds.sort(objectSort(order_by,direction));
    addGenericSEDs();
    $('[name=generic_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_generic_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=generic_sed_list]').each(function(index, element){
        var direction=$(this).find('#id_generic_sed_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_generic_sed_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_generic_sed_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_generic_sed_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_generic_sed_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_generic_sed_sort_'+order_by+'_dir').attr('style','display: inline');;
    });
    return false;
}

function sortNeurophysiologySEDs(order_by, direction, up_image, down_image)
{
    neurophysiology_seds.sort(objectSort(order_by,direction));
    addNeurophysiologySEDs();
    $('[name=neurophysiology_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_neurophysiology_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=neurophysiology_sed_list]').each(function(index, element){
        var direction=$(this).find('#id_neurophysiology_sed_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_neurophysiology_sed_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_neurophysiology_sed_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_neurophysiology_sed_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_neurophysiology_sed_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_neurophysiology_sed_sort_'+order_by+'_dir').attr('style','display: inline');;
    });
    return false;
}

function setBuildingSEDSortControls(sed_type, order_by, direction, up_image, down_image)
{
    $('[name='+sed_type+'_build_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_'+sed_type+'_build_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_'+sed_type+'_build_sed_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_'+sed_type+'_build_sed_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_'+sed_type+'_build_sed_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_'+sed_type+'_build_sed_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_'+sed_type+'_build_sed_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_'+sed_type+'_build_sed_sort_'+order_by+'_dir').style.display='inline';
}

function sortBuildingSEDs(sed_type, building_seds, order_by, direction)
{
    building_seds.sort(objectSort(order_by,direction));
    addBuildingSEDs(sed_type,building_seds);
    setBuildingSEDSortControls(sed_type,order_by,direction);
    return false;
}

function setTestingSEDSortControls(sed_type, order_by, direction, up_image, down_image)
{
    $('[name='+sed_type+'_test_sed_sort_dir]').each(function(index, element){
        if(this.id=='id_'+sed_type+'_test_sed_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_'+sed_type+'_test_sed_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_'+sed_type+'_test_sed_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_'+sed_type+'_test_sed_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_'+sed_type+'_test_sed_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_'+sed_type+'_test_sed_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_'+sed_type+'_test_sed_sort_'+order_by+'_dir').style.display='inline';
}

function sortTestingSEDs(sed_type, testing_seds, order_by, direction)
{
    testing_seds.sort(objectSort(order_by,direction));
    addTestSEDs(sed_type,testing_seds);
    setTestingSEDSortControls(sed_type,order_by,direction);
    return false;
}

function sortSSRs(order_by, direction, up_image, down_image)
{
    ssrs.sort(objectSort(order_by,direction));
    addSSRs();
    $('[name=ssr_sort_dir]').each(function(index, element){
        if(this.id=='id_ssr_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=ssr_list]').each(function(index, element){
        var direction=$(this).find('#id_ssr_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_ssr_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_ssr_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_ssr_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_ssr_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_ssr_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}

function sortMembers(order_by, direction, up_image, down_image)
{
    members.sort(objectSort(order_by,direction));
    addMembers();
    $('[name=member_sort_dir]').each(function(index, element){
        if(this.id=='id_member_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_member_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_member_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_member_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_member_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_member_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_member_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortBookmarks(order_by, direction, up_image, down_image)
{
    bookmarks.sort(objectSort(order_by,direction));
    addBookmarks();
    $('[name=bookmark_sort_dir]').each(function(index, element){
        if(this.id=='id_bookmark_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    var direction=$('#id_bookmark_sort_'+order_by).attr('value');
    if(direction=='ascending')
    {
        $('#id_bookmark_sort_'+order_by+'_dir').attr('src',up_image);
        $('#id_bookmark_sort_'+order_by).attr('value','descending');
    }
    else
    {
        $('#id_bookmark_sort_'+order_by+'_dir').attr('src',down_image);
        $('#id_bookmark_sort_'+order_by).attr('value','ascending');
    }
    document.getElementById('id_bookmark_sort_'+order_by+'_dir').style.display='inline';
    return false;
}

function sortWorkspaces(order_by, direction, up_image, down_image)
{
    workspaces.sort(objectSort(order_by,direction));
    addWorkspaces();
    $('[name=workspace_sort_dir]').each(function(index, element){
        if(this.id=='id_workspace_sort_'+order_by+'_dir')
            this.style.display='inline';
        else
            this.style.display='none';
    });
    $('[name=workspace_list]').each(function(index, element){
        var direction=$(this).find('#id_workspace_sort_'+order_by).attr('value');
        if(direction=='ascending')
        {
            $(this).find('#id_workspace_sort_'+order_by+'_dir').attr('src',up_image);
            $(this).find('#id_workspace_sort_'+order_by).attr('value','descending');
        }
        else
        {
            $(this).find('#id_workspace_sort_'+order_by+'_dir').attr('src',down_image);
            $(this).find('#id_workspace_sort_'+order_by).attr('value','ascending');
        }
        $(this).find('#id_workspace_sort_'+order_by+'_dir').attr('style','display: inline');
    });
    return false;
}