export const release_style = {
  type: `select`,
  values: ['continuous', 'release_batch', 'job'],
};

export const step_check = {
  type: 'bool',
  values: [true, false],
};

export const parallel_job_allowed = {
  type: 'bool',
  values: [true, false],
};

export const display_phase_progress = {
  type: 'bool',
  values: [true, false],
};

export const step_check_force_order = {
  type: 'bool',
  values: [true, false],
};

export const production_batch_qt = {
  type: `int`,
};

export const release_batch_qt = {
  type: `int`,
};

export const max_offline = {
  type: `int`,
};

export const auto_new_batch = {
  type: 'bool',
  values: [true, false],
};

export const std_processing_time = {
  type: 'int',
};

export const unsupervised_work_allowed = {
  type: 'bool',
  values: [true, false],
};

/*
export const wip_flow = {
  title: `Accesso ai semilavorati`,
  type: `select`,
  values: new Map([
    ['line', {
      name: `Linea`,
      description: `Ciascun lavoro in questa fase rilascia semilavorati per uno solo dei lavori a valle.`
    }],

    ['buffer', {
      name: `Magazzino di fase`,
      description: `I semilavorati rilasciati da questa fase confluiscono in un unico raggruppamento virtuale, a cui i lavori della fase successiva (se esistente) attingono liberamente.`
    }]
  ])
}
*/

export default {
  // release_style,
  step_check,
  step_check_force_order,
  parallel_job_allowed,
  display_phase_progress,
  production_batch_qt,
  max_offline,
  auto_new_batch,
  std_processing_time,
  unsupervised_work_allowed,
  // release_batch_qt,
  // wip_flow
};
