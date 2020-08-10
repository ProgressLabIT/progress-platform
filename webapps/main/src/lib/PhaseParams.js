export const release_style = {

  title: `Modalità rilascio`,
  type: `select`,
  values: new Map([

    ['continuous', {
      name: `Continua`,
      description: `Tutti i prodotti di questa fase sono immediatamente disponibili alla fase successiva o a magazzino al momento della dichiarazione di produzione.`
    }],

    ['release_batch', {
      name: `Lotto di rilascio`,
      description: `I prodotti di una fase sono disponibili alla fase successiva o a magazzino dopo la produzione di una quantità prefissata definita nel parametro "Lotto di rilascio". Tale quantità è valida per tutto il lavoro, con l'eccezione dell'ultimo rilascio, che potrebbe essere inferiore al lotto definito`
    }],

    // ['session', {
    //   name: `Sessione di lavoro`,
    //   description: `I prodotti sono resi disponibili alla fase a valle o a magazzino alla fine della sessione di lavoro (es. fine turno).`
    // }],

    // ['manual', {
    //   name: `Manuale`,
    //   description: `I prodotti di una fase già dichiarati diventano disponibili alla fase a valle quando segnalato dall'operatore tramite pulsante "RILASCIA"`
    // }],

    ['job', {
      name: `Lavoro`,
      description: `I prodotti sono rilasciati solo a completamento del lavoro`
    }]
  ])
}


export const step_check = {

  title: `Lotto di controllo`,
  type: 'select',
  values: new Map([
    ['none', {
      name: `Nessuno`,
      description: `Nessun controllo dei passi. Eventuali procedure registrate vengono mostrate a scopo puramente illustrativo per l'utente, senza nessun tracciamento o vincolo. È l'operatore che decide quando dichiarazione la produzione dei pezzi.`
    }],

    // ['single', {
    //   name: `Passo singolo`,
    //   description: `A fine procedura viene dichiarata la produzione di un singolo pezzo.`
    // }],

    ['fixed_batch', {
      name: `Lotto fisso`,
      description: `I passi della procedura vengono considerati come eseguiti in contemporanea su un numero fisso di prodotti definito nel parametro "Lotto di Produzione". Al completamento di tutti i passi viene dichiarata conclusa la produzione dell'intero lotto.`  
    }],

    // ['manual_batch', {
    //   name: `Lotto manuale`,
    //   description: `A fine procedura viene dichiarata la produzione di un lotto di produzione definito di volta in volta dall'operatore.`
    // }],

    ['job', {
      name: `Lavoro`,
      description: `I passi della procedura vengono considerati come eseguiti in contemporanea su tutti i pezzi pianificati per il lavoro in corso. Al completamento di tutti i passi viene dichiarata conclusa la produzione di tutti i pezzi previsti (lavoro a ciclo unico).`
    }]
  ])
}


export const parallel_job_allowed = {
  title: `Lavoro in parallelo`,
  type: 'bool',
  values: new Map([
    [true, {
      name: `Autorizzato`,
      description: `In questa fase è possibile creare più lavori per un dato Ordine di Produzione, che possono essere eseguiti in parallelo da più operatori.`
    }],

    [false, {
      name: `Non autorizzato`,
      description: `Questa fase deve essere eseguita in un unico lavoro.`
    }]
  ])
}


export const step_check_force_order = {
  title: `Sequenza passi obbligata *`,
  type: 'bool',
  values: new Map([
    [true, {
      name: `Sì`,
      description: `I passi possono essere validati solo nella sequenza indicata. (* Valido solo con lotto di controllo)`
    }],

    [false, {
      name: `No`,
      description: `Ciascun passo può essere validato in maniera autonoma dagli altri. (* Valido solo con lotto di controllo)`
    }]
  ])
}

export const production_batch_qt = {
  title: `Lotto di produzione`,
  type: `int`,
  description: `Quantità di avanzamento produzione a fine ciclo. Questo parametro ha efficacia solo se il controllo passi è impostato con valore "Lotto fisso". Nel caso di lotto fisso, la quantità indicata non può essere modificata dall'operatore ed è valida per tutto il lavoro, con l'eccezione dell'ultimo rilascio, che potrebbe essere inferiore al lotto definito.`
}

export const release_batch_qt = {
  title: `Lotto di rilascio`,
  type: `int`,
  description: `Quantità di rilascio semilavorati/prodotti finiti. Questo parametro ha efficacia solo se la modalità di rilascio è impostata con valore "Lotto fisso" o "Lotto variabile". Nel caso di lotto fisso, la quantità indicata non può essere modificata dall'operatore ed è valida per tutto il lavoro, con l'eccezione dell'ultimo rilascio, che potrebbe essere inferiore al lotto definito. Nel caso di lotto variabile, la quantità indicata è quella che il sistema propone all'operatore.`
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