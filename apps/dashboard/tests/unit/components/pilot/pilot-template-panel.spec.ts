import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotTemplatePanel from '@/components/pilot/PilotTemplatePanel.vue';

const sampleTemplates = [
  {
    template_id: 'tpl-1',
    slug: 'proj',
    name: '日常 10 章',
    start_chapter: 1,
    end_chapter: 10,
    budget_usd: 5,
    mode: 'pilot',
    created_at: '2026-09-01T00:00:00Z',
    updated_at: '2026-09-01T00:00:00Z',
  },
  {
    template_id: 'tpl-2',
    slug: 'proj',
    name: '正史 30 章',
    start_chapter: 1,
    end_chapter: 30,
    budget_usd: 20,
    mode: 'canon',
    created_at: '2026-09-01T00:00:00Z',
    updated_at: '2026-09-01T00:00:00Z',
  },
];

describe('PilotTemplatePanel', () => {
  it('renders select with template options and empty state guidance', () => {
    const wrapper = mount(PilotTemplatePanel, {
      props: {
        slug: 'proj',
        templates: sampleTemplates,
        loading: false,
        saveLoading: false,
        error: null,
        message: null,
      },
    });
    expect(wrapper.find('[data-testid="pilot-template-panel"]').exists()).toBe(true);
    const options = wrapper.findAll('[data-testid="template-select"] option');
    expect(options.length).toBe(3); // placeholder + 2 templates
    expect(wrapper.text()).toContain('日常 10 章');
  });

  it('emits apply with selected template id', async () => {
    const wrapper = mount(PilotTemplatePanel, {
      props: {
        slug: 'proj',
        templates: sampleTemplates,
        loading: false,
        saveLoading: false,
        error: null,
        message: null,
      },
    });
    await wrapper.find('[data-testid="template-select"]').setValue('tpl-2');
    await wrapper.find('[data-testid="template-apply"]').trigger('click');
    const events = wrapper.emitted('apply');
    expect(events).toBeTruthy();
    expect(events![0][0]).toBe('tpl-2');
  });

  it('emits remove with selected template id', async () => {
    const wrapper = mount(PilotTemplatePanel, {
      props: {
        slug: 'proj',
        templates: sampleTemplates,
        loading: false,
        saveLoading: false,
        error: null,
        message: null,
      },
    });
    await wrapper.find('[data-testid="template-select"]').setValue('tpl-1');
    await wrapper.find('[data-testid="template-delete"]').trigger('click');
    const events = wrapper.emitted('remove');
    expect(events).toBeTruthy();
    expect(events![0][0]).toBe('tpl-1');
  });

  it('emits save with name after opening save row', async () => {
    const wrapper = mount(PilotTemplatePanel, {
      props: {
        slug: 'proj',
        templates: sampleTemplates,
        loading: false,
        saveLoading: false,
        error: null,
        message: null,
      },
    });
    await wrapper.find('[data-testid="template-save"]').trigger('click');
    await wrapper.find('[data-testid="template-name"]').setValue('我的模板');
    await wrapper.find('[data-testid="template-save-confirm"]').trigger('click');
    const events = wrapper.emitted('save');
    expect(events).toBeTruthy();
    expect(events![0][0]).toEqual({ name: '我的模板' });
  });

  it('shows message and error status text', () => {
    const wrapper = mount(PilotTemplatePanel, {
      props: {
        slug: 'proj',
        templates: sampleTemplates,
        loading: false,
        saveLoading: false,
        error: '保存失败',
        message: '已保存模板「日常 10 章」',
      },
    });
    expect(wrapper.find('[data-testid="template-message"]').text()).toContain('已保存模板');
    expect(wrapper.find('[data-testid="template-error"]').text()).toContain('保存失败');
  });
});
