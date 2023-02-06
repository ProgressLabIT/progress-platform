const mutations_to_ignore = [
  'TOGGLE_SESSION_LOCK',
  'CLOSE_SESSION'
]

export const resetSessionTimeoutAtStoreChange = store => {
  store.subscribe( (mutation) => {
    if (!mutations_to_ignore.includes(mutation.type)) {
      store.dispatch('setSessionTimeout')
    }
  })
}
