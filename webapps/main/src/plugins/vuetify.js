import Vue from 'vue';
import Vuetify from 'vuetify/lib';
import { Ripple } from 'vuetify/lib/directives'

Vue.use(Vuetify, {
	directives: {
    Ripple
  }
});

const opts = {
	global: {
		ripples: false,
	},
	// icons: {
	// 	iconfont: 'md'
	// },

	theme: {
		dark: true,
		// options: {
		// 	customProperties: false,
		// },
		themes: {
			dark: {
				primary: '#22AED1',
				secondary: '#0DAB76',
				text_color: {
					highlight: 'rgba(255,255,255,0.87)',
					normal: 'rgba(255,255,255,0.6)',
					disabled: 'rgba(255,255,255,0.3)',
				},
				font: {
					heading: {
						family: 'Orbitron',
						spacing: '.05em',
					},
					body: {
						family: 'Red Hat Text',
						spacing: '.03em',
					}
				}
			},
      light: {
        primary: '#22AED1',
        secondary: '#0DAB76',
      }
		}
	}
}

export default new Vuetify(opts);
