module.exports = {
  transpileDependencies: [
    "vuetify"
  ],
  devServer: {
  	watchOptions: {
  		ignored: ['public/docs/**', 'public/media/**']
  	}
  }
}