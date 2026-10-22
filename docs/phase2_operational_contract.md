# Fase 2 — specifica operativa congelata

Data: 2026-10-22. Questa specifica chiude le decisioni operative della Fase 2
e prevale sulle note preliminari che riportano punti allora aperti.
Parametri in `configs/phase2_assumptions.json`; configurazione di ingresso in
`configs/simulation.yaml`; hash del congelamento in `reports/phase2_freeze.json`.
Il simulatore C non è ancora implementato: verifica, validazione, RNG e
analisi del transitorio rimangono attività delle Fasi 3–4.

## 1. Corse e capolinea

Si conservano tutte le 260 partenze in [07:00,11:00) e le 48 corse già in
viaggio alle 07:00, sulle sei linee dello snapshot del 2026-10-12. Sono
necessarie 16 varianti operative: 15 per le partenze e una ulteriore per una
corsa iniziale della 628. Le altre corse del giorno sono archiviate ma non
entrano in questa esecuzione.

Ogni corsa ha un mezzo dedicato, di capacità assegnata C_k costante. Non si
modellano turni, ricircolo, stalli contesi o blocking stradale. I bus possono
sorpassarsi; l'ordine effettivo dei passaggi emerge dai tempi di percorrenza.

Al capolinea iniziale, all'istante GTFS, si imbarcano istantaneamente i
passeggeri compatibili presenti in FIFO, fino alla capacità, e si parte. Non
si applicano apertura, salita o chiusura delle fermate intermedie. Chi resta
attende il prossimo bus compatibile. La partenza non si anticipa né si ritarda
in base al carico o alla puntualità della corsa precedente.

Dal primo segmento si usa il viaggio di riferimento GTFS meno 15 secondi,
con il fattore dello scenario. Questa convenzione può anticipare il primo
arrivo rispetto al GTFS anche con fattore 1, perché non si effettua una sosta
di riferimento al capolinea prima di partire. È una scelta esplicita del
modello, non una ricostruzione esatta dell'intero orario programmato.

Al capolinea finale nessuno sale. Se ci sono N persone a bordo: apertura di
2 secondi, discesa sequenziale in ordine di registrazione a bordo, 1 secondo
per persona. Ogni viaggio termina al completamento della propria discesa;
la corsa termina dopo l'ultima discesa, senza simulare una chiusura finale
irrilevante a corse successive. Se il mezzo arriva vuoto la corsa termina
all'arrivo. Nessun ritorno è generato implicitamente.

## 2. Fermate intermedie e significato di salita

Si applicano le regole già concordate: salto della fermata senza discese e
senza passeggeri compatibili presenti; altrimenti apertura 2 s, discese
1 s/persona, salite 2 s/persona, chiusura 3 s. Non si attende volontariamente
un futuro passeggero quando la coda compatibile è vuota.

Durante apertura, discese e imbarco i nuovi arrivati si accodano. L'imbarco
termina a bus pieno o coda compatibile vuota. Durante la chiusura non si sale.
Il bus non aspetta l'orario GTFS alle fermate interne: la dinamica procede
dai tempi simulati e dalle soste effettive.

All'inizio del servizio di salita si riservano passeggero e posto. Il
passeggero non può essere selezionato da un altro bus, ma resta contato nella
coda fino al completamento dei 2 secondi. Al completamento lascia la coda,
entra nel conteggio a bordo e termina l'attesa primaria. In questo modello
l'attesa fino alla salita completata include quindi il tempo individuale di
imbarco. Non è una misura della sola attesa prima dell'avvio dell'imbarco.
La capacità impegnata è occupazione più eventuale posto riservato.

Le discese liberano i posti al proprio completamento; le salite iniziano
dopo tutte le discese. I conteggi a bordo cambiano ai completamenti, non
anticipatamente all'arrivo del mezzo. Conservare un flag di prenotazione del
passeggero selezionato per evitare doppi imbarchi con bus simultanei.

Un imbarco negato per capacità si conta quando il bus termina l'imbarco
perché pieno, per ciascun passeggero compatibile ancora in attesa e non già
riservato da un altro bus. Massimo un evento per passeggero e corsa. Gli
arrivi durante la chiusura e le corse incompatibili non sono imbarchi negati
per capacità. Al capolinea iniziale il controllo si applica dopo il lotto
istantaneo. Si conservano sia conteggio eventi sia flag «almeno uno».

## 3. Eventi simultanei

Confrontare prima l'istante, poi questa priorità, poi gli identificativi:

1. Arresto all'orizzonte.
2. Arrivo esogeno di un passeggero.
3. Completamento di apertura/chiusura porte, salita o discesa.
4. Arrivo di un bus a una fermata.
5. Partenza programmata e imbarco istantaneo al capolinea iniziale.
6. Selezione del prossimo servizio, inizio chiusura o partenza verso il tratto.

Le decisioni di fase 6 avvengono dopo tutti gli eventi di priorità superiore
al medesimo istante. Per esempio chi arriva esattamente al completamento
dell'ultima salita può ancora essere selezionato prima della chiusura; chi
arriva al completamento della chiusura resta in coda.

Parità residue: route_id, direction_id, trip_id in ordine lessicografico,
stop_sequence, passenger_id, contatore monotono dell'evento. Campi non
applicabili usano sentinelle documentate nell'implementazione (stringa vuota
per identificativi, -1 per sequenze). Gli identificativi passeggero sono
univoci e assegnati in ordine riproducibile per coda. Non usare epsilon
temporali per alterare l'ordine. Le fasi di completamento e decisione devono
essere separate: non effettuare una selezione anticipata dentro un callback.

## 4. Stato iniziale alle 07:00

Sono definite due modalità sintetiche, con le medesime 48 corse iniziali e
le stesse posizioni di calendario. Non si ricostruisce uno storico reale.

- `empty_passengers`, caso predefinito: code vuote e nessuno sui bus iniziali.
- `loaded_synthetic`, confronto del transitorio: occupazione iniziale di
  ciascun bus pari a floor(0,5 C_k), destinazioni bilanciate deterministicamente
  fra le visite residue con discesa consentita, inclusa la prossima fermata.

Per ciascuna coda caricata si introducono
floor(lambda_prima_fascia_scenario * h_nominale / 2) persone. Le età sono
punti medi equispaziati fra 0 e h_nominale/2; l'ordinamento è dal più anziano.
Le destinazioni iniziali sono bilanciate sul supporto ammissibile. Sono
condizioni deterministiche esplicite, non campioni iid né uno stato di
equilibrio. Non si consumano numeri casuali per costruirle.

L'export dà per ogni bus il segmento programmato, la frazione di avanzamento
e la prossima visita. Il primo arrivo residuo resta all'orario GTFS, senza
estrarre un ritardo per un passato non osservato. Da quell'arrivo si applica
la dinamica ordinaria; un arrivo esattamente alle 07:00 è elaborato all'inizio.

I passeggeri iniziali hanno una coorte separata. Non contribuiscono all'attesa
primaria della coorte entrata in [07:00,11:00), ma contribuiscono a occupazione,
code totali, discese e capacità. Non inventare l'istante di salita passato dei
passeggeri iniziali a bordo. Tracciare separatamente gli integrali per coorte.

Il file `initial_states.json` contiene entrambe le modalità per tutti i sei
scenari. Il confronto vuoto/caricato è un'analisi della Fase 4, non nuovi
risultati già eseguiti o un aumento implicito dei confronti primari.

## 5. Arresto alle 11:00

Si simulano eventi con istante t < 39600 secondi dal giorno di servizio.
Alle 11:00 si aggiornano gli integrali fino al limite e si fotografa lo stato,
senza elaborare gli altri eventi che cadono esattamente al limite. Nessun
drenaggio e nessuna nuova corsa oltre la finestra. Le corse in viaggio sono
residui da registrare, non vengono eliminate retroattivamente dalle statistiche.

Registrare passeggeri in coda, in salita riservata, a bordo e in discesa,
corse residue, occupazioni e conteggi per linea. Una salita ancora in corso
non è completata: il passeggero è non servito entro la finestra e contribuisce
all'attesa limitata fino alle 11:00. Una discesa incompleta resta a bordo.

Per la coorte di arrivi, l'attesa è min(salita_completata, T)-arrivo, o T-arrivo
se non servita. Conservare le convenzioni del protocollo per coorti vuote.
Il tempo completo a bordo è disponibile soltanto per viaggi completati;
non presentare la loro media come stima incondizionata di tutti i viaggi.
Il warm-up configurato è zero: l'eventuale revisione segue lo studio del
transitorio, senza scarti automatici.

## 6. Dominio geometrico condiviso

L'export controlla le shape originali delle corse operative. Per ciascuna
sequenza di fermate si proiettano gli stop sulle polilinee in ordine monotono.
Si confrontano solo tratti con la stessa coppia diretta di stop_id.

Un tratto è ammissibile se entrambe le ancore distano al massimo 60 m dalle
fermate e la lunghezza proiettata è maggiore di 1 m. Due tratti sono compatibili
se il rapporto delle lunghezze è al massimo 1,10 e lo scostamento massimo di
101 punti equispaziati per frazione di lunghezza è al massimo 25 m. Ogni gruppo
richiede compatibilità di tutte le coppie, non solo concatenazione di vicinanze.
La metrica è una proiezione equirettangolare locale a latitudine 42 gradi.

Sono risultati 62 gruppi condivisi fra almeno due linee, coprendo 3.978 dei
9.880 segmenti-corsa operativi. Nessun segmento geometrico è stato rifiutato
per ancore o lunghezza non positiva. I tratti non raggruppati restano esterni
al dominio. È un controllo riproducibile dello snapshot, non un accertamento
del percorso effettivo su strada; soglie e campionamento sono scelte locali.

Per un segmento con shared_arc_id, nel bin ambientale di 300 s:

    indipendente: chiave = (route_id, shared_arc_id, bin)
    condiviso:    chiave = (shared_arc_id, bin).

Fuori dal dominio, entrambi i casi mantengono la chiave
(route_id, from_stop_id, to_stop_id, bin). La mappatura si usa in entrambi
i modelli sullo stesso insieme di segmenti. Fattori lognormali di media 1 e
CV 0,2, riusati per chiave nella replica; F = 1 in REGULAR. Non si cambia
fattore durante il viaggio. Si rappresenta ambiente comune, non congestione
causata dai bus o capacità stradale.

Le marginali della tabella sono identiche per costruzione. Le marginali
effettivamente selezionate dalle traiettorie, la media dei tempi e l'adeguatezza
RNG restano gate della Fase 3 prima degli esperimenti: non sono provate dal
solo congelamento degli input. Se falliscono, rivedere il modello e registrare
una nuova versione prima della produzione.

## 7. Contratto dei parametri e incertezza

| Famiglia | Unità e valore/fonte | Stato |
|---|---|---|
| Rete, sequenze, calendario | Snapshot GTFS del servizio 2026-10-12, hash nel manifest | Osservati nel file programmato |
| Capacità e mix | 109/162 posti; alternanza circa 50–50 per linea-direzione | Classi rappresentative assunte, assegnazioni sintetiche |
| Domanda | Poisson indipendenti, passeggeri/s, otto fasce piatte; target nominale 0,85 | Assunta, non domanda misurata |
| OD | Uniforme su stop_id distinti ammissibili, estratta all'arrivo | Assunta |
| Viaggio base | Gap programmato - 15 s | Derivato con decomposizione assunta |
| Perturbazione | Lognormale media 1, CV 0,2; ambiente 300 s | Assunta, non fit empirico |
| Sosta interna | 2 s apertura + 1 s/D + 2 s/B + 3 s chiusura, o zero se saltata | Assunta |
| Confini | Due stati iniziali espliciti; orizzonte di 14.400 s, senza drenaggio | Scelte dello studio |
| Geometria comune | Shape archiviate e soglie 60 m / 25 m / 1,10 | Verifica geometrica locale, non operativa |

Le fonti delle capacità e i dettagli della domanda sono in `phase2_inputs.md`.
Nessun parametro è dichiarato calibrato. Le ipotesi non hanno un intervallo
di confidenza empirico: i confronti di domanda, REGULAR e dipendenza previsti
studiano alcuni loro effetti. Sono candidati di sensibilità, da pianificare
separatamente, CV 0,1/0,2/0,3, sosta di riferimento 10/15/20 secondi e pesi OD
alternativi. Non presentarli come ulteriori run già prescritte o eseguite.

## 8. Riproduzione e chiusura

Con Python 3.11+ e lo snapshot conservato:

```powershell
python scripts/prepare_phase2.py
python scripts/prepare_shared_geometry.py
python scripts/prepare_phase2_scenarios.py
python scripts/prepare_initial_states.py
python tests/test_phase2_geometry.py
python scripts/audit_phase2_inputs.py
```

Non servono librerie Python esterne, rete o installazioni. I dati voluminosi
restano ignorati da Git; script, configurazioni e report conservano istruzioni,
provenienza e hash per rigenerarli. Non si ridistribuiscono i raw.

L'audit verifica provenienza, copertura, bilanci degli input, dominio geometrico,
destinazioni iniziali, capacità, FIFO e regole finite. Scrive il manifest di
congelamento con hash di configurazioni, specifica, strumenti e dati derivati.
Il progetto usa il percorso GTFS più scenari: collector e fit
realtime sono non applicabili a questa specifica.

La Fase 2 è conclusa come specifica e preparazione degli input. Il passo
successivo è implementare il caso controllato in C e confrontarlo con la
matematica, poi estendere alla tratta e alla rete. Nessun test sugli input
sostituisce verifica/validazione del simulatore o analisi del transitorio.
