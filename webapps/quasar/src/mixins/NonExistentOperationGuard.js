export default {
  beforeMount() {
    if (typeof this.operation === 'undefined') {
      window.alert("Codice operazione non valido, verrai reindirizzato alla lista operazioni.")
      this.$router.push({ name: 'operationLibrary' })
    }
  }
}
