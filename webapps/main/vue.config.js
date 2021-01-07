module.exports = {
  transpileDependencies: [
    "vuetify"
  ],
  pluginOptions: {
    i18n: {
      locale: 'it',
      fallbackLocale: 'it',
      localeDir: 'locales',
      enableInSFC: false
    }
  },
  devServer: {
    disableHostCheck: true,
  	watchOptions: {
  		ignored: ['public/docs/**', 'public/media/**']
  	},
	  // public: 'progress.localhost:80',
  }
}