# Modello

**Stato corrente, 2026-10-22:** specifica di Fase 2 congelata nel
[contratto operativo](phase2_operational_contract.md), che completa e prevale
sulle note preliminari sotto. Configurazioni in `configs/simulation.yaml` e
`configs/phase2_assumptions.json`; hash in `reports/phase2_freeze.json`.
Rete, domanda, capacità, tempi, ambiente comune, inizializzazione ed eventi
sono definiti. Implementazione e verifiche del simulatore restano in Fase 3.

## Note preliminari del 15–16 ottobre, conservate come cronologia

Variabilità del viaggio: [lognormale a media nominale preservata e CV 0,2](travel_time_model.md),
valore di lavoro sintetico. REGULAR usa tempi di riferimento deterministici.
Il dominio condiviso e i controlli delle marginali sulle traiettorie restano aperti.

Input estratti e ipotesi numeriche iniziali:
[estrazione offline e bozza sintetica di Fase 2](phase2_inputs.md).
La bozza non chiude le decisioni operative ancora aperte.

Formulazioni per la verifica della tratta in regime stabile:
[caso non sovraccarico con posti disponibili variabili](non_overloaded_route_formulas.md).

Formulazione della dinamica della rete: [modello completo con disponibilità
dei posti determinata da occupazione e discese](network_queue_model.md).
Prima specifica matematica; parametri e decisioni operative ancora aperti.

Riferimento matematico per la verifica: [caso controllato a una fermata con
servizio periodico e posti disponibili fissi](controlled_queue_model.md).
Include coda residua, medie stazionarie e confronto finito da stato vuoto;
non sostituisce la specifica della rete completa.

## Decisioni sul passeggero e sulla domanda — 2026-10-15

Aggiornamento tempi: decomposizione concordata con sosta sintetica di riferimento
di 15 secondi, sottratta da ogni gap programmato fra fermate. La sosta effettiva
dipendente dai passeggeri sostituisce quella di riferimento: apertura 2 s,
discese 1 s/persona, salite 2 s/persona, chiusura 3 s, in sequenza.
Nessuna sosta senza discese o persone compatibili in attesa all'arrivo.
Dettagli e convenzioni in [phase2_inputs.md](phase2_inputs.md).

Specifica parziale concordata; valori numerici ancora aperti. Le regole sono
ipotesi dello studio, non comportamenti misurati.

- Ogni passeggero sceglie prima dell'arrivo linea, direzione e destinazione.
  Una coda logica per `(stop_id, linea, direzione)`; nessun cambio di linea,
  trasbordo o abbandono. Una persona occupa un posto.
- Le varianti condividono la coda. Ogni bus serve in ordine FIFO i passeggeri
  con destinazione successiva raggiungibile dalla corsa. Gli incompatibili
  non bloccano gli altri e non subiscono un imbarco negato per capacità.
  Chi resta per bus pieno conserva la posizione.
- Discese prima delle salite. Chi arriva durante l'imbarco può salire se
  compatibile e se c'è posto, contribuendo al tempo di sosta. L'imbarco termina
  a coda compatibile vuota o bus pieno; nessuna salita durante la chiusura porte.
  Partenze dai capolinea agli orari GTFS con mezzo dedicato per corsa, senza
  ricircolo; tutti scendono al capolinea finale e la corsa termina.
  Finestra di imbarco iniziale, completamento della discesa finale e precedenze
  degli eventi simultanei ancora da specificare.
- Informazioni concettuali: identificativo, origine, linea, verso,
  destinazione, arrivo, stato, corsa utilizzata, salita, discesa e imbarchi negati.
- Arrivi base: Poisson con intensità costante per coda dentro ciascuna fascia
  di 30 minuti; otto fasce fra 07:00 e 11:00. Tassi e dipendenza fra code da
  definire. La generazione deve rispettare il cambio di tasso ai confini.
- Destinazioni uniformi tra le fermate successive ammissibili. Formalizzazione
  per varianti e fermate ripetute ancora aperta; non generare passeggeri senza
  destinazioni ammissibili. Distribuzione configurabile per confrontare in
  seguito pesi di attrattività e poli. L'uniforme sostiene la verifica iniziale,
  non dimostra validità rispetto alla domanda reale.
- Conservare come estensione gli arrivi coordinati con gli orari programmati,
  eventualmente miscelati agli spontanei; legge e parametri ancora aperti.
  Confrontare concentrazioni temporali a uguale domanda totale attesa.
- Chi attende alle 11:00 è non servito entro la finestra; registrarne l'attesa
  maturata secondo il protocollo. Stato iniziale, passeggeri a bordo al termine
  ed eventuale drenaggio ancora da definire.

### Dimensionamento della domanda rispetto alla capacità

Prima assegnazione della flotta concordata: mix sintetico 50–50 fra bus
standard da 12 m e articolati da 18 m. Non è una composizione osservata sulle
linee selezionate; non si approfondisce per ora l'assegnazione reale dei mezzi.
Capacità numeriche delle due classi, metodo di assegnazione alle corse e
applicazione del mix per linea o sull'intero campione ancora da specificare.
Mantenere la stessa assegnazione nelle comparazioni che richiedono servizio e
capacità invariati; generazione e riuso della flotta non devono introdurre
differenze di capacità fra tali scenari.

Usare scenari sintetici di pressione sul servizio, senza presentarli come
stime della domanda reale. Procedura concordata:

1. Fissare capacità dei mezzi, calendario e destinazioni uniformi.
2. Scegliere il profilo relativo di domanda fra code e fasce (ancora aperto).
3. Calcolare il carico medio atteso lungo i percorsi e scegliere livelli bassi,
   prossimi alla capacità e superiori alla capacità nei tratti critici.
   Considerare occupazione in arrivo e discese: la capacità nominale non è
   interamente disponibile a ogni fermata.
4. Controllare nelle prove preliminari occupazione, imbarchi negati e crescita
   delle code; congelare gli input prima degli esperimenti di produzione.

Con Poisson, domanda media bassa non garantisce assenza di imbarchi negati;
domanda alta non implica che ogni corsa lasci persone a terra. Le tre condizioni
sono obiettivi di scenario, non risultati dimostrati. I moltiplicatori
0.75/1/1.25 di `configs/experiments.yaml` restano preliminari e non garantiscono
queste condizioni: riesaminarli e tracciare eventuali revisioni prima delle run.
Nessun valore numerico o simulazione introdotto; Fase 2 ancora aperta.

Riferimento scientifico: sezioni 4–8 di `PMCSN_Roma_Bus_SPEC.md`.
DES e passeggeri non implementati. Nel piano ufficiale aggiornato, Fase 2 per la specifica concettuale e Fase 3 per struct, stato, eventi simultanei, RNG, ownership, bilanci e implementazione. La Fase 4 riguarda l'analisi obbligatoria del transitorio.
