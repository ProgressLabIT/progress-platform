


export default function multiFieldSearch(searchString, testItem, fieldList) {
  // create the list of search terms removing duplicates
  const user_searching = !!searchString
  let searchTerms = user_searching ? [...new Set(searchString.toLowerCase().split(' '))] : []

  // create the list of words to search in, removing duplicates
  let matchString = ''
  fieldList.forEach( field => {
    // handle both string and arrays of strings. 
    // If field is array, consider each item as a term in itself
    let field_content = testItem[field]

    // Check both "nonnullity" via truthyness and type, since typeof null === 'object' 
    if (field_content && typeof field_content === 'object') {
      field_content = ''.concat(...field_content.map( i => i + ' ' ))
    }
    matchString += field_content + ' '
  })

  // Create array of words to search in, removing duplicates
  let matchContext = [...new Set(matchString.toLowerCase().split(' '))]

  // make sure that all search terms are included in at least one word
  let match = searchTerms.every(searchTerm => {
    let termMatch = matchContext.some(matchTerm => matchTerm.includes(searchTerm))
    return termMatch
  })

  // return true if search matches or if search box empty 
  return match
}