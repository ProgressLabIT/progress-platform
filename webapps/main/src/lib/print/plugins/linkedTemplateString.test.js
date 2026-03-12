import { describe, it, expect } from 'vitest';
import { createLinkedTemplateString } from './linkedTemplateString.js';

describe('createLinkedTemplateString', () => {
  it('returns object with defaultSchema.linkType === "template_expression"', () => {
    const plugin = createLinkedTemplateString();
    expect(plugin.propPanel.defaultSchema.linkType).toBe('template_expression');
  });

  it('returns object with defaultSchema.templateExpression === ""', () => {
    const plugin = createLinkedTemplateString();
    expect(plugin.propPanel.defaultSchema.templateExpression).toBe('');
  });

  it('has pdf property inherited from base text plugin', () => {
    const plugin = createLinkedTemplateString([]);
    expect(plugin.pdf).toBeDefined();
  });
});
