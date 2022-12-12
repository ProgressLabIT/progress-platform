import multiMatch from '@/lib/MultiFieldSearch.js'

/* 
This function is used to filter both work orders and jobs according 
to the parameters defined in the parent component ProductionOverview
*/




export default function productionFilterMatch(item, filters, search_fields) {
  /* 
  Initialize filter results. 
  If any false will be found in this array the filter function will return false
  */
  let filter_match_map = []

  for (const [filter, value] of Object.entries(filters)) {
  // for (const filter of Object.keys(this.filters)) {
    
    // by default show wo in the list
    let match = true
    
    switch (filter) {

      // Perform text search in the defined fields
      case 'search_string':
        match = multiMatch(filters.search_string, item, search_fields)
        break

      case 'started':
        if (!value && item.stage === 'started') match = false
        break

      case 'queued':
        if (!value && ['created', 'planned'].includes(item.stage)) match = false
        break

      case 'on_time':
        if (!value && item.on_time) match = false
        break 

      case 'late':
        if (!value && !item.on_time) match = false
        break

      case 'critical':
        if (!value && item.critical) match = false
        break

      case 'not_critical':
        if (!value && !item.critical) match = false
        break

      case 'active':
        // Do not show if control is false and item is active
        if (!value && item.active) match = false
        break

      case 'idle':
        // Do not show if control is false and item is not active
        if (!value && !item.active) match = false
        break
    }

    // add result of the specific filter to the map
    filter_match_map.push(match)
  }

  // Return false and exclude item from list if any filter returned false
  return !filter_match_map.some( i => i === false )
}
