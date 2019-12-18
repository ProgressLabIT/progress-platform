import Vue from 'vue';
import Vuetify from 'vuetify/lib';

Vue.use(Vuetify);

const opts = {
	icons: {
		iconfont: 'md'
	},
	theme: {
		dark:true,
		options: {
			customProperties: true,
		},
		themes: {
			dark: {
				colors: {
					background: {
						0: '#131E21',
						1: '#1F2A2D',
						2: '#242E31'
					},
					blue: '#22AED1',
					green: '#0DAB76',
					red: '#E71D36',
					orange: '#FF9F1C',
				},
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
			}
		}
	}
}

export default new Vuetify(opts);
