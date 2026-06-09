/**
 * Shared visibility gate for jobs in the /user hub.
 *
 * A job is shown only once it is "released" to the floor, which requires BOTH:
 *  - an actionable batch — WIP for the next batch is available
 *    (`next_batch_available`) or a batch is already active (`active_batch_qt`);
 *  - its scheduled start having arrived (`start_from <= now`).
 *
 * This ports the legacy `UserJobs.vue` `showJob()` gate. The rule is duplicated
 * across the hub (rendered list in UserJobsList, count badge + filter-option
 * derivation in UserHubPage), so it lives here to keep every consumer in sync.
 *
 * Legacy semantics preserved deliberately: a null `start_from` becomes
 * `new Date(null)` === epoch 0, which is always in the past — so jobs with no
 * scheduled start date stay visible.
 */
export function isJobReleased(job) {
  const batchAvailable = job.next_batch_available || job.active_batch_qt;
  const startReached = new Date(job.start_from).getTime() <= Date.now();
  return Boolean(batchAvailable) && startReached;
}
