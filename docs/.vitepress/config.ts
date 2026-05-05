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
          { text: 'Production', collapsed: true, items: [
            { text: 'Overview', link: '/api/production/' },
            { text: 'DELETE /work-order/{wo_key}', link: '/api/production/delete-work-order/wo-key' },
            { text: 'GET /job-assignment', link: '/api/production/get-job-assignment' },
            { text: 'GET /job', link: '/api/production/get-job' },
            { text: 'GET /job/{job_key}', link: '/api/production/get-job/job-key' },
            { text: 'GET /job/{job_key}/time', link: '/api/production/get-job/job-key/time' },
            { text: 'GET /queue/site/{site_key}', link: '/api/production/get-queue/site/site-key' },
            { text: 'GET /work-order-search-opts', link: '/api/production/get-work-order-search-opts' },
            { text: 'GET /work-order', link: '/api/production/get-work-order' },
            { text: 'GET /work-order/{wo_key}', link: '/api/production/get-work-order/wo-key' },
            { text: 'GET /work-order/{wo_key}/traceability', link: '/api/production/get-work-order/wo-key/traceability' },
            { text: 'GET /work-session', link: '/api/production/get-work-session' },
            { text: 'POST /jobs/start', link: '/api/production/jobs/start' },
            { text: 'PATCH /work-order/{wo_key}', link: '/api/production/patch-work-order/wo-key' },
            { text: 'PATCH /work-order/{wo_key}/update-quantities', link: '/api/production/patch-work-order/wo-key/update-quantities' },
            { text: 'POST /job/update', link: '/api/production/post-job/update' },
            { text: 'POST /work-order', link: '/api/production/post-work-order' },
            { text: 'PUT /queue', link: '/api/production/put-queue' },
            { text: 'PUT /queue/operator/{operator_key}', link: '/api/production/put-queue/operator/operator-key' },
          ]},
          { text: 'Warehouse', collapsed: true, items: [
            { text: 'Overview', link: '/api/warehouse/' },
            { text: 'DELETE /inventory/count-assignment', link: '/api/warehouse/delete-inventory/count-assignment' },
            { text: 'DELETE /inventory/count-session', link: '/api/warehouse/delete-inventory/count-session' },
            { text: 'DELETE /position/{position_key}', link: '/api/warehouse/delete-position/position-key' },
            { text: 'GET /inventory', link: '/api/warehouse/get-inventory' },
            { text: 'GET /inventory/count-assignment', link: '/api/warehouse/get-inventory/count-assignment' },
            { text: 'GET /inventory/count-position-status', link: '/api/warehouse/get-inventory/count-position-status' },
            { text: 'GET /inventory/count-record', link: '/api/warehouse/get-inventory/count-record' },
            { text: 'GET /inventory/count-session', link: '/api/warehouse/get-inventory/count-session' },
            { text: 'GET /inventory/count-session/{session_key}', link: '/api/warehouse/get-inventory/count-session/session-key' },
            { text: 'GET /inventory/count-session/{session_key}/completed-positions', link: '/api/warehouse/get-inventory/count-session/session-key/completed-positions' },
            { text: 'GET /inventory/count-session/{session_key}/processed-records', link: '/api/warehouse/get-inventory/count-session/session-key/processed-records' },
            { text: 'GET /movement-list', link: '/api/warehouse/get-movement-list' },
            { text: 'GET /movement', link: '/api/warehouse/get-movement' },
            { text: 'GET /movement/latest-positions', link: '/api/warehouse/get-movement/latest-positions' },
            { text: 'GET /movement/latest-products', link: '/api/warehouse/get-movement/latest-products' },
            { text: 'GET /position-hierarchy', link: '/api/warehouse/get-position-hierarchy' },
            { text: 'GET /position', link: '/api/warehouse/get-position' },
            { text: 'GET /position/{position_key}', link: '/api/warehouse/get-position/position-key' },
            { text: 'PATCH /position/{position_key}', link: '/api/warehouse/patch-position/position-key' },
            { text: 'POST /inventory/count-assignment', link: '/api/warehouse/post-inventory/count-assignment' },
            { text: 'POST /inventory/count-record/import', link: '/api/warehouse/post-inventory/count-record/import' },
            { text: 'POST /inventory/count-session', link: '/api/warehouse/post-inventory/count-session' },
            { text: 'POST /movement-list', link: '/api/warehouse/post-movement-list' },
            { text: 'POST /movement', link: '/api/warehouse/post-movement' },
            { text: 'POST /position', link: '/api/warehouse/post-position' },
            { text: 'PUT /inventory/count-session/{session_key}', link: '/api/warehouse/put-inventory/count-session/session-key' },
          ]},
          { text: 'Serial', collapsed: true, items: [
            { text: 'Overview', link: '/api/serial/' },
            { text: 'GET /component-batch', link: '/api/serial/get-component-batch' },
            { text: 'GET /serial-batch', link: '/api/serial/get-serial-batch' },
            { text: 'GET /serial-children', link: '/api/serial/get-serial-children' },
            { text: 'GET /serial-code', link: '/api/serial/get-serial-code' },
            { text: 'GET /serial-code/verify-free', link: '/api/serial/get-serial-code/verify-free' },
            { text: 'GET /serial-field', link: '/api/serial/get-serial-field' },
            { text: 'GET /serial-hierarchy', link: '/api/serial/get-serial-hierarchy' },
            { text: 'GET /serial-parents', link: '/api/serial/get-serial-parents' },
            { text: 'GET /serial-selection', link: '/api/serial/get-serial-selection' },
            { text: 'GET /serial', link: '/api/serial/get-serial' },
            { text: 'GET /serial/{serial_key}', link: '/api/serial/get-serial/serial-key' },
            { text: 'GET /serial/{serial_key}/dhr', link: '/api/serial/get-serial/serial-key/dhr' },
            { text: 'GET /wip-serial', link: '/api/serial/get-wip-serial' },
          ]},
          { text: 'Collaboration', collapsed: true, items: [
            { text: 'Overview', link: '/api/collaboration/' },
            { text: 'DELETE /issue-type/{issue_type_key}', link: '/api/collaboration/delete-issue-type/issue-type-key' },
            { text: 'DELETE /task-type/{type_key}', link: '/api/collaboration/delete-task-type/type-key' },
            { text: 'GET /issue-type', link: '/api/collaboration/get-issue-type' },
            { text: 'GET /issue', link: '/api/collaboration/get-issue' },
            { text: 'GET /message', link: '/api/collaboration/get-message' },
            { text: 'GET /task-type', link: '/api/collaboration/get-task-type' },
            { text: 'GET /task', link: '/api/collaboration/get-task' },
            { text: 'GET /task/{task_key}', link: '/api/collaboration/get-task/task-key' },
            { text: 'PATCH /issue-type/{issue_type_key}', link: '/api/collaboration/patch-issue-type/issue-type-key' },
            { text: 'POST /issue-type', link: '/api/collaboration/post-issue-type' },
            { text: 'POST /task-type', link: '/api/collaboration/post-task-type' },
            { text: 'PUT /task-type/{type_key}', link: '/api/collaboration/put-task-type/type-key' },
          ]},
          { text: 'Quality', collapsed: true, items: [
            { text: 'Overview', link: '/api/quality/' },
            { text: 'DELETE /field/{field_key}', link: '/api/quality/delete-field/field-key' },
            { text: 'DELETE /list/{field_key}', link: '/api/quality/delete-list/field-key' },
            { text: 'DELETE /print-template/{template_key}', link: '/api/quality/delete-print-template/template-key' },
            { text: 'GET /field', link: '/api/quality/get-field' },
            { text: 'GET /list', link: '/api/quality/get-list' },
            { text: 'GET /print-template', link: '/api/quality/get-print-template' },
            { text: 'GET /print-template/{template_key}', link: '/api/quality/get-print-template/template-key' },
            { text: 'POST /field', link: '/api/quality/post-field' },
            { text: 'POST /list/{field_key}', link: '/api/quality/post-list/field-key' },
            { text: 'POST /print-job', link: '/api/quality/post-print-job' },
            { text: 'POST /print-template', link: '/api/quality/post-print-template' },
            { text: 'POST /update-template-assignments', link: '/api/quality/post-update-template-assignments' },
            { text: 'PUT /field/{field_key}', link: '/api/quality/put-field/field-key' },
            { text: 'PUT /print-template', link: '/api/quality/put-print-template' },
          ]},
          { text: 'Traceability', collapsed: true, items: [
            { text: 'Overview', link: '/api/traceability/' },
            { text: 'GET /batch/{batch_key}', link: '/api/traceability/get-batch/batch-key' },
            { text: 'GET /batch/{batch_key}/serials', link: '/api/traceability/get-batch/batch-key/serials' },
            { text: 'GET /event', link: '/api/traceability/get-event' },
            { text: 'GET /wip', link: '/api/traceability/get-wip' },
            { text: 'POST /batch/temp-data', link: '/api/traceability/post-batch/temp-data' },
            { text: 'POST /event', link: '/api/traceability/post-event' },
            { text: 'POST /event/bulk', link: '/api/traceability/post-event/bulk' },
            { text: 'POST /job/{job_key}/heartbeat', link: '/api/traceability/post-job/job-key/heartbeat' },
            { text: 'PUT /batch/{batch_key}/serial-temp-links', link: '/api/traceability/put-batch/batch-key/serial-temp-links' },
          ]},
          { text: 'Process', collapsed: true, items: [
            { text: 'Overview', link: '/api/process/' },
            { text: 'DELETE /operation/{operation_key}', link: '/api/process/delete-operation/operation-key' },
            { text: 'DELETE /step/{step_key}/media/{filename}', link: '/api/process/delete-step/step-key/media/filename' },
            { text: 'GET /operation', link: '/api/process/get-operation' },
            { text: 'GET /phase', link: '/api/process/get-phase' },
            { text: 'GET /procedure/{phase_key}', link: '/api/process/get-procedure/phase-key' },
            { text: 'GET /product/{product_key}/process', link: '/api/process/get-product/product-key/process' },
            { text: 'GET /step/{step_key}/media', link: '/api/process/get-step/step-key/media' },
            { text: 'PATCH /operation/{operation_key}', link: '/api/process/patch-operation/operation-key' },
            { text: 'POST /operation', link: '/api/process/post-operation' },
            { text: 'POST /operation/{operation_key}/copy', link: '/api/process/post-operation/operation-key/copy' },
            { text: 'POST /product/{product_key}/counter/copy', link: '/api/process/post-product/product-key/counter/copy' },
            { text: 'POST /product/{product_key}/process/copy', link: '/api/process/post-product/product-key/process/copy' },
            { text: 'POST /step/{step_key}/media', link: '/api/process/post-step/step-key/media' },
            { text: 'PUT /product/{product_key}/process', link: '/api/process/put-product/product-key/process' },
          ]},
          { text: 'Product', collapsed: true, items: [
            { text: 'Overview', link: '/api/product/' },
            { text: 'DELETE /{product_key}', link: '/api/product/delete-product-key' },
            { text: 'DELETE /{product_key}/doc/{doc_name}', link: '/api/product/delete-product-key/doc/doc-name' },
            { text: 'DELETE /{product_key}/image', link: '/api/product/delete-product-key/image' },
            { text: 'GET /{product_key}', link: '/api/product/get-product-key' },
            { text: 'GET /{product_key}/bom', link: '/api/product/get-product-key/bom' },
            { text: 'GET /{product_key}/stats', link: '/api/product/get-product-key/stats' },
            { text: 'PATCH /{product_key}', link: '/api/product/patch-product-key' },
            { text: 'POST /copy', link: '/api/product/post-copy' },
            { text: 'POST /{product_key}/doc', link: '/api/product/post-product-key/doc' },
            { text: 'PUT /{product_key}', link: '/api/product/put-product-key' },
            { text: 'PUT /{product_key}/bom', link: '/api/product/put-product-key/bom' },
            { text: 'PUT /{product_key}/image', link: '/api/product/put-product-key/image' },
          ]},
          { text: 'Organization', collapsed: true, items: [
            { text: 'Overview', link: '/api/organization/' },
            { text: 'DELETE /api-token/{token_key}', link: '/api/organization/delete-api-token/token-key' },
            { text: 'DELETE /user/{user_key}', link: '/api/organization/delete-user/user-key' },
            { text: 'DELETE /user/{user_key}/password', link: '/api/organization/delete-user/user-key/password' },
            { text: 'GET /api-token', link: '/api/organization/get-api-token' },
            { text: 'GET /department', link: '/api/organization/get-department' },
            { text: 'GET /user', link: '/api/organization/get-user' },
            { text: 'GET /user/api-tokens', link: '/api/organization/get-user/api-tokens' },
            { text: 'PATCH /user/{user_key}', link: '/api/organization/patch-user/user-key' },
            { text: 'POST /user', link: '/api/organization/post-user' },
            { text: 'PUT /user/{user_key}/image', link: '/api/organization/put-user/user-key/image' },
            { text: 'PUT /user/{user_key}/password', link: '/api/organization/put-user/user-key/password' },
          ]},
          { text: 'Administration', collapsed: true, items: [
            { text: 'Overview', link: '/api/administration/' },
            { text: 'DELETE /force-delete-work-order/{work_order_key}', link: '/api/administration/delete-force-delete-work-order/work-order-key' },
            { text: 'DELETE /reset/inventory', link: '/api/administration/delete-reset/inventory' },
            { text: 'DELETE /reset/prod', link: '/api/administration/delete-reset/prod' },
          ]},
          { text: 'Configuration', collapsed: true, items: [
            { text: 'Overview', link: '/api/configuration/' },
            { text: 'DELETE /counter/{counter_key}', link: '/api/configuration/delete-counter/counter-key' },
            { text: 'DELETE /custom-data/{key}', link: '/api/configuration/delete-custom-data/key' },
            { text: 'GET /config', link: '/api/configuration/get-config' },
            { text: 'GET /counter', link: '/api/configuration/get-counter' },
            { text: 'GET /custom-data', link: '/api/configuration/get-custom-data' },
            { text: 'GET /custom-data/{key}', link: '/api/configuration/get-custom-data/key' },
            { text: 'GET /tag', link: '/api/configuration/get-tag' },
            { text: 'PATCH /config', link: '/api/configuration/patch-config' },
            { text: 'POST /counter', link: '/api/configuration/post-counter' },
            { text: 'POST /tag', link: '/api/configuration/post-tag' },
            { text: 'POST /tag/update-connections', link: '/api/configuration/post-tag/update-connections' },
            { text: 'PUT /config/{key}/file', link: '/api/configuration/put-config/key/file' },
            { text: 'PUT /counter/{counter_key}', link: '/api/configuration/put-counter/counter-key' },
            { text: 'PUT /custom-data/{key}', link: '/api/configuration/put-custom-data/key' },
          ]},
          { text: 'Attachments', collapsed: true, items: [
            { text: 'Overview', link: '/api/attachments/' },
            { text: 'DELETE /files', link: '/api/attachments/delete-files' },
            { text: 'DELETE /media/{media_key}', link: '/api/attachments/delete-media/media-key' },
            { text: 'GET /media/{media_key}', link: '/api/attachments/get-media/media-key' },
            { text: 'PATCH /media/{media_key}', link: '/api/attachments/patch-media/media-key' },
            { text: 'POST /files', link: '/api/attachments/post-files' },
            { text: 'POST /media/create', link: '/api/attachments/post-media/create' },
          ]},
          { text: 'Security', collapsed: true, items: [
            { text: 'Overview', link: '/api/security/' },
            { text: 'DELETE /session/{session_key}', link: '/api/security/delete-session/session-key' },
            { text: 'GET /whoami', link: '/api/security/get-whoami' },
            { text: 'POST /auth', link: '/api/security/post-auth' },
            { text: 'POST /session', link: '/api/security/post-session' },
            { text: 'POST /user/{user_key}/verify', link: '/api/security/post-user/user-key/verify' },
          ]},
          { text: 'Notification', collapsed: true, items: [
            { text: 'Overview', link: '/api/notification/' },
            { text: 'GET /notification/{topic}', link: '/api/notification/get-notification/topic' },
            { text: 'POST /notification/ticket', link: '/api/notification/post-notification/ticket' },
          ]},
        ]},
      ],
      '/events/': [
        { text: 'Events Reference', items: [
          { text: 'Overview', link: '/events/' },
          { text: 'production: JobStarted', link: '/events/production/job-started' },
          { text: 'production: BatchCompleted', link: '/events/production/batch-completed' },
          { text: '↳ Fan-out: next-phase spawn', link: '/events/production/batch-completed-fanout' },
        ]},
      ],
      '/cli/': [
        { text: 'CLI Reference', items: [
          { text: 'Overview', link: '/cli/' },
          { text: 'progress init', link: '/cli/init' },
          { text: 'progress restore', link: '/cli/restore' },
          { text: 'progress tap', link: '/cli/tap' },
        ]},
      ],
      '/users/': [
        { text: 'User Documentation', items: [
          { text: 'Overview', link: '/users/' },
          { text: 'Production', link: '/users/production' },
          { text: 'Inventory', link: '/users/inventory' },
          { text: 'Counting', link: '/users/counting' },
          { text: 'User Hub', link: '/users/user-hub' },
          { text: 'Warehouse', link: '/users/warehouse' },
          { text: 'Coverage', link: '/users/coverage' },
        ]},
      ],
      '/admins/': [
        { text: 'Admin & Integrator', items: [
          { text: 'Overview', link: '/admins/' },
          { text: 'Deployment', link: '/admins/deployment' },
          { text: 'Configuration', link: '/admins/configuration' },
          { text: 'Integration', link: '/admins/integration' },
          { text: 'Operations', link: '/admins/operations' },
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
