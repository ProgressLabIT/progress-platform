export default {
  created() {
    if (typeof this.operation === 'undefined') {
      window.alert("Codice operazione non valido, verrai reindirizzato alla lista operazioni.")
      this.$router.push({ name: 'operationLibrary' })
    }
  }
}