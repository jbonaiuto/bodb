import json
import urllib
import urllib2

def test_new_cocomac():
    source_region='AIP'
    sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE BrainSite LIKE $region OR Acronym LIKE $region'
    result=perform_query(sql, {'region': '%'+source_region+'%'})
    brainsite_idx=result['fields'].index('BrainSite')
    origin_search_string=','.join([x[brainsite_idx] for x in result['data'].values()])

    searchDict={
        'axonOriginList':origin_search_string,
        'axonTerminalList': '',
        'includeLargeInjections': '0',
        'useAM': '1',
        'useSORT': '0',
        'output': 'temptable',
        'fibercourse': 'I?'
    }
    query_req = urllib2.Request('http://cocomac.g-node.org/cocomac2/services/axonal_projections.php', urllib.urlencode( searchDict ) )
    query_response = urllib2.urlopen(query_req)
    temp_table=query_response.read()

    sql='SELECT * FROM %s' % temp_table
    result=perform_query(sql,{})
    axon_origin_idx=result['fields'].index('axon_origin')
    axon_terminal_idx=result['fields'].index('axon_terminal')
    axon_origins=[x[axon_origin_idx] for x in result['data'].values()]
    axon_terminals=[x[axon_terminal_idx] for x in result['data'].values()]
    region_id_list=[]
    for axon_origin,axon_terminal in zip(axon_origins,axon_terminals):
        if not axon_origin in region_id_list:
            region_id_list.append(axon_origin)
        if not axon_terminal in region_id_list:
            region_id_list.append(axon_terminal)

    region_map={}
    remaining_regions=region_id_list
    while len(remaining_regions)>0:
        region_block=remaining_regions[-10:]
        sql='SELECT BrainMaps_BrainSites.ID, BrainMaps_BrainSites.BrainSite FROM BrainMaps_BrainSites WHERE BrainMaps_BrainSites.ID IN (%s)' % ','.join(region_block)
        result=perform_query(sql, {})
        brainregion_id_idx=result['fields'].index('ID')
        brainregion_name_idx=result['fields'].index('BrainSite')
        for x in result['data'].values():
            region_map[x[brainregion_id_idx]]=x[brainregion_name_idx]
        remaining_regions=remaining_regions[:-10]

    for axon_origin,axon_terminal in zip(axon_origins,axon_terminals):
        print('%s projects to %s' % (region_map[axon_origin],region_map[axon_terminal]))
#    # injection query
#    sql='SELECT Injections.ID FROM Injections WHERE ID_BrainSite IN (SELECT BrainMaps_BrainSites.ID FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE BrainSite LIKE $region OR Acronym LIKE $region)'
#    url='%s%s' % (base_url, urllib.quote_plus(sql))
#    url+='&region=%25%'+source_region+'%25&format=json'
#    result=json.load(urllib.urlopen(url))
#    print(result)
#
#    # labeled query
#    sql='SELECT Injections.ID, Injections.ID_Method FROM Injections JOIN LabelledSites_Descriptions ON LabelledSites_Descriptions.ID_Injection=Injections.ID JOIN LabelledSites_Data ON LabelledSites_Data.ID_Description=LabelledSites_Descriptions.ID WHERE LabelledSites_Data.ID_BrainSite IN (SELECT BrainMaps_BrainSites.ID FROM BrainMaps_BrainSites JOIN BrainMaps_BrainSiteAcronyms ON BrainMaps_BrainSiteAcronyms.ID=BrainMaps_BrainSites.ID_BrainMaps_BrainSiteAcronym WHERE BrainSite LIKE $region OR Acronym LIKE $region)'
#    url='%s%s' % (base_url, urllib.quote_plus(sql))
#    url+='&region=%25%'+source_region+'%25&format=json'
#    result=json.load(urllib.urlopen(url))
#    method_id_idx=result['fields'].index('ID_Method')
#    for injection_id, values in result['data'].iteritems():
#        print('injection: %s' % injection_id)
#        method_id=values[method_id_idx]
#        sql='SELECT ID, TracerSubstance FROM Methods WHERE ID=$method_id'
#        method_result=perform_query(sql,{'method_id':method_id})
#        substance_idx=method_result['fields'].index('TracerSubstance')
#        for method_id, method_values in method_result['data'].iteritems():
#            print('Method %s, substance=%s' % (method_id,method_values[substance_idx]))





def perform_query(sql, values):
    base_url='http://cocomac.g-node.org/cocomac2/services/custom_sql_query.php?sql='
    url='%s%s' % (base_url, urllib.quote_plus(sql))
    for key,val in values.iteritems():
        url+='&%s=%s' % (key,urllib.quote_plus(val))
    url+='&format=json'
    return json.load(urllib.urlopen(url))

if __name__=='__main__':
    test_new_cocomac()