


export default function multiFieldSearch(searchString, testItem, fieldList) {
  // create the list of search terms removing duplicates
  let searchTerms = [...new Set(searchString.toLowerCase().split(' '))]

  // create the list of words to search in, removing duplicates
  let matchString = ''
  fieldList.forEach( field => matchString += testItem[field] + ' ' )

  let matchContext = [...new Set(matchString.toLowerCase().split(' '))]

  // make sure that all search terms are included in at least one word
  let match = searchTerms.every(searchTerm => {
    let termMatch = matchContext.some(matchTerm => matchTerm.includes(searchTerm))
    return termMatch
  })

  // return true if search matches or if search box empty 
  return match
}