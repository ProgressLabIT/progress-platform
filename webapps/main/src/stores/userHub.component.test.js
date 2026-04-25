import { setActivePinia, createPinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useUserHubStore } from './userHub.js';

vi.mock('@/boot/axios', () => ({
  api: { get: vi.fn() },
}));
import { api } from '@/boot/axios';

// -----------------------------------------------------------------------------
// useUserHubStore — session-scoped notification feed
//
// Contract (frozen for Plans 04/05):
//   - notifications: ref<NotificationItem[]>
//   - unreadCount: computed<number>
//   - hasUnread: computed<boolean>
//   - pushNotification(item): prepend; evict oldest at cap 100
//   - markRead(id): flip .read=true if found and currently false (no-op otherwise)
//   - reset(): clear notifications (logout / test teardown)
//
// Normalization (T-02-03-01 mitigation): only 7 whitelisted keys survive; unknown
// payload fields are dropped to prevent attacker-influenced props from leaking
// into the UI layer.
// -----------------------------------------------------------------------------

function makeItem(overrides = {}) {
  return {
    id: 'id-' + Math.random().toString(36).slice(2),
    event_type: 'TASK_UPDATED',
    task_key: 'T1',
    task_code: 'Some task',
    assigned_by: 'userX',
    ts: '2026-04-17T10:00:00Z',
    read: false,
    ...overrides,
  };
}

describe('useUserHubStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('test_initial_state_empty — notifications=[], unreadCount=0, hasUnread=false', () => {
    const store = useUserHubStore();
    expect(store.notifications).toEqual([]);
    expect(store.unreadCount).toBe(0);
    expect(store.hasUnread).toBe(false);
  });

  it('test_pushNotification_prepends_newest_first', () => {
    const store = useUserHubStore();
    const a = makeItem({ id: 'A' });
    const b = makeItem({ id: 'B' });
    store.pushNotification(a);
    store.pushNotification(b);
    expect(store.notifications[0].id).toBe('B');
    expect(store.notifications[1].id).toBe('A');
  });

  it('test_pushNotification_normalizes_item_shape — drops unknown fields (T-02-03-01)', () => {
    const store = useUserHubStore();
    store.pushNotification({
      id: 'X',
      event_type: 'TASK_UPDATED',
      task_key: 'T1',
      task_code: 'Title',
      assigned_by: 'userA',
      ts: '2026-04-17T10:00:00Z',
      read: false,
      __extra: 'junk',
      malicious: '<script>alert(1)</script>',
    });
    const stored = store.notifications[0];
    expect(Object.keys(stored).sort()).toEqual(
      [
        'assigned_by',
        'event_type',
        'id',
        'read',
        'task_key',
        'task_code',
        'ts',
      ].sort(),
    );
    expect(stored).not.toHaveProperty('__extra');
    expect(stored).not.toHaveProperty('malicious');
  });

  it('test_pushNotification_defaults_read_false when read omitted', () => {
    const store = useUserHubStore();
    const item = makeItem({ id: 'X' });
    delete item.read;
    store.pushNotification(item);
    expect(store.notifications[0].read).toBe(false);
  });

  it('test_cap_evicts_oldest_at_100 (T-02-03-02)', () => {
    const store = useUserHubStore();
    // Push 101 items in order 1..101.
    // Because pushNotification prepends, after all pushes:
    //   notifications[0]   = item 101
    //   notifications[99]  = item 2    (item 1 evicted)
    for (let i = 1; i <= 101; i++) {
      store.pushNotification(makeItem({ id: 'item-' + i, task_key: 'T' + i }));
    }
    expect(store.notifications.length).toBe(100);
    expect(store.notifications[0].id).toBe('item-101');
    expect(store.notifications[99].id).toBe('item-2');
    // item-1 must be gone
    const hasItem1 = store.notifications.some((n) => n.id === 'item-1');
    expect(hasItem1).toBe(false);
  });

  it('test_markRead_flips_one_item', () => {
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'A' }));
    store.pushNotification(makeItem({ id: 'B' }));
    // After prepending: [B, A], both unread
    expect(store.unreadCount).toBe(2);
    store.markRead('A');
    const a = store.notifications.find((n) => n.id === 'A');
    const b = store.notifications.find((n) => n.id === 'B');
    expect(a.read).toBe(true);
    expect(b.read).toBe(false);
    expect(store.unreadCount).toBe(1);
  });

  it('test_markRead_unknown_id_noop', () => {
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'A' }));
    expect(store.unreadCount).toBe(1);
    store.markRead('nonexistent');
    expect(store.unreadCount).toBe(1);
  });

  it('test_markRead_already_read_noop', () => {
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'A', read: true }));
    expect(store.unreadCount).toBe(0);
    store.markRead('A');
    expect(store.unreadCount).toBe(0);
    expect(store.notifications[0].read).toBe(true);
  });

  it('test_unreadCount_reactive_on_push', () => {
    const store = useUserHubStore();
    expect(store.unreadCount).toBe(0);
    store.pushNotification(makeItem({ id: 'A' }));
    expect(store.unreadCount).toBe(1);
    store.pushNotification(makeItem({ id: 'B' }));
    expect(store.unreadCount).toBe(2);
  });

  it('test_hasUnread_computed', () => {
    const store = useUserHubStore();
    expect(store.hasUnread).toBe(false);
    store.pushNotification(makeItem({ id: 'A' }));
    expect(store.hasUnread).toBe(true);
    store.markRead('A');
    expect(store.hasUnread).toBe(false);
  });

  it('test_reset_clears_notifications', () => {
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'A' }));
    store.pushNotification(makeItem({ id: 'B' }));
    store.pushNotification(makeItem({ id: 'C' }));
    expect(store.notifications.length).toBe(3);
    store.reset();
    expect(store.notifications.length).toBe(0);
    expect(store.unreadCount).toBe(0);
    expect(store.hasUnread).toBe(false);
  });
});

describe('userHub store — assignments slice (Phase 3)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    api.get.mockReset();
  });

  it('test_initial_assignments_state', () => {
    const store = useUserHubStore();
    expect(store.jobs).toEqual({ assigned: [], unassigned: [] });
    expect(store.tasks).toEqual([]);
    expect(store.loadingJobs).toBe(false);
    expect(store.loadingTasks).toBe(false);
    expect(store.lastLoadedAt).toEqual({ jobs: null, tasks: null });
  });

  it('test_refreshJobs_populates_assigned_and_unassigned', async () => {
    api.get.mockResolvedValueOnce({
      data: {
        detail: {
          assigned_jobs_by_operator: [{ assigned_jobs: [{ _key: 'j1' }, { _key: 'j2' }] }],
          unassigned_jobs: [{ _key: 'j3' }],
        },
      },
    });
    const store = useUserHubStore();
    await store.refreshJobs('u1');
    expect(api.get).toHaveBeenCalledWith('/job-assignment', { params: { user_key: 'u1' } });
    // Store stamps `assigned: true/false` so JobCard can render the right icon.
    expect(store.jobs.assigned).toEqual([
      { _key: 'j1', assigned: true },
      { _key: 'j2', assigned: true },
    ]);
    expect(store.jobs.unassigned).toEqual([{ _key: 'j3', assigned: false }]);
    expect(store.lastLoadedAt.jobs).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(store.loadingJobs).toBe(false);
  });

  it('test_refreshJobs_handles_empty_operators_array', async () => {
    api.get.mockResolvedValueOnce({
      data: { detail: { assigned_jobs_by_operator: [], unassigned_jobs: [] } },
    });
    const store = useUserHubStore();
    await store.refreshJobs('u1');
    expect(store.jobs.assigned).toEqual([]);
    expect(store.jobs.unassigned).toEqual([]);
  });

  it('test_refreshJobs_clears_loading_on_reject', async () => {
    api.get.mockRejectedValueOnce(new Error('network'));
    const store = useUserHubStore();
    await store.refreshJobs('u1').catch(() => {});
    expect(store.loadingJobs).toBe(false);
  });

  it('test_refreshTasks_populates_tasks', async () => {
    const taskData = [{ _key: 't1', title: 'A' }, { _key: 't2', title: 'B' }];
    api.get.mockResolvedValueOnce({ data: taskData });
    const store = useUserHubStore();
    await store.refreshTasks('u1');
    expect(api.get).toHaveBeenCalledWith('/task', { params: { assigned_to: 'u1' } });
    expect(store.tasks).toEqual(taskData);
    expect(store.lastLoadedAt.tasks).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(store.loadingTasks).toBe(false);
  });

  it('test_refreshTasks_clears_loading_on_reject', async () => {
    api.get.mockRejectedValueOnce(new Error('network'));
    const store = useUserHubStore();
    await store.refreshTasks('u1').catch(() => {});
    expect(store.loadingTasks).toBe(false);
  });

  it('test_loadAssignments_calls_both_in_parallel', async () => {
    api.get
      .mockResolvedValueOnce({ data: { detail: { assigned_jobs_by_operator: [], unassigned_jobs: [] } } })
      .mockResolvedValueOnce({ data: [] });
    const store = useUserHubStore();
    await store.loadAssignments('u1');
    expect(api.get).toHaveBeenCalledTimes(2);
    expect(api.get).toHaveBeenCalledWith('/job-assignment', { params: { user_key: 'u1' } });
    expect(api.get).toHaveBeenCalledWith('/task', { params: { assigned_to: 'u1' } });
  });

  it('test_refreshAssignments_is_alias_for_loadAssignments', async () => {
    api.get
      .mockResolvedValueOnce({ data: { detail: { assigned_jobs_by_operator: [], unassigned_jobs: [] } } })
      .mockResolvedValueOnce({ data: [] });
    const store = useUserHubStore();
    await store.refreshAssignments('u1');
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('test_reset_clears_assignments_and_notifications', () => {
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'X' }));
    store.jobs.assigned = [{ _key: 'j1' }];
    store.tasks = [{ _key: 't1' }];
    store.lastLoadedAt.jobs = '2026-01-01T00:00:00Z';
    store.reset();
    expect(store.notifications.length).toBe(0);
    expect(store.jobs).toEqual({ assigned: [], unassigned: [] });
    expect(store.tasks).toEqual([]);
    expect(store.lastLoadedAt).toEqual({ jobs: null, tasks: null });
  });

  it('test_phase2_exports_preserved', () => {
    const store = useUserHubStore();
    expect(store.pushNotification).toBeTypeOf('function');
    expect(store.markRead).toBeTypeOf('function');
    expect(store.reset).toBeTypeOf('function');
    expect(store.notifications).toBeDefined();
    expect(store.unreadCount).toBeDefined();
    expect(store.hasUnread).toBeDefined();
  });

  it('test_assignment_actions_do_not_touch_notifications', async () => {
    api.get.mockResolvedValueOnce({ data: { detail: { assigned_jobs_by_operator: [], unassigned_jobs: [] } } });
    const store = useUserHubStore();
    store.pushNotification(makeItem({ id: 'N1' }));
    expect(store.notifications.length).toBe(1);
    await store.refreshJobs('u1');
    expect(store.notifications.length).toBe(1);
  });

  // Regression: the SSE `job_data` payload built by
  // backend/api/events/production/base_production.py::_build_event_payload
  // must carry the same `issues_open` / `issues_total` / `due_by` fields the
  // initial list load returns, because applyJobUpdate shallow-merges the
  // payload over the cached job. If the payload omits them (or carries them
  // as null) the job card renders empty counts.
  it('test_applyJobUpdate_carries_issue_counts_from_SSE_payload', () => {
    const store = useUserHubStore();
    store.jobs = {
      assigned: [{ _key: 'j1', stage: 'running', issues_open: 2, issues_total: 5, assigned_to: 'u1' }],
      unassigned: [],
    };
    store.applyJobUpdate(
      { _key: 'j1', stage: 'paused', issues_open: 3, issues_total: 5, assigned_to: 'u1' },
      'u1',
    );
    expect(store.jobs.assigned[0]).toMatchObject({
      _key: 'j1',
      stage: 'paused',
      issues_open: 3,
      issues_total: 5,
    });
  });

  it('test_applyJobUpdate_preserves_fields_not_in_payload', () => {
    const store = useUserHubStore();
    store.jobs = {
      assigned: [{ _key: 'j1', stage: 'running', issues_open: 2, issues_total: 5, assigned_to: 'u1' }],
      unassigned: [],
    };
    // Payload omits issue counts (pre-fix backend shape).
    store.applyJobUpdate(
      { _key: 'j1', stage: 'paused', assigned_to: 'u1' },
      'u1',
    );
    // Cached counts must survive — the store does additive merge, not replace.
    expect(store.jobs.assigned[0]).toMatchObject({
      _key: 'j1',
      stage: 'paused',
      issues_open: 2,
      issues_total: 5,
    });
  });
});
