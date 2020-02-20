export const release_style = {

  title: `Modalità rilascio`,
  type: `select`,
  values: new Map([

    ['continuous', {
      value_name: `Continua`,
      value_desc: `Tutti i prodotti di questa fase sono immediatamente disponibili alla fase successiva o a magazzino al momento della dichiarazione di produzione.`
    }],

    ['batch', {
      value_name: `Lotto`,
      value_desc: `I prodotti di una fase sono disponibili alla fase successiva o a magazzino dopo la produzione di una quantità prefissata definita nel parametro "Lotto di rilascio". Tale quantità è valida per tutto il lavoro, con l'eccezione dell'ultimo rilascio, che potrebbe essere inferiore al lotto definito`
    }],

    ['session', {
      value_name: `Sessione di lavoro`,
      value_desc: `I prodotti sono resi disponibili alla fase a valle o a magazzino alla fine della sessione di lavoro (es. fine turno).`
    }],

    ['manual', {
      value_name: `Manuale`,
      value_desc: `I prodotti di una fase già dichiarati diventano disponibili alla fase a valle quando segnalato dall'operatore tramite pulsante "RILASCIA"`
    }],

    ['job', {
      value_name: `Lavoro`,
      value_desc: `I prodotti sono rilasciati solo a completamento del lavoro`
    }]
  ])
}


export const step_check = {

  title: `Controllo passi`,
  type: 'select',
  values: new Map([
    ['none', {
      value_name: `Nessuno`,
      value_desc: `Nessun controllo step. Eventuali procedure registrate vengono utilizzate solo a scopo di consultazione per l'utente, senza nessun tracciamento o vincolo. È l'operatore che decide quando dichiarazione la produzione dei pezzi.`
    }],

    ['single', {
      value_name: `Passo singolo`,
      value_desc: `A fine procedura viene dichiarata la produzione di un singolo pezzo.`
    }],

    ['fixed_batch', {
      value_name: `Lotto fisso`,
      value_desc: `A fine procedura viene dichiarata la produzione di un lotto di avanzamento fisso, definito nel parametro "Quantità lotto di produzione".`  
    }],

    ['manual_batch', {
      value_name: `Lotto manuale`,
      value_desc: `A fine procedura viene dichiarata la produzione di un lotto di produzione definito di volta in volta dall'operatore.`
    }],

    ['job', {
      value_name: `Lavoro`,
      value_desc: `A fine procedura viene dichiarata la produzione dell'intera quantità pianificata per il lavoro (lavoro a ciclo unico).`
    }]
  ])
}


export const parallel_job_allowed = {
  title: `Lavoro in parallelo`,
  type: 'bool',
  values: new Map([
    [true, {
      value_name: `Autorizzato`,
      value_desc: `In questa fase è possibile creare più lavori per un dato Ordine di Produzione, che possono essere eseguiti in parallelo da più operatori.`
    }],

    [false, {
      value_name: `Non autorizzato`,
      value_desc: `Questa fase deve essere eseguita in un unico lavoro.`
    }]
  ])
}


export const step_check_force_order = {
  title: `Sequenza passi obbligata`,
  type: 'bool',
  values: new Map([
    [true, {
      value_name: `Sì`,
      value_desc: `I passi possono essere validati solo nella sequenza indicata.`
    }],

    [false, {
      value_name: `No`,
      value_desc: `Ciascun passo può essere validato in maniera autonoma dagli altri.`
    }]
  ])
}

export const production_batch_qt = {
  title: `Lotto di produzione`,
  type: `int`,
  description: `Quantità di avanzamento produzione a fine ciclo. Questo parametro ha efficacia solo se il controllo passi è impostato con valore "Lotto fisso" o "Lotto variabile". Nel caso di lotto fisso, la quantità indicata non può essere modificata dall'operatore ed è valida per tutto il lavoro, con l'eccezione dell'ultimo rilascio, che potrebbe essere inferiore al lotto definito. Nel caso di lotto variabile, la quantità indicata è quella che il sistema propone all'operatore.`
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
      value_name: `Linea`,
      value_desc: `Ciascun lavoro in questa fase rilascia semilavorati per uno solo dei lavori a valle.`
    }],

    ['buffer', {
      value_name: `Magazzino di fase`,
      value_desc: `I semilavorati rilasciati da questa fase confluiscono in un unico raggruppamento virtuale, a cui i lavori della fase successiva (se esistente) attingono liberamente.`
    }]
  ])
}
*/

export default {
  release_style,
  step_check,
  step_check_force_order,
  parallel_job_allowed,
  production_batch_qt,
  release_batch_qt,
  // wip_flow
}