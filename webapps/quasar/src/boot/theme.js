import { boot } from 'quasar/wrappers'

export const dark = {
  blue: '#22AED1',
  grey: '#707070',
  green: '#0DAB76',
  red: '#E71D36',
  orange: '#FF9F1C',

  blue_bg: 'rgba(39,174,209, .3)',
  green_bg: 'rgba(13,171,118, .3)',
  red_bg: 'rgba(213,29,54,.3)',
  // orange_bg: 'rgba(255,159,28,.3)',

  footer: '#090C0D',
  background: '#131E21',
  surface2: '#242E31',
  surface1: '#1F2A2D',

  text_low: 'rgba(255,255,255,.6)',
  text_high: 'rgba(255,255,255,.87)',
  text_disabled: 'rgba(255,255,255,.38)'
}

export const light = {
  footer: 'rgba(30,52,58,1)',
  black: '#090C0D',
  background: '#eeeeee',
  surface1: '#ffffff',
  surface2: '#ffffff',
  grey: '#707070',
  blue: '#22AED1',
  blue_bg: 'rgba(39,174,209, .3)',
  green: '#0DAB76',
  green_bg: 'rgba(13,171,118, .3)',
  red: '#E71D36',
  red_bg: 'rgba(213,29,54,.3)',
  orange: '#FF9F1C',
  orange_bg: 'rgba(255,159,28,.3)',
  text_high: 'rgba(30,52,58)',
  text_low: 'rgba(0,0,0,.6)',
  text_disabled: 'rgba(0,0,0,.38)'
}

export default boot(({ app }) => {
  app.config.globalProperties.$theme = dark
})
