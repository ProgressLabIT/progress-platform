// docs/.vitepress/config.ts
import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

export default withMermaid(defineConfig({
  // Site identity
  lang: 'en-US',
  title: 'Progress Platform',
  description: 'Manufacturing Operations Management — event-sourced MES on FastAPI + ArangoDB + Vue 3.',
  base: '/progress-platform/',  // D-13: GH Pages project base
  cleanUrls: true,              // CP-4: sidebar links omit .html
  lastUpdated: true,            // CP-9: requires fetch-depth: 0 in deploy workflow
  // ignoreDeadLinks: VitePress default is false; lychee handles fragments separately (Pitfall 1.4)

  // SEO / discoverability
  sitemap: {
    hostname: 'https://progresslabit.github.io/progress-platform/',  // D-13 / CP-3
  },

  // M-01: favicon link removed pending real asset (Phase 4 launch-prep)
  head: [
    ['meta', { name: 'theme-color', content: '#0066cc' }],
  ],

  markdown: {
    lineNumbers: true,
  },

  themeConfig: {
    siteTitle: 'Progress Platform',

    // D-07: 5 sections in fixed order
    nav: [
      { text: 'API', link: '/api/' },
      { text: 'Events', link: '/events/' },
      { text: 'CLI', link: '/cli/' },
      { text: 'Users', link: '/users/' },
      { text: 'Admins', link: '/admins/' },
    ],

    // Pitfall 1.2: hand-written sidebar (no auto-sidebar plugin)
    // CP-4: links omit .html (cleanUrls: true)
    sidebar: {
      '/api/': [
        { text: 'API Reference', items: [
          { text: 'Overview', link: '/api/' },
          { text: 'production: jobs/start', link: '/api/production/jobs/start' },
        ]},
      ],
      '/events/': [
        { text: 'Events Reference', items: [
          { text: 'Overview', link: '/events/' },
          { text: 'production: JobStarted', link: '/events/production/job-started' },
        ]},
      ],
      '/cli/': [
        { text: 'CLI Reference', items: [
          { text: 'Overview', link: '/cli/' },
          { text: 'progress init', link: '/cli/init' },
        ]},
      ],
      '/users/': [
        { text: 'User Documentation', items: [
          { text: 'Overview', link: '/users/' },
          { text: 'Production', link: '/users/production' },
        ]},
      ],
      '/admins/': [
        { text: 'Admin & Integrator', items: [
          { text: 'Overview', link: '/admins/' },
          { text: 'Deployment', link: '/admins/deployment' },
        ]},
      ],
    },

    // Pitfall 1.3 / SITE-05: MiniSearch local search
    search: {
      provider: 'local',
      options: {
        detailedView: true,
        miniSearch: {
          searchOptions: {
            fuzzy: 0.2,
            prefix: true,
            boost: { title: 4, text: 2, titles: 1 },
          },
        },
      },
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/ProgressLabIT/progress-platform' },
      { icon: 'gitlab', link: 'https://gitlab.com/progresslab/progress-platform' },
    ],
    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2026 Progress Platform Contributors.',
    },

    // D-13 / SITE-08: source-code permalinks always github.com (never gitlab)
    editLink: {
      pattern: 'https://github.com/ProgressLabIT/progress-platform/edit/DEV/docs/:path',
      text: 'Edit this page on GitHub',
    },
  },

  mermaid: {
    theme: 'default',
  },
  mermaidPlugin: {
    class: 'mermaid my-mermaid',
  },
}))
