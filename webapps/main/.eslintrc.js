const path = require('node:path');

module.exports = {
  // https://eslint.org/docs/user-guide/configuring#configuration-cascading-and-hierarchy
  // This option interrupts the configuration hierarchy at this file
  // Remove this if you have an higher level ESLint config file (it usually happens into a monorepos)
  root: true,

  parserOptions: {
    ecmaVersion: '2021', // Allows for the parsing of modern ECMAScript features
  },

  env: {
    node: true,
    browser: true,
    'vue/setup-compiler-macros': true,
  },

  // Rules order is important, please avoid shuffling them
  extends: [
    // Base ESLint recommended rules
    'eslint:recommended',

    // Uncomment any of the lines below to choose desired strictness,
    // but leave only one uncommented!
    // See https://eslint.vuejs.org/rules/#available-rules
    // 'plugin:vue/vue3-essential', // Priority A: Essential (Error Prevention)
    // 'plugin:vue/vue3-strongly-recommended', // Priority B: Strongly Recommended (Improving Readability)
    'plugin:vue/vue3-recommended', // Priority C: Recommended (Minimizing Arbitrary Choices and Cognitive Overhead)

    'plugin:import/recommended',

    'prettier',
  ],

  plugins: [
    // https://eslint.vuejs.org/user-guide/#why-doesn-t-it-work-on-vue-files
    // required to lint *.vue files
    'vue',
  ],

  globals: {
    ga: 'readonly', // Google Analytics
    cordova: 'readonly',
    __statics: 'readonly',
    __QUASAR_SSR__: 'readonly',
    __QUASAR_SSR_SERVER__: 'readonly',
    __QUASAR_SSR_CLIENT__: 'readonly',
    __QUASAR_SSR_PWA__: 'readonly',
    process: 'readonly',
    Capacitor: 'readonly',
    chrome: 'readonly',

    // Can be removed once defineModel is released as stable and included in eslint-plugin-vue
    defineModel: 'readonly',
  },

  settings: {
    'import/extensions': ['.js', '.vue'],
    'import/parsers': { 'vue-eslint-parser': ['.vue'] },
    // To avoid import/default error with <script setup>
    'import/ignore': ['.vue$'],
    'import/resolver': {
      typescript: {
        project: path.resolve(__dirname, './jsconfig.json'),
      },
    },
  },

  // add your custom rules here
  rules: {
    // TODO: Enable this rule after gradually converting all prop names to camelCase
    'vue/prop-name-casing': 'off',
    'vue/no-unsupported-features': [
      'error',
      {
        version: require('vue').version,
      },
    ],
    'vue/padding-line-between-blocks': 'warn',
    'vue/no-empty-component-block': 'warn',
    'vue/eqeqeq': 'error',

    // To make the following work: `import Sortable from 'sortablejs'`
    'import/no-named-as-default': 'off',
    'import/order': [
      'warn',
      {
        alphabetize: { order: 'asc' },
        groups: [
          'builtin',
          'external',
          'internal',
          'parent',
          'sibling',
          'index',
          'object',
          'type',
        ],
      },
    ],

    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    // allow debugger during development only
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  },
};
