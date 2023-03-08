export default {
  beforeMount() {
    if (typeof this.user_data === 'undefined') {
      window.alert("Codice utente non valido, verrai reindirizzato alla lista utenti.")
      if (this.showModal) {
        this.showModal = false
      }
      this.$router.push({ name: 'userLibrary' })
    }
  }
}
