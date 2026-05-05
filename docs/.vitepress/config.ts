// docs/.vitepress/config.ts
import { defineConfig } from 'vitepress'
import type { DefaultTheme } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'

const adminSidebar: DefaultTheme.SidebarItem[] = [
  { text: 'Admin & Developers', items: [
    { text: 'Overview', link: '/admin/' },
    { text: 'Platform Architecture', link: '/admin/architecture' },
    { text: 'Installation', link: '/admin/installation' },
    { text: 'Configuration', link: '/admins/configuration' },
    { text: 'Deployment', link: '/admins/deployment' },
    { text: 'Operations', link: '/admins/operations' },
    { text: 'Integration', link: '/admins/integration' },
    { text: 'Release & Update', link: '/admin/release-update' },
    { text: 'Backup & Restore', link: '/admin/backup-restore' },
  ]},
  { text: 'Developing Extensions', items: [
    { text: 'Prefect Workflows', link: '/admin/prefect-workflows' },
    { text: 'Streamlit Apps', link: '/admin/streamlit-apps' },
    { text: 'IIoT Streams', link: '/admin/iiot-streams' },
  ]},
]

const manualSidebar: DefaultTheme.SidebarItem[] = [
  { text: 'User Manual', items: [
    { text: 'Introduction', link: '/manual/' },
    { text: 'User Hub', link: '/manual/user-hub' },
    { text: 'Library', link: '/manual/library' },
    { text: 'Production', link: '/manual/production' },
    { text: 'Quality', link: '/manual/quality' },
    { text: 'Traceability', link: '/manual/traceability' },
    { text: 'Tasks & Issues', link: '/manual/tasks' },
    { text: 'Warehouse', link: '/manual/warehouse' },
    { text: 'Reports', link: '/manual/reports' },
    { text: 'Admin Panel', link: '/manual/admin-panel' },
  ]},
]

const referenceSidebar: DefaultTheme.SidebarItem[] = [
  { text: 'Technical Reference', items: [
    { text: 'Overview', link: '/reference/' },
    { text: 'DB Collections', link: '/reference/db-collections' },
    { text: 'Broker Subjects', link: '/reference/broker-subjects' },
  ]},
  { text: 'API Reference', collapsed: false, items: [
    { text: 'Overview', link: '/api/' },
    { text: 'Production', collapsed: true, link: '/api/production/' },
    { text: 'Warehouse', collapsed: true, link: '/api/warehouse/' },
    { text: 'Serial', collapsed: true, link: '/api/serial/' },
    { text: 'Collaboration', collapsed: true, link: '/api/collaboration/' },
    { text: 'Quality', collapsed: true, link: '/api/quality/' },
    { text: 'Traceability', collapsed: true, link: '/api/traceability/' },
    { text: 'Process', collapsed: true, link: '/api/process/' },
    { text: 'Product', collapsed: true, link: '/api/product/' },
    { text: 'Organization', collapsed: true, link: '/api/organization/' },
    { text: 'Administration', collapsed: true, link: '/api/administration/' },
    { text: 'Configuration', collapsed: true, link: '/api/configuration/' },
    { text: 'Attachments', collapsed: true, link: '/api/attachments/' },
    { text: 'Security', collapsed: true, link: '/api/security/' },
    { text: 'Notification', collapsed: true, link: '/api/notification/' },
  ]},
  { text: 'Events Reference', collapsed: false, items: [
    { text: 'Overview', link: '/events/' },
    { text: 'Production', collapsed: true, link: '/events/production/' },
    { text: 'Inventory', collapsed: true, link: '/events/inventory/' },
    { text: 'Serial', collapsed: true, link: '/events/serial/' },
    { text: 'Collaboration', collapsed: true, link: '/events/collaboration/' },
    { text: 'WIP', collapsed: true, link: '/events/wip/' },
    { text: 'Work Session', collapsed: true, link: '/events/work_session/' },
    { text: 'Admin', collapsed: true, link: '/events/admin/' },
  ]},
  { text: 'CLI Reference', collapsed: false, items: [
    { text: 'Overview', link: '/cli/' },
    { text: 'progress init', link: '/cli/init' },
    { text: 'progress restore', link: '/cli/restore' },
    { text: 'progress tap', link: '/cli/tap' },
  ]},
]

export default withMermaid(defineConfig({
  // Site identity
  lang: 'en-US',
  title: 'Progress Platform',
  description: 'Manufacturing Operations Management — event-sourced MES on FastAPI + ArangoDB + Vue 3.',
  base: '/progress-platform/',  // D-13: GH Pages project base
  cleanUrls: true,              // CP-4: sidebar links omit .html
  lastUpdated: true,            // CP-9: requires fetch-depth: 0 in deploy workflow
  // ignoreDeadLinks: VitePress default is false; lychee handles fragments separately (Pitfall 1.4)

  // Templates carry literal {placeholder} syntax for content authors; they're
  // not user-facing pages. Exclude from build so VitePress doesn't validate
  // their placeholder links and lychee doesn't either (covered by paths in lychee.toml).
  srcExclude: ['**/.vitepress/templates/**'],

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

    // 4-section navigation
    nav: [
      { text: 'Overview', link: '/overview/' },
      { text: 'User Manual', link: '/manual/' },
      { text: 'Admin & Developers', link: '/admin/' },
      { text: 'Technical Reference', link: '/reference/' },
    ],

    // Pitfall 1.2: hand-written sidebar (no auto-sidebar plugin)
    // CP-4: links omit .html (cleanUrls: true)
    sidebar: {
      // ── New section sidebars ──────────────────────────────────
      '/overview/': [
        { text: 'Overview', items: [
          { text: 'Introduction', link: '/overview/' },
          { text: 'Why Progress', link: '/overview/why-progress' },
          { text: 'Features', link: '/overview/features' },
          { text: 'Concepts & Glossary', link: '/overview/concepts' },
        ]},
      ],
      '/manual/': manualSidebar,
      '/admin/': adminSidebar,
      '/admins/': adminSidebar,
      '/reference/': referenceSidebar,
      '/api/': referenceSidebar,
      '/events/': referenceSidebar,
      '/cli/': referenceSidebar,
      '/users/': manualSidebar,
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
