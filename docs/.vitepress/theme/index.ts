// docs/.vitepress/theme/index.ts
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { theme as openapiTheme, useOpenapi } from 'vitepress-openapi/client'
import 'vitepress-openapi/dist/style.css'
import './custom.css'

import mermaid from 'mermaid'
import elkLayouts from '@mermaid-js/layout-elk'

// Phase 1: load placeholder spec; Phase 2 swaps in the real export
import spec from '../../public/openapi.json' with { type: 'json' }

// CP-5: SSR guard — ELK loader registration must be browser-only
if (typeof window !== 'undefined') {
  mermaid.registerLayoutLoaders(elkLayouts)
}

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    useOpenapi({ spec })
    openapiTheme.enhanceApp({ app })
  },
} satisfies Theme
