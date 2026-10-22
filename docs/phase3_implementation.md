# Fase 3 — simulatore C e verifiche

Data: 2026-10-22. Implementati caso controllato e rete del contratto di Fase 2.
Le esecuzioni conservate sono verifiche e conferma del gate, non pilota o produzione.
Il gate 3.8 è accettato secondo la versione 1.1 e il perimetro dichiarato.

Aggiornamento del gate 3.8: dopo la diagnosi v1 (384 repliche, 634 controlli
inconcludenti), eseguita la [conferma indipendente v1.1](gate38_confirmation_protocol.md)
con 672 nuove repliche per caso, 8064 totali. [Esito dettagliato](../reports/gate38_results.md):
8904 asserti superati, zero non superati e zero inconcludenti; requisiti esatti
superati e tutti gli obiettivi di semiampiezza entro metà margine raggiunti.
Le 384 repliche di pianificazione non entrano negli IC finali.
[Piano e diagnosi mirata](../reports/gate38_confirmation_plan.md) e
[report storico v1](../reports/gate38_v1_results.md) sono conservati separatamente.
La validazione empirica resta limitata dai dati; l'analisi del transitorio resta Fase 4.

## Riproduzione

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Analyze
python scripts/verify_controlled.py
python scripts/verify_network.py
python scripts/gate38.py
python scripts/gate38.py --criteria configs/gate38_confirmation.json --exe build/release/rome_bus_pmcsn.exe --output-dir data/processed/phase3/REPRODUCTION_NEW_DIRECTORY
python scripts/export_simulation.py --scenario BASE --output data/processed/phase3/base.txt
./build/debug/rome_bus_pmcsn.exe simulate network data/processed/phase3/base.txt --trace data/processed/phase3/base.csv > data/processed/phase3/base.jsonl
./build/debug/rome_bus_pmcsn.exe validate controlled
```

La build non richiede Python. Gli strumenti di preparazione e confronto usano
Python 3.11+ e sola libreria standard, senza rete. Per una toolchain CLion in
altra posizione passare `-ClionRoot PATH` allo script di build.
`--loaded` nell'export sceglie lo stato caricato; sono ammessi tutti i sei scenari.
`simulate network INPUT --replicas N` continua gli stream fra repliche.
Invocazioni separate ripartono dal seed: prima della Fase 5 serve un runner
che continui gli stati anche fra scenari e fra pilota e produzione.
Il batch diagnostico del gate continua già gli stati fra casi, ma non esegue
dimensionamento pilota/produzione, checkpoint o ripartenze della Fase 5.

`validate network INPUT` esegue gli stessi controlli e bilanci del simulatore;
non certifica validazione empirica. Output JSONL su stdout, errori su stderr e
codice non zero. Le tracce sono create esclusivamente come file nuovi. Un errore
può lasciare una traccia incompleta: usare risultati solo con codice di uscita zero.

## Architettura e proprietà

`calendar.c` è un min-heap ordinato per tempo, priorità, linea, direzione, corsa,
sequenza, passeggero e seriale. Stringhe e payload degli eventi sono presi in
prestito: il chiamante li conserva fino alla distruzione del calendario.
`network.c` possiede e libera code, bus, visite, passeggeri, tabella ambientale
e calendario della replica, anche in caso di errore. I collegamenti fra persone
usano indici affinché reallocazioni non invalidino riferimenti.

Priorità: arrivi passeggeri 1, completamenti 2, arrivi bus 3, partenze programmate 4,
decisioni/ingresso nel tratto 5, osservazioni senza effetti 6. L'arresto a priorità
0 è implementato escludendo gli eventi a `t >= T` e integrando fino a T.
Completamenti e selezioni successive sono eventi distinti, senza epsilon.
La prenotazione esclusiva di persona e posto dura fino alla salita completata;
la persona resta nella coda fino a quel momento. Le discese precedono le salite.
I bus possono sorpassarsi; non esistono stalli contesi, trasbordi o ricircolo.
I secondi oltre 86400 non sono ridotti modulo 24 ore.

OD estratte all'arrivo fra stop distinti del supporto; all'imbarco si sceglie
la prima visita futura ammissibile della corsa effettiva. Gli iniziali a bordo
mantengono la visita di destinazione specificata nel JSON congelato.
Eventi al limite esclusi, nessun drenaggio, nessun warm-up automatico.

Input non finiti, allocazioni fallite, I/O, bilanci violati, budget RNG e tempi
sotto la risoluzione numerica provocano errore, senza correzioni silenziose.
Limiti controllati: 4096 code/bus, 256 visite/destinazioni, identificativi di
95 byte, capacità 10000, fino a un milione di iniziali o arrivi di fixture.

## Input e provenienza

L'export verifica gli hash di trips, scenari sintetici, stati iniziali e viaggi
contro il congelamento di Fase 2. Non modifica quel congelamento. Il proprio
manifest contiene hash, scenario, inizializzazione e indici di code/corse/stop.
`configs/simulation.yaml` rimane lo snapshot storico della specifica Fase 2:
non è letto direttamente dalla nuova CLI.

PMNET1 usa record separati da whitespace, indici da zero, senza commenti:

```text
PMNET1 start end cv shared_boolean
number_of_queues number_of_buses
route direction stop_index destination_count destination_indices... rate_0 ... rate_7
route direction trip capacity visit_count first_visit first_time origin_boolean
stop_index stop_sequence pickup_boolean dropoff_boolean reference_travel shared_arc_or_dash
number_of_initial_passengers
onboard_boolean bus_or_queue_index destination_stop_index destination_visit arrival_time
D number_of_fixed_arrivals
queue_index destination_stop_index arrival_time
```

Ripetere il record di coda per tutte le code, il blocco bus/visite per tutti i
bus, e i record passeggeri per i rispettivi conteggi. La sezione D è facoltativa
e serve alle fixture deterministiche. `destination_visit` è ignorata in coda.
Otto tassi in fasce da 1800 s; finestre fino a 14400 s. Soste congelate 2/1/2/3 s:
l'export rifiuta coefficienti diversi. REGULAR usa CV zero. Gli input voluminosi
e le tracce restano in `data/processed/phase3`, ignorati da Git e rigenerabili.

## RNG: revisione prima degli esperimenti

Il controllato conserva il candidato Lehmer accademico: a=48271, m=2147483647,
jump 22925, budget cumulativo strettamente minore di 8367782 per stream.
TestRandom con seed 1 e 10000 estrazioni termina nello stato 399268537.
Si conta anche l'estrazione che oltrepassa l'orizzonte.

La prima prova BASE con Lehmer consumava 76789 uniformi per gli arrivi. La
proiezione indicativa `240 * 76789 = 18429360` supera lo spazio fra stream.
Si è quindi applicata la sostituzione prevista dal protocollo prima di pilota
e produzione: la rete usa MRG32k3a di L'Ecuyer, periodo circa 2^191, con 256
stream separati dai salti pubblicati di 2^127. Non è un PRNG nuovo.

La radice 123456789 produce un vettore iniziale con sei componenti uguali;
gli altri stream derivano solo dai salti. Stream 0 arrivi, 1 OD, 2 ambiente
indipendente, 3 condiviso. Nessuna estrazione per lo stato iniziale deterministico.
Il contatore a 64 bit arresta ogni stream prima dell'overflow, molto prima di
2^127. Tutte le sei componenti e i consumi di tutti gli stream sono salvati.
I prodotti modulari e le ricorrenze C17 sono valutati entro i limiti a 64 bit.

Fonti primarie consultate per ricorrenze, costanti e salti:
[RngStreams degli autori](https://github.com/umontreal-simul/RngStreams),
[sorgente di riferimento](https://raw.githubusercontent.com/umontreal-simul/RngStreams/master/src/RngStream.cpp),
[documentazione SSJ](https://umontreal-simul.github.io/ssj/docs/master/classumontreal_1_1ssj_1_1rng_1_1MRG32k3a.html).
Riferimenti: L'Ecuyer, Operations Research 47(1), 1999; L'Ecuyer, Simard, Chen,
Kelton, Operations Research 50(6), 2002. Non si dichiara lettura integrale degli articoli.

Box–Muller usa due uniformi per fattore nuovo senza conservare la seconda normale.
Ogni fattore è riusato per chiave nella replica; il bin dipende dalla partenza
effettiva. Dominio geometrico e chiavi seguono il contratto. Nessun troncamento.

## Evidenze di verifica

CTest: RNG/calendario, ordinamento completo dei pareggi, capacità, bilanci,
domanda nulla, input invalidi, sovraccarico, riproducibilità. Fixture di rete:
arrivo al completamento della discesa, bus simultanei con prenotazioni distinte,
arrivo al completamento della chiusura, salita incompleta a T, orari oltre
mezzanotte. Esiti calcolati a mano. Build anche con GCC `-fanalyzer`, warning
come errori. Non si dichiara una prova formale di correttezza.

`reports/phase3_controlled_checks.json`: 1000 repliche per ognuno dei tassi
0.2, 0.8, 1.2 con h=10, c=10, T=200. Serie finita di Spitzer calcolata in modo
indipendente in Python con somme positive e limite geometrico del troncamento
Poisson. Bus a T escluso: E[Q(T)] = E[X_19]+lambda*h; media temporale = media
di E[X_0],...,E[X_19] più lambda*h/2. Tolleranza diagnostica sei errori standard,
non IC di produzione. I tre confronti passano; su ogni traiettoria integrale
della coda = somma delle attese limitate, compresi i residui.

`reports/phase3_network_checks.json`: quattro repliche vuote e una caricata per
ognuno dei sei scenari; ripetizione tracciata della prima replica. Controlli di
conservazione per coorte, capacità, continuità degli stream e riproducibilità
con/senza traccia. Le inizializzazioni di tutti i 256 stream sono confrontate
con salti ricalcolati indipendentemente tramite interi arbitrari Python.
Le campagne separate ripetono la radice: non si calcolano contrasti indipendenti
fra scenari. Non sono le 40 repliche pilota. Tempi wall-clock nel report,
inclusi avvio e serializzazione; non sono benchmark generalizzabili.

## Misure e validazione limitata

JSON globale: arrivi della coorte, salite completate, non serviti, attese limitate,
integrale coda, viaggi completati, carico e persone riservate. Coorte vuota:
`mean_wait: null`. Per coda: conteggi e integrali distinti per coorte, negati per
evento e persona della coorte primaria, numerosità/somma/somma quadrati degli
headway. Gli indici nel manifest permettono aggregazione per linea. CV headway
campionario solo con almeno due intervalli e media positiva, senza mescolare stop.

Tempi a bordo solo per viaggi completati con salita nota, senza inventare il
passato degli iniziali a bordo o stimare la media incondizionata dagli usciti.
CSV: visite, fattori effettivamente selezionati, code, integrali e conteggi
cumulativi ogni 300 s, occupazioni dei bus attivi e fotografia delle code a T.
JSON finale per bus: visita, attività, fase, occupazione, capacità e integrale
esatto dell'occupazione (passeggeri-secondi). Fasi: 1 arrivo,
2 origine, 3 apertura, 4 discesa, 5 salita, 6 chiusura, 7 decisione, 8 viaggio.

Momenti dei fattori selezionati, inclusi i riusi: le prime tolleranze smoke
0.02 sulla media e 0.03 sul CV della prima replica passavano ma non bastavano
all'accettazione. La conferma v1.1 ora verifica su statistiche di replica tutti
gli asserti prefissati, con IC simultanei e medesimi margini: tutti superati.
L'accettazione riguarda le marginali aggregate alla griglia CDF dichiarata e
le medie dei tempi per arco, non identità esatta di ogni distribuzione o code estreme.
Nessuna tolleranza è stata allargata sulla base dei risultati.

Le formule stazionarie della tratta senza dwell non sono applicate alla rete
con sosta dipendente dal carico. Il riferimento analitico indipendente eseguito
è la fermata controllata finita; bilanci e fixture verificano l'estensione operativa.
Nessun dato indipendente disponibile calibra o valida domanda, OD o tempi reali:
la plausibilità è condizionata agli scenari sintetici. L'audit GTFS verifica il
calendario, non i passeggeri reali. L'analisi del transitorio resta Fase 4.
