export const release_style = {

  // title: `Modalità rilascio`,
  type: `select`,
  values: ['continuous','release_batch', 'job'],

    // ['session', {
    //   name: `Sessione di lavoro`,
    //   description: `I prodotti sono resi disponibili alla fase a valle o a magazzino alla fine della sessione di lavoro (es. fine turno).`
    // }],

    // ['manual', {
    //   name: `Manuale`,
    //   description: `I prodotti di una fase già dichiarati diventano disponibili alla fase a valle quando segnalato dall'operatore tramite pulsante "RILASCIA"`
    // }],
}


export const step_check = {

  // title: `Lotto di controllo`,
  type: 'select',
  values: ['none', 'fixed_batch', 'job']

    // ['single', {
    //   name: `Passo singolo`,
    //   description: `A fine procedura viene dichiarata la produzione di un singolo pezzo.`
    // }],

    // ['manual_batch', {
    //   name: `Lotto manuale`,
    //   description: `A fine procedura viene dichiarata la produzione di un lotto di produzione definito di volta in volta dall'operatore.`
    // }],
}


export const parallel_job_allowed = {
  // title: `Lavoro in parallelo`,
  type: 'bool',
  values: [true, false]
}


export const step_check_force_order = {
  // title: `Sequenza passi obbligata *`,
  type: 'bool',
  values: [true, false]
}

export const production_batch_qt = {
  // title: `Lotto di produzione`,
  type: `int`
}

export const release_batch_qt = {
  // title: `Lotto di rilascio`,
  type: `int`
}

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
  production_batch_qt,
  // release_batch_qt,
  // wip_flow
}