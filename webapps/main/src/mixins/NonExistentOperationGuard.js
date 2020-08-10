export default {
  created() {
    if (typeof this.operation === 'undefined') {
      console.log(this.operation)
      window.alert("Codice operazione non valido, verrai reindirizzato alla lista operazioni.")
      this.$router.push({ name: 'operationLibrary' })
    }
  }
}