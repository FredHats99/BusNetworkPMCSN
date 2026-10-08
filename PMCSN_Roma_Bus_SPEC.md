# PMCSN · Roma Bus Network
## Specifica progettuale, piano di implementazione e checklist

**Riferimento accademico:** `progetto2526.pdf`, AA 2025/2026, Prof. V. de Nitto Personè (2 pagine). Requisiti e pagine sorgente: `docs/requisiti_ufficiali.md`. **Partecipazione: individuale; presentazione massimo 20 minuti.** C è una scelta dell'utente; raccolta GTFS estesa e algoritmo migliorativo sono scelte locali, non obblighi del PDF per l'individuale.

**Versione:** 1.2 · **Data:** 2026-10-08 · **Stato:** piano individuale riallineato alla specifica ufficiale AA 2025/2026; modello e dati da verificare · **Ambiente target:** C, CMake/CTest; CLion oppure Visual Studio Code.

> **Missione:** costruire un modello prestazionale *data-driven* di una porzione della rete di autobus urbani di Roma, capace di riprodurre il servizio osservato e simulare le code dei passeggeri, per comprendere come congestione, ritardi e irregolarità si propagano e valutare interventi migliorativi.
>
> **Principio scientifico non negoziabile:** un modello che riproduce i ritardi dei mezzi **non** dimostra automaticamente di aver identificato la domanda o le code reali dei passeggeri. Ogni parametro va etichettato come **osservato**, **stimato**, **assunto** o **calibrato**. Distinguere sempre dati misurati, previsioni GTFS-RT e output del simulatore.

---

## 1. Contesto, finalità e criteri di riuscita

Il progetto applica i concetti di *Performance Modeling of Computer Systems and Networks* (PMCSN) a un sistema urbano reale. Per il caso Roma Bus proponiamo una rete di code con nodi interconnessi, capacità finite, server mobili e servizio batch, introducendo classi, routing e feedback quando pertinenti agli obiettivi. La specifica ufficiale richiede uno studio di modellistica e simulazione completo; non impone questa particolare topologia né una dimensione minima della rete.

### 1.1 Domande di ricerca

1. Dove e quando emergono ritardi e irregolarità negli autobus di un sottoinsieme reale della rete romana?
2. In che modo i ritardi si propagano lungo percorsi condivisi e attraverso l'interazione con la domanda alle fermate?
3. In quali condizioni può emergere il *bus bunching* e che conseguenze ha sull'attesa dei passeggeri?
4. Come variano i risultati con capacità dei mezzi, intensità della domanda, tempi di salita/discesa e frequenze?
5. Quali politiche operative (es. *holding*, regolarizzazione degli headway, frequenza modificata) migliorano le prestazioni senza peggiorare sensibilmente altri indicatori?

### 1.2 Ambizioni, in ordine di priorità

- **Modello base proposto:** sottorete GTFS inizialmente di 1–2 linee; parametri da fonti disponibili o scenari dichiarati; simulatore C verificato, validazione motivata, analisi del transitorio ed esperimenti pertinenti. Se si usano misure operative, separare dati di calibrazione e validazione. Il numero di linee non è un minimo ufficiale.
- **Estensione proposta, non requisito ufficiale:** 3–5 linee interconnesse, almeno un segmento o gruppo di fermate condivise; modello esplicito delle code dei passeggeri e della capacità dei veicoli; scenari di domanda con incertezza documentata.
- **Obiettivo avanzato facoltativo:** calibrazione vincolata della domanda con segnali indipendenti (occupazione verificata, salite/discese, indagini o conteggi disponibili); feedback passeggeri↔autobus; ottimizzazione di politiche e analisi di sensibilità.
- **Non promettere:** ricostruzione della vera domanda alle singole fermate o precisione delle code senza misure dirette/indipendenti sufficienti.

### 1.3 Criteri di accettazione finali

- Rete e configurazione replicabili da dati/versioni identificati, non disegnati a mano senza tracciabilità.
- Se prevista una pipeline dati: ETL automatizzata e testata, log degli errori e provenienza dei file.
- Parametri stimati con unità, intervalli/variabilità e metodo dichiarato.
- Simulatore riproducibile con seed, orizzonte, warm-up (quando pertinente), repliche e intervalli di confidenza.
- Verifica e validazione distinte e documentate; se si calibra su misure reali, separazione temporale e confronto con baseline pertinenti.
- Esperimenti progettati rispetto agli obiettivi, con risultati e incertezza quantificata; numero di scenari motivato (il PDF non impone un minimo di tre).
- Analisi obbligatoria del transitorio: comportamento in funzione del tempo, eventuale convergenza e suo istante/intervallo; orizzonte motivato.
- Grafici e tabelle riassuntive sia per il transitorio sia per gli esperimenti.
- Algoritmo migliorativo ed evoluzione del modello con ripetizione dello studio se il progetto è di gruppo.
- Relazione cartacea, codice senza librerie di sistema, presentazione nei limiti ufficiali e disponibilità a esecuzioni dal vivo.
- Limitazioni di identificabilità della domanda documentate, mai nascoste.

---

## 2. Perimetro iniziale e vincoli

**Luogo:** Roma, rete autobus urbana; GTFS statico può includere più operatori e altre modalità: filtrare esplicitamente per `route_type`, `agency_id` e linee selezionate. **Zona e linee definitive:** *da scegliere dopo audit del dataset*, non assumere che 3–5 linee arbitrarie siano adatte.

**Granularità:** unità minima del grafo = fermata direzionale e passaggio di corsa; archi = collegamenti consecutivi tra fermate; possibili risorse condivise = baie/fermate e segmenti/terminali soltanto se i dati consentono di definirne capacità e interferenze. Distinguere una **fermata logica** da una **risorsa a capacità limitata**: non sono automaticamente la stessa cosa.

**Raccolta empirica opzionale, distinta dall'orizzonte simulato richiesto dal docente:** pilota di 48–72 ore per verificare feed e qualità; successivamente circa 4 settimane di osservazioni, includendo ore di punta, fasce morbide, feriali e weekend. Questi intervalli sono proposte locali, non prescrizioni della specifica ufficiale né garanzia di rappresentatività. Definirli solo se necessari agli obiettivi; lo studio a scenari può procedere con ipotesi tracciate anche senza questa campagna. **Non è attivata alcuna raccolta automatica da questo documento:** occorre eseguire il collector su un computer/server con uptime adeguato.

**Timezone:** `Europe/Rome`; conservare gli istanti in UTC e la data di servizio GTFS separatamente. GTFS può usare orari oltre le 24:00; non interpretarli ingenuamente come orologi civili.

**Criteri di esclusione:** nessuna dipendenza da dati ottenibili soltanto tramite email, accessi a pagamento o credenziali non disponibili; documentare chiaramente eccezioni future. Conservare e ridistribuire i dati rispettando licenze, termini d'uso, privacy e limiti tecnici della fonte.

---

## 3. Fonti e stato di disponibilità

| Fonte | Dati attesi | Stato operativo | Limiti / verifica obbligatoria |
|---|---|---|---|
| Roma Servizi per la Mobilità: GTFS statico (`rome_static_gtfs.zip`) | routes, trips, stops, stop_times, shapes, calendari | **Fonte pubblica documentata** | Verificare URL effettivo, risposta HTTP, licenza e file interni; aggiornamenti frequenti |
| GTFS-RT Vehicle Positions (`rome_rtgtfs_vehicle_positions_feed.pb`) | coordinate, vehicle/trip, timestamp e campi opzionali | **Fonte pubblica documentata** | Verificare connettività, copertura, identificatori, aggiornamento e campi effettivamente popolati |
| GTFS-RT Trip Updates (`rome_rtgtfs_trip_updates_feed.pb`) | aggiornamenti/previsioni dei passaggi | **Fonte pubblica documentata** | Una previsione non è un passaggio misurato; controllare `timestamp`, `delay`, `uncertainty` |
| GTFS-RT Service Alerts | deviazioni e perturbazioni | **Fonte pubblica documentata** | Copertura e codifica da verificare |
| Occupazione nei feed GTFS-RT | stato qualitativo o percentuale, **se presente** | **Sperimentale/da verificare** | Non trattare categorie come conteggi; controllare missingness e affidabilità |
| Archivi GTFS statici esterni | versioni precedenti di orari e topologia | **Possibile supporto** | Non sostituiscono uno storico GPS |
| Storico pubblico dei GPS / conteggi fermata OD | movimenti storici e domanda passeggeri | **Non ancora verificato disponibile** | Non assumerne esistenza |

**Fonti primarie da controllare e annotare con data di accesso:**
- Roma Servizi per la Mobilità, Open Data: https://romamobilita.it/sistemi-e-tecnologie/open-data/
- GTFS Schedule Reference: https://gtfs.org/documentation/schedule/reference/
- GTFS Realtime Reference: https://gtfs.org/documentation/realtime/reference/
- GTFS Realtime Trip Updates: https://gtfs.org/documentation/realtime/feed-entities/trip-updates/

**Regola di tracciabilità:** in `data/catalog.yaml` registrare per ogni risorsa URL, autore, licenza verificata, timestamp download, checksum SHA-256, intervallo temporale, schema, copertura e note di qualità. I nomi dei file GTFS-RT indicati sono **nomi pubblicati**, non una promessa che il relativo link possa essere scaricato senza test dell'endpoint.

---

## 4. Modello concettuale: due livelli accoppiati

### 4.1 Livello A · rete operativa degli autobus

- **Entità:** autobus/corse con identificativo di istanza coerente (`trip_id` più service date/start_time ove necessario).
- **Topologia:** sequenza ordinata delle fermate per ciascuna corsa e relativi archi; incroci di linee e fermate condivise.
- **Eventi:** inizio corsa, partenza dal nodo, arrivo al nodo successivo, inizio/fine sosta, termine corsa, eventuale holding o perturbazione.
- **Stato:** posizione/fermata attuale, carico a bordo (quando modellato), ritardo, prossimo evento, headway rispetto al precedente mezzo della stessa linea/direzione.
- **Tempi stocastici:** tempo di viaggio per arco condizionato a fascia oraria/giorno; tempo di sosta ricavato o stimato. Le posizioni GPS campionate **non** garantiscono di osservare direttamente l'istante di arrivo e partenza da ogni fermata.
- **Risorse condivise:** introdurre code vere (es. stallo di fermata occupato) solo quando sia giustificabile capacità, politica di servizio e possibilità di blocking; altrimenti l'arco è un ritardo di viaggio stocastico e **non** una coda arbitraria.

### 4.2 Livello B · rete delle code dei passeggeri

- **Job:** passeggeri; classi per linea/direzione/destinazione o percorso.
- **Nodi:** code logiche alle fermate, con eventuali trasferimenti tra linee.
- **Server:** autobus mobili che servono passeggeri in **batch** all'arrivo, con capienza `C_b`.
- **Routing:** probabilità di destinazione/trasbordo `P_ij`, osservate se disponibili, altrimenti assunte e sottoposte a sensibilità.
- **Ingresso:** processo di arrivo non stazionario `λ_i,c(t)`, anch'esso osservato, stimato o ipotizzato secondo evidenza.
- **Uscita:** discesa dalla rete e trasferimenti; perdita/abbandono solo se modellati esplicitamente.

Per fermata `i` e classe `c`, tra due eventi:

`Q_i,c(t+) = Q_i,c(t-) + A_i,c - B_i,c`

con vincoli `B_i,c ≥ 0`, `Σ_c B_i,c ≤ C_b - O_b(t-)` e regola di priorità/boarding dichiarata. All'arrivo dell'autobus, le discese liberano posti **prima** di determinare la capacità residua per le salite, secondo la politica configurata.

### 4.3 Accoppiamento domanda-servizio

Un modello di prima approssimazione della sosta:

`D_i,b = d0_i + α_i × board_i,b + β_i × alight_i,b + ε_i,b`

Alternativa più aderente alla salita/discesa contemporanea: `D_i,b = d0_i + max(α_i × board_i,b, β_i × alight_i,b) + ε_i,b`. La scelta deve essere verificata tramite dati e analisi di sensibilità. `D ≥ 0` sempre.

**Feedback:** ritardo → headway maggiore → più attesa/accumulo → sosta maggiore → ulteriore ritardo; possibile *bunching* e propagazione alle linee che condividono risorse. Prima di attivare il feedback, validare separatamente i tempi di viaggio di base.

**Limite cruciale:** il solo GTFS-RT non rende osservabili gli arrivi individuali dei passeggeri alle fermate; il fitting della domanda usando solo i ritardi può produrre molte soluzioni ugualmente compatibili. Trattare il modello passeggeri come **scenari plausibili**, finché mancano segnali indipendenti.

---

## 5. Statistiche PMCSN e metodi di analisi

Per arco, fermata, linea, fascia oraria e sistema, dove misurabile:

- tempi medi e varianze dei collegamenti `E[T_ij]`, `Var(T_ij)`; distribuzioni empiriche e quantili P50/P90/P95;
- tempi di sosta `E[D_i]`, `Var(D_i)` con indicazione se misurati o inferiti;
- headway programmati/effettivi, coefficiente di variazione `CV_H`, distribuzione dei ritardi, bunching (definizione operativa da fissare);
- throughput passeggeri serviti e mezzi transitati, occupazione `O_b/C_b`, queue length `E[Q]`, `P(Q>K)`, mancati imbarchi;
- tempi d'attesa `E[W_q]` e complessivi `E[W]`, puntualità, regolarità e distribuzioni per fascia;
- bilancio passeggeri, consumo di capacità e disponibilità di risorse dove modellate.

**Identità/controlli:** Little `L=λW` solo quando insieme di sistema e regime rendono valido il confronto; verificarne le condizioni anziché applicarla automaticamente a intervalli transitori. Pollaczek–Khinchin `M/G/1` può servire soltanto da benchmark per un singolo server con ipotesi idonee: non descrive direttamente autobus batch, periodici e mobili. Reti di Jackson soltanto come benchmark se rispettate le loro ipotesi; simulazione a eventi discreti per il modello principale.

---

## 6. Pipeline dati e qualità

**Flusso:** `HTTP download → raw immutabile → parsing/validazione → normalizzazione → join static/realtime → eventi inferiti → features → parametri → simulazione → report`.

1. **Ingest statico:** scaricare ZIP e checksum, validare CSV, servizio calendar/calendar_dates, direzioni, shape e stop sequence; memorizzare versione GTFS.
2. **Ingest realtime:** interrogare i feed all'incirca ogni 60 s (se supportato dalla sorgente e dai termini), impostare timeout/backoff e user-agent identificabile, salvare raw `.pb` comprimibili con timestamp acquisizione + hash; parsare protobuf.
3. **Normalizzare:** `observed_at_utc` (nel feed), `fetched_at_utc` (client), `feed_timestamp_utc`, `service_date`, `route_id`, `trip_id`, `vehicle_id`, `stop_id`, `stop_sequence`, posizione e campi opzionali. Evitare join che confondono due istanze della stessa corsa in giorni diversi.
4. **Controlli:** freschezza, duplicati, buchi temporali, jump GPS, velocità implausibili, `trip_id` senza corrispondenza, sequenze fermate incoerenti, anomalie dei timestamp, modifiche di topologia, veicoli scomparsi dal feed.
5. **Map matching/event detection:** associazione alla shape e inferenza passaggio/arrivo/partenza con soglie configurabili; `event_confidence`, intervallo di incertezza e regole per scartare stime deboli.
6. **Feature engineering:** tempi tra fermate, ritardi rispetto a schedule, headway per `route_id + direction_id + stop_id + service_date`, breakdown per fascia/giorno; aggregati robusti.
7. **Versionamento:** SQLite per tabelle normalizzate, con export CSV e schema documentato; `data/raw/` in append-only; nessun download automatico durante i test unitari.

**Metriche di salute collector:** percentuale richieste riuscite, latenza, età mediana dei dati, percentuale trip identificabili, copertura temporale per linea, distribuzione buchi e tasso di posizioni scartate. Configurare alert locali/log per errori continuativi.

**Gate G1 (qualità, se si usa una raccolta empirica):** non passare alla calibrazione empirica finché la raccolta pilota non dimostra continuità sufficiente e match statico↔realtime accettabile. Soglie quantitative da concordare **dopo** aver osservato il feed, senza inventarle ora.

---

## 7. Calibrazione, validazione, transitorio e incertezza

**Requisito ufficiale:** analizzare il comportamento iniziale in funzione del tempo, verificarne eventuale convergenza e motivare l'orizzonte. La Fase 4 della checklist è dedicata a questo studio; warm-up e stazionarietà non vanno presupposti. La calibrazione empirica qui sotto si applica quando si usano dati osservati, mentre verifica e validazione documentata sono richieste anche nel percorso a scenari.

1. **Split temporale:** training/calibrazione, validation e test su giorni distinti; evitare leakage di una stessa corsa o finestra a cavallo degli split.
2. **Baseline:** orario programmato senza rumore; distribuzione empirica per fascia; modello senza feedback della domanda; confrontare ogni versione avanzata con queste.
3. **Fit tempi di arco:** empirico bootstrap, gamma/lognormale o altra distribuzione giustificata da goodness-of-fit e capacità predittiva; dipendenza per ora/giorno dove i campioni sono sufficienti.
4. **Fit dwell:** soltanto se eventi fermata attendibili; altrimenti prior plausibili e sensibilità, non parametri presentati come misurati.
5. **Domanda passeggeri:** ricercare eventuale segnale indipendente; se assente definire tre livelli di domanda (basso/medio/alto), OD/routing parametrico e intervalli plausibili, senza chiamarli verità osservata.
6. **Obiettivo calibrazione:** combinare errori **normalizzati** su headway, tempi, ritardi e, solo se davvero disponibili, occupazione/boarding. Vincoli fisici, regolarizzazione, identificabilità e analisi di sensibilità; non minimizzare una sola metrica.
7. **Validazione:** MAE/RMSE o altra distanza per tempi, distribuzioni/quantili, confronto autocorrelazione e bunching, copertura degli intervalli predittivi, confronto per ore di punta e fasce morbide.
8. **Robustezza:** repliche indipendenti, random seed salvati, intervalli di confidenza, bootstrap sui dati empirici, scenari ottimistico/centrale/pessimistico; confronti con *common random numbers* quando opportuno.

**Gate G2 (identificabilità):** se due profili di domanda distinti riproducono ugualmente ritardi/headway ma generano code differenti, il report deve mostrarlo esplicitamente. Le conclusioni sulle attese dei passeggeri resteranno condizionate allo scenario e non saranno presentate come misure reali.

---

## 8. Esperimenti e interventi

La tabella propone scenari candidati: scegliere quelli pertinenti nel disegno sperimentale di Fase 1. S0 e S1–S3 non sono un insieme imposto dal PDF. L'algoritmo migliorativo è obbligatorio per un gruppo e facoltativo per il progetto individuale; in gruppo occorre ripetere lo studio sul modello evoluto, incluso il transitorio.

| ID | Scenario | Modifica | Misure principali |
|---|---|---|---|
| S0 | Baseline | Servizio e parametri calibrati o scenari di riferimento | Ritardi, headway, tempi attesa, code |
| S1 | Domanda crescente | Moltiplicatore `λ` per fascia e fermata | Saturazione, code, mancati imbarchi |
| S2 | Holding | Attesa controllata a fermate/capolinea designati | Regolarità, costo in tempo a bordo, attesa |
| S3 | Headway-based control | Partenze/holding per mitigare deviazione dagli intervalli target | CV degli headway, attese, throughput |
| S4 | Capacità/frequenza | Modifica mezzi o numero corse entro vincoli definiti | Miglioramento per risorsa aggiunta |
| S5 | Perturbazione | Rallentamento/chiusura su tratto condiviso | Propagazione e resilienza |

**Obiettivo multi-criterio (esempio):** minimizzare media ponderata di attesa passeggeri, ritardo autobus, bunching e probabilità di mancato imbarco. Definire unità e normalizzazioni; includere costi/penalità di holding e numero di mezzi. Verificare che migliorare la puntualità dei bus non peggiori il tempo totale sperimentato dagli utenti.

---

## 9. Architettura software richiesta

**Linguaggio richiesto:** C. Standard di riferimento proposto: **C17**, da verificare con la toolchain scelta. Build con **CMake**, test registrati con **CTest**; ambiente CLion oppure Visual Studio Code con supporto C/CMake. Il progetto comprende acquisizione, preprocessing, statistiche, simulazione e CLI in C.

**Dipendenze candidate:** libcurl per HTTP, libarchive o libzip per ZIP, protobuf-c con codice C generato dallo schema GTFS-RT, libyaml per le configurazioni e SQLite per le tabelle normalizzate. Valutare una libreria numerica C per fit e intervalli di confidenza soltanto se necessaria. Verificare compatibilità, licenza e build sulla piattaforma target prima di fissare dipendenze/versioni; nessuna libreria è già installata o validata da questa specifica.

**Strutture e responsabilità:** rappresentare Bus, Trip, Stop, Link ed Event mediante `struct`, tipi e funzioni C con interfacce `.h` e implementazioni `.c`. Separare logica del modello, I/O e CLI. Definire ownership e durata di buffer/strutture, controllare allocazioni, overflow e codici di errore, liberare risorse anche nei percorsi di fallimento. Implementare il calendario DES come coda di priorità con ordinamento deterministico degli eventi simultanei. Definire un generatore pseudocasuale documentato e flussi separati per le componenti stocastiche, evitando di basare la riproducibilità sul solo `rand()` della piattaforma.

```text
rome-bus-pmcsn/
├── README.md
├── CMakeLists.txt
├── CMakePresets.json               # toolchain e configurazioni riproducibili
├── .gitignore
├── configs/
│   ├── collector.yaml
│   ├── network.yaml
│   ├── simulation.yaml
│   └── experiments.yaml
├── data/
│   ├── catalog.yaml
│   ├── raw/                        # non versionare file voluminosi/sensibili
│   ├── interim/
│   ├── processed/                  # SQLite, export CSV con schema documentato
│   └── external/
├── include/rome_bus_pmcsn/          # interfacce pubbliche .h
├── src/
│   ├── main.c                      # dispatch dei sottocomandi CLI
│   ├── common/                     # memoria, errori, tempo, config, RNG
│   ├── ingest/                     # GTFS statico, GTFS-RT, collector
│   ├── validation/                 # controlli e report qualità
│   ├── preprocessing/              # parsing, join, eventi, map matching
│   ├── network/                    # grafo e risorse
│   ├── statistics/                 # statistiche descrittive e fit
│   ├── simulation/                 # DES, bus, fermate, passeggeri
│   ├── calibration/                # stima e confronto dati/modello
│   ├── experiments/                # scenari e ottimizzazione
│   └── visualization/              # export SVG/CSV e report
├── schemas/                        # schema protobuf e versione sorgente
├── scripts/                        # build, esecuzione e figure
├── tests/                          # test C e fixture offline
├── reports/                        # grafici, tabelle, relazione e log
└── docs/
    ├── assumptions.md
    ├── data_dictionary.md
    ├── model_spec.md
    └── decisions.md
```

Il codice protobuf generato deve essere separato dal codice scritto a mano; documentare versione dello schema e procedura di generazione. Le directory di build vanno escluse dal versionamento. Per grafici e mappe usare export generati dal programma e strumenti di rendering documentati, senza introdurre una dipendenza obbligatoria da Python.

### Contratti minimi dei moduli

- `common`: definisce gestione degli errori, ownership, tempo UTC/data di servizio e RNG riproducibile; isola le differenze di piattaforma.
- `ingest`: conserva campi mancanti distinti da zero; scrive raw atomici con timestamp/checksum e libera risorse HTTP/ZIP/protobuf.
- `preprocessing`: fornisce eventi con incertezza e identificatori di corsa univoci; salva tabelle SQLite con schema e provenienza.
- `network`: produce grafo diretto e mappa nodo↔fermata↔linea; non presume connessioni solo perché due fermate sono vicine.
- `simulation`: calendario eventi ordinato, capacità e bilanci, seed riproducibili, statistiche per replica; evita di conservare tutte le tracce individuali negli esperimenti grandi.
- `calibration`: riceve dati/split/versione parametri e produce score, parametri, confidenza e provenienza.
- `experiments`: legge configurazioni immutabili e lancia baseline/scenari con semi e orizzonti comparabili.

### Interfaccia CLI desiderata (da implementare)

```sh
cmake -S . -B build
cmake --build build --config Debug
ctest --test-dir build -C Debug --output-on-failure

rome_bus_pmcsn audit-feeds
rome_bus_pmcsn download-static
rome_bus_pmcsn collect-rt --config configs/collector.yaml
rome_bus_pmcsn quality-report
rome_bus_pmcsn build-network --config configs/network.yaml
rome_bus_pmcsn estimate-parameters
rome_bus_pmcsn simulate --config configs/simulation.yaml
rome_bus_pmcsn validate
rome_bus_pmcsn run-experiments --config configs/experiments.yaml
```

I sottocomandi sono **interfacce da implementare**, non comandi già funzionanti. Invocare l'eseguibile dal percorso prodotto dalla build, con estensione `.exe` su Windows; il percorso dipende dal generatore CMake e dalla configurazione e va documentato nel README.

---

## 10. Piano di lavoro / Checklist eseguibile

**Ordine aggiornato sulla specifica ufficiale AA 2025/2026:** sistema e obiettivi → progettazione esperimenti → modello e simulatore → verifica/validazione → analisi del transitorio → esperimenti → eventuale evoluzione migliorativa → relazione e presentazione.

Le caselle della Fase 0 conservano lo stato del lavoro già verificato; le nuove attività restano aperte. Ogni fase deve lasciare decisioni, comandi, configurazioni e risultati riproducibili. I riferimenti **R01–R16** rinviano a `docs/requisiti_ufficiali.md`, che distingue obblighi ufficiali, condizioni per i gruppi e scelte del caso Roma Bus. **Modalità confermata: progetto individuale.** Le condizioni per i gruppi sono conservate come riferimento, ma non diventano attività obbligatorie per questo progetto.

Il collector e l'estensione a 3–5 linee sono attività di supporto opzionali, da motivare rispetto agli obiettivi. Il programma scientifico può procedere con input tracciati e scenari dichiarati anche senza uno storico realtime di quattro settimane; le conclusioni vanno limitate all'evidenza disponibile. L'analisi del transitorio è invece obbligatoria e precede l'adozione di un warm-up.

### Fase 0 — Setup e audit preliminare già eseguiti

- [x] **0.1 — Inventario iniziale:** verificare repository, file e strumenti già presenti; registrare compilatore C, standard C17 proposto, CMake, sistema operativo e vincoli operativi, evitando di reinizializzare un repository esistente.
- [x] **0.2 — Struttura software:** creare moduli `.c` in `src/`, header in `include/rome_bus_pmcsn/`, `configs/`, `schemas/`, `scripts/`, `tests/`, `docs/`, `reports/` e directory dati secondo la sezione 9.
- [x] **0.3 — Ambiente riproducibile:** predisporre `CMakeLists.txt`, preset di build e dipendenze C; provarne la compatibilità prima di bloccare le versioni; configurare warning del compilatore, formatter, analisi statica e test C tramite CTest.
- [x] **0.4 — Configurazione e documentazione:** creare README con installazione e comandi, `.gitignore` per raw voluminosi/credenziali e configurazioni iniziali senza valori fittizi presentati come reali.
- [x] **0.5 — Audit delle fonti:** individuare e verificare URL effettivi di GTFS statico, Vehicle Positions, Trip Updates e Service Alerts; annotare data di accesso, licenze, termini e limiti di interrogazione.
- [x] **0.6 — Campione statico:** scaricare uno ZIP, calcolare SHA-256 e verificare tabelle, chiavi, calendari, coordinate, sequenze e orari oltre le 24:00.
- [x] **0.7 — Campioni realtime:** scaricare e parsare campioni reali dei tre feed realtime; ispezionare timestamp, identificatori, campi opzionali, occupazione e corrispondenze con lo statico. Usare acquisizioni ripetute per valutare l'aggiornamento: un solo snapshot non misura frequenza o continuità.
- [x] **0.8 — Contratti dati:** definire `data/catalog.yaml` e `docs/data_dictionary.md` con provenienza, unità, null, UTC, data di servizio e chiave dell'istanza di corsa.
- [x] **0.9 — Verifica automatica:** aggiungere fixture statiche/protobuf e test di parsing, campi mancanti, checksum e timestamp; nessun download nei test unitari.
- [x] **0.10 — Prima milestone:** implementare `audit-feeds` e `download-static`; produrre `reports/feed_audit.md` distinguendo risultati osservati, aspetti non verificati e raccomandazione go/no-go. Se un feed necessario è inutilizzabile, documentare il blocco e il perimetro alternativo senza dichiarare realizzata la raccolta.

**Completamento:** eseguibile C compilabile, test di fase superati, campioni tracciati e audit ripetibile. Questa fase prepara la raccolta; non dimostra ancora la qualità di uno storico.

**Stato Fase 0 (2026-10-08):** build C e 8 test offline verificati; campioni reali e audit salvati in `reports/feed_audit.md`. I controlli iniziali della Fase 0 sono conclusi; il riuso scientifico e la redistribuzione restano non confermati dalle condizioni pubblicate. Nessuna raccolta continuativa attivata.

- [x] **0.11 — Lettura ufficiale:** leggere e verificare visivamente le due pagine di `progetto2526.pdf`; ricondurre i requisiti alla nuova checklist e registrare la matrice in `docs/requisiti_ufficiali.md`.

### Fase 1 — Definire sistema, obiettivi e disegno degli esperimenti

- [x] **1.1 — Modalità [R08]:** progetto individuale confermato dall'utente e registrato in `docs/decisions.md`; adempimenti di gruppo non applicabili.
- [ ] **1.2 — Riferimenti metodologici [R04, R05]:** consultare gli algoritmi 1.1 e 1.2 di Leemis–Park e la sezione III di Kurkowski–Camp–Colagrosso; creare una corrispondenza tra i loro passi e gli artefatti del progetto. Il PDF cita questi testi ma non ne riporta il contenuto: non dichiararli già letti e non inventare i passi.
- [ ] **1.3 — Sistema [R01]:** delimitare la sottorete Roma Bus, fermate direzionali, linee, passeggeri, servizio, confini e interazioni. Iniziare da un perimetro gestibile; motivare eventuali ampliamenti.
- [ ] **1.4 — Obiettivi [R02]:** scegliere domande misurabili, motivazioni e miglioramenti attesi; associare ogni domanda a indicatori, unità e criterio di confronto (es. attesa, regolarità, mancati imbarchi).
- [ ] **1.5 — Natura temporale [R03, R13]:** scegliere simulazione a orizzonte finito, studio del regime stazionario o periodico e spiegare perché è pertinente al servizio autobus. Distinguere durata della raccolta dati, orizzonte simulato e tempo di presentazione.
- [ ] **1.6 — Disegno sperimentale preliminare [R03]:** fissare baseline, fattori, livelli, variabili di risposta e scenari in `configs/experiments.yaml` prima di scegliere parametri in base ai risultati. Il numero di scenari deriva dagli obiettivi, non da un minimo numerico attribuito al PDF.
- [ ] **1.7 — Protocollo statistico [R03, R05]:** pianificare repliche, flussi RNG/seed, intervalli di confidenza e precisione richiesta; specificare confronti appaiati/common random numbers quando opportuni. Warm-up e orizzonte definitivo saranno motivati dall'analisi del transitorio.
- [ ] **1.8 — Piano dello studio [R02, R03, R16]:** salvare obiettivi, ipotesi e disegno preliminare in `docs/study_plan.md`; controllare pertinenza PMCSN e fattibilità. Prevedere già la Fase 6 se il progetto è di gruppo.

**Completamento:** caso e obiettivi espliciti, esperimenti progettati, modalità registrata e metodologia collegata ai riferimenti richiesti.

### Fase 2 — Specificare il modello e preparare gli input

- [ ] **2.1 — Modello concettuale [R04]:** descrivere entità, stato, risorse, code, discipline, capacità, arrivi, routing, eventi e ipotesi in `docs/model_spec.md`, seguendo i passi dei riferimenti consultati in 1.2.
- [ ] **2.2 — Topologia e servizio:** estrarre la sottorete GTFS con calendari, direzioni e varianti; salvare grafo, linee e motivazione in `configs/network.yaml`. Non inventare connessioni per prossimità o contese senza fondamento.
- [ ] **2.3 — Contratti dei parametri:** definire unità e fonti di tempi arco, dwell, frequenza, capacità, domanda e OD; etichettare ogni valore come osservato, stimato, assunto o calibrato.
- [ ] **2.4 — Scelta del percorso dati:** decidere quali input richiedano misure realtime e quali possano essere scenari motivati. Se si usano dati reali, verificare condizioni di riuso, qualità e provenienza; altrimenti predisporre input sintetici dichiarati, mantenendo le conclusioni condizionate alle ipotesi.
- [ ] **2.5 — Raccolta opzionale:** se necessaria agli obiettivi, implementare collector C con timeout/backoff, raw atomici, checksum, recovery e report; valutare un pilota 48–72 h e la campagna successiva. Sono proposte operative, non durate imposte dal docente.
- [ ] **2.6 — Pipeline empirica, se usata:** normalizzare UTC/data di servizio, unire statico/realtime per istanza di corsa, filtrare anomalie e inferire eventi con incertezza; conservare le previsioni separate dai passaggi osservati. Applicare G1 prima del fit empirico.
- [ ] **2.7 — Stima e scenari:** analizzare distribuzioni e dipendenze con campioni adeguati; fissare split temporali se si calibra su dati. In mancanza di domanda osservata definire scenari plausibili e sensibilità, senza pretendere di identificarla dai soli ritardi.
- [ ] **2.8 — Specifica eseguibile:** congelare una prima configurazione di rete, parametri, inizializzazione e condizioni di arresto, pronta per il modello base e gli esperimenti di Fase 1.

**Completamento:** modello base e input tracciabili; eventuali limiti dei dati non impediscono la formulazione di uno studio a scenari ben dichiarato.

### Fase 3 — Implementare, verificare e validare il simulatore C

- [ ] **3.1 — Motore DES [R04, R11]:** implementare `struct` e funzioni C, calendario a coda di priorità e ordine deterministico degli eventi simultanei; documentare scelte critiche, ownership e gestione degli errori.
- [ ] **3.2 — Servizio autobus:** implementare inizio/fine corsa, percorsi, tempi di viaggio e soste, servizio GTFS e orari oltre mezzanotte; introdurre risorse condivise solo secondo il modello concettuale.
- [ ] **3.3 — Code dei passeggeri, se previste dagli obiettivi:** implementare arrivi, classi, FIFO/politica esplicita, discesa prima della salita, servizio batch, capacità, trasferimenti e mancato imbarco. Introdurre feedback sul dwell solo dopo verifiche delle componenti.
- [ ] **3.4 — RNG e misure:** salvare seed/flussi, statistiche per replica e serie temporali necessarie al transitorio; raccogliere occupazione, lunghezza code, throughput, attesa e regolarità con denominatori espliciti.
- [ ] **3.5 — Verifica [R10]:** confrontare casi deterministici calcolabili a mano; testare ordine eventi, capacità e conservazione, domanda zero, sovraccarico, casi limite e riproducibilità. Verifica significa correttezza dell'implementazione rispetto al modello.
- [ ] **3.6 — Validazione [R10]:** valutare plausibilità del modello rispetto al sistema e agli obiettivi, con confronti analitici pertinenti e dati indipendenti se disponibili; riportare errori, limiti e ciò che non è validabile. I test software da soli non validano il sistema reale.
- [ ] **3.7 — CLI e report:** implementare `simulate` e `validate` con input configurabili, risultati salvati e comando riproducibile; mantenere separate esecuzioni di debug, calibrazione e valutazione.
- [ ] **3.8 — Gate del modello base:** accettare il modello con criteri fissati nel piano; documentare correzioni prima degli esperimenti finali. Non dichiarare validata la domanda soltanto perché gli headway sono compatibili.

**Completamento:** simulatore base verificato, validazione documentata e serie temporali disponibili. L'audit feed già svolto non completa questa fase.

### Fase 4 — Analizzare obbligatoriamente il transitorio

- [ ] **4.1 — Protocollo [R06]:** scegliere condizioni iniziali motivate e osservabili (es. sistema vuoto e, se utile, carico iniziale alternativo); registrare code, utilizzo, throughput, attese e indicatori autobus in funzione del tempo.
- [ ] **4.2 — Esecuzioni pilota [R06]:** usare più repliche e una griglia temporale coerente; produrre traiettorie e riepiloghi che rendano visibile il comportamento iniziale, non soltanto medie globali.
- [ ] **4.3 — Diagnosi [R06]:** valutare se le metriche raggiungano un regime coerente con le ipotesi e stimare quando. Distinguere stabilizzazione stazionaria, regime periodico e andamento non stazionario; mostrare anche eventuale mancata convergenza.
- [ ] **4.4 — Warm-up [R06, R13]:** per studio stazionario motivare un eventuale tempo di esclusione con le evidenze; per giornata finita/servizio non stazionario mantenere il transitorio pertinente. Non applicare un taglio arbitrario per forzare la convergenza.
- [ ] **4.5 — Orizzonte definitivo [R13]:** scegliere e motivare durata simulata e precisione dopo le prove; distinguere tempo di warm-up, finestra di osservazione e condizioni di arresto.
- [ ] **4.6 — Grafici e tabelle [R07]:** riportare andamento temporale, variabilità tra repliche, punto/intervallo di stabilizzazione se esiste e dati numerici riassuntivi in `reports/transient_analysis.md`.
- [ ] **4.7 — Gate del transitorio:** salvare conclusioni e aggiornare il protocollo di Fase 1. Se il sistema diverge o il regime non è stazionario, motivare la scelta di uno studio finito oppure correggere il modello/lo scenario e ripetere le prove.

**Completamento:** comportamento iniziale mostrato graficamente e numericamente; conclusione esplicita su convergenza e tempi, senza presupporre che debba sempre esistere un equilibrio.

### Fase 5 — Eseguire gli esperimenti e analizzare i risultati

- [ ] **5.1 — Protocollo congelato [R03]:** fissare fattori/livelli, baseline, orizzonte, inizializzazione, eventuale warm-up, repliche e criteri statistici sulla base delle Fasi 1 e 4; motivare ogni revisione.
- [ ] **5.2 — Esecuzione riproducibile:** implementare `run-experiments`; salvare manifest, versione del modello, input e seed per ogni replica e scenario scelto.
- [ ] **5.3 — Stime e precisione:** calcolare indicatori, differenze e intervalli di confidenza; considerare autocorrelazione e indipendenza delle repliche e motivare numerosità/metodo, senza scegliere solo il seed più favorevole.
- [ ] **5.4 — Risultati doppi [R07]:** per transitorio e ogni esperimento produrre sia grafici sia tabelle riassuntive, con unità, scenario, campioni/repliche e incertezza.
- [ ] **5.5 — Interpretazione [R02, R16]:** rispondere agli obiettivi con spiegazioni del comportamento e dei compromessi; distinguere output simulati, dati e ipotesi. Analizzare anche risultati contrari alle aspettative.
- [ ] **5.6 — Sensibilità e robustezza:** variare i parametri più incerti (domanda, dwell, routing/capacità se modellati), verificare stabilità delle conclusioni e limiti di identificabilità.
- [ ] **5.7 — Stato dei risultati:** raccogliere conclusioni del modello base e decisioni aperte; se il progetto è individuale valutare l'utilità della Fase 6, se è di gruppo eseguirla obbligatoriamente.

**Completamento:** risultati base collegati agli obiettivi, con grafici, tabelle e analisi della loro attendibilità.

### Fase 6 — Evoluzione migliorativa facoltativa nel progetto individuale

- [x] **6.1 — Applicabilità [R09]:** modalità individuale registrata; algoritmo migliorativo facoltativo. Decidere se svolgerlo dopo gli esperimenti base, in funzione del valore scientifico e del tempo disponibile; non è un requisito di accettazione per questo progetto.
- [ ] **6.2 — Algoritmo migliorativo [R09]:** scegliere una politica pertinente, per esempio holding o controllo degli headway; descrivere obiettivo, osservazioni disponibili, regole/pseudocodice, vincoli e costo. Deve evolvere il modello, non limitarsi a cambiare un parametro senza un algoritmo.
- [ ] **6.3 — Modello evoluto [R09]:** implementare la politica e documentare differenze rispetto alla baseline, nuove ipotesi e parti critiche del codice C.
- [ ] **6.4 — Ripetizione dello studio [R09]:** ripetere definizione degli obiettivi e degli esperimenti, specifica del modello, verifica, validazione e analisi del transitorio sul sistema modificato; non ereditare automaticamente il warm-up del modello base.
- [ ] **6.5 — Confronto base/evoluto [R07, R09]:** ripetere gli esperimenti comparabili con seed/flussi gestiti coerentemente; mostrare grafici, tabelle e incertezza delle differenze, includendo effetti collaterali come tempo a bordo e risorse aggiunte.
- [ ] **6.6 — Conclusioni della politica [R09, R16]:** discutere se e in quali scenari l'algoritmo migliori l'obiettivo. L'obbligo è studiare l'evoluzione; non inventare un beneficio se non emerge dai risultati.

**Completamento:** per gruppi, evoluzione algoritmica studiata ripetendo i passi ufficiali; per individuali, fase eseguita oppure esclusione dichiarata. Estensioni a molte linee e ottimizzazione estesa restano facoltative.

### Fase 7 — Relazione cartacea, codice e presentazione

- [ ] **7.1 — Relazione [R10]:** preparare un elaborato stampabile con introduzione, caso e motivazioni, miglioramenti attesi, sistema, obiettivi, modelli, verifica, validazione, risultati e conclusioni; includere limiti e riferimenti.
- [ ] **7.2 — Implementazione [R11]:** descrivere le scelte essenziali/critiche (calendario eventi, RNG, capacità, misure, memoria, eventuale controllo migliorativo) con il livello di sintesi richiesto; non sostituire questa spiegazione con il solo listato.
- [ ] **7.3 — Grafici e tabelle [R07, R10]:** inserire entrambi per transitorio ed esperimenti, con legende, unità e spiegazioni; per gruppi includere anche il modello modificato e il confronto.
- [ ] **7.4 — Codice da consegnare [R12]:** preparare sorgenti C, header, CMake, test, configurazioni, README e istruzioni per le dipendenze; escludere librerie di sistema, binari/build e dati senza diritto di redistribuzione. Prevedere invio del codice via email o link secondo la specifica, senza effettuare automaticamente l'invio.
- [ ] **7.5 — Riproduzione e prova pulita:** verificare build/test e comandi di simulazione da ambiente pulito; includere seed, manifest e input consentiti o fixture dichiarate.
- [ ] **7.6 — Presentazione [R13, R14]:** preparare materiale distinto dalla relazione: sempre sistema, obiettivi e orizzonte motivato; mostrare modello/parametri, transitorio, risultati, eventuale evoluzione e conclusioni secondo lo studio svolto.
- [ ] **7.7 — Durata [R14]:** provare la presentazione individuale con cronometro e rispettare il limite di **20 minuti**. La regola di 10 minuti per componente riguarda solo progetti di gruppo.
- [ ] **7.8 — Esecuzioni durante l'esame [R15]:** predisporre comandi e configurazioni per esecuzioni dal vivo richieste dal docente; usare input locali riproducibili, evitando che la demo dipenda dalla disponibilità momentanea del feed.
- [ ] **7.9 — Controllo finale [R16]:** verificare significatività/pertinenza, capacità modellistica e analisi, chiarezza/sintesi e completezza; collegare tutti i requisiti della matrice alle evidenze e registrare le condizioni applicabili.

**Completamento:** relazione cartacea pronta, codice consegnabile senza librerie di sistema, presentazione nei limiti e demo eseguibile; nessun adempimento di consegna dichiarato eseguito finché non lo è realmente.

---

## 11. Test obbligatori

- **Ingest:** parsabilità GTFS e `.pb`, checksum, timestamp, aggiornamenti statici, timeout, file parziali, retry non distruttivi.
- **Identità:** nessuna collisione tra `trip_id` di giornate differenti; compatibilità stop sequence/service date; versioni statiche cambiate.
- **Memoria e robustezza C:** verificare ownership, rilascio risorse, errori di allocazione, accessi fuori limite e overflow; eseguire sanitizer dove supportati dalla toolchain e documentare eventuali strumenti alternativi.
- **DES:** nessun evento retroattivo; nessuna capacità negativa; nessuna salita oltre capienza; ordine discesa/salita; nessuna creazione/distruzione ingiustificata di job.
- **Casi limite:** domanda zero, un solo bus, capacità zero, domanda superiore alla capacità, fermata senza discesa, perdita feed, autobus soppresso, viaggio parziale, corse passanti mezzanotte.
- **Validazione statistica:** con parametri e seed fissati ottenere medesimi risultati; bootstrap/repliche gestiti correttamente; split temporali senza contaminazione.
- **Regression:** confrontare scenario semplificato deterministico con soluzione calcolabile a mano, incluse attese fra arrivi periodici e vincoli di capacità.

---

## 12. Rischi e contromisure

| Rischio | Impatto | Contromisura |
|---|---|---|
| Feed intermittente, cambiato o bloccato | Alto | Pilot, raw backup, retry, metriche, fallback a statico e dataset demo |
| GPS poco frequente per rilevare dwell | Alto | Stimare intervalli di incertezza, non fingere precisione, modellare dwell come scenario |
| Domanda passeggeri non osservata | **Critico** | Scenari espliciti, vincoli plausibili, ricerca di misure indipendenti, sensitivity/identifiability |
| Snapshot GTFS statico non coerente con giorno realtime | Alto | Associare versione statica per data e conservare snapshot |
| Headway/ritardi inaccurati per corse duplicate o mancanti | Medio-alto | Chiavi di istanza, quality filters, manual audit campioni |
| Troppe linee/dimensioni | Medio | MVP progressivo e confini fissi, estendere soltanto dopo validazione |
| Overfitting sui giorni raccolti | Alto | Split cronologico, test out-of-sample, repliche e baseline |
| Assenza di una vera contesa fra risorse autobus | Alto | Esplicitare risorse effettive o concentrare la rete di code sul livello passeggeri |

---

## 13. Decisioni ancora aperte (non inventarle nel codice)

1. Identità delle linee, zona e insieme delle fermate.
2. URL finali dei file e termini di accesso verificati da test reali.
3. Campi realtime realmente valorizzati e qualità della mappatura alle corse.
4. Disponibilità di segnali indipendenti sulla domanda/occupazione.
5. Regola di boarding, OD/routing, tipi veicolo e rispettive capienze.
6. Forma delle distribuzioni e segmentazione per fascia oraria.
7. Definizione quantitativa di *bunching*, metriche target e soglie di accettazione.
8. Regole di congestione/contesa alle fermate, solo se fondate su evidenza.
9. Budget computazionale, necessità effettiva della raccolta continuativa e condizioni/licenze di riuso.
10. Progetto individuale o gruppo (massimo 3), partecipanti e algoritmo migliorativo se richiesto.
11. Obiettivi e fattori sperimentali definitivi, regime finito/stazionario/periodico e orizzonte motivato.
12. Corrispondenza con algoritmi 1.1/1.2 Leemis–Park e linee guida della sezione III Kurkowski et al., dopo lettura effettiva.

**Decision log:** scrivere ogni scelta in `docs/decisions.md` con data, alternative valutate, motivazione, evidenza disponibile e impatto sul modello.

---

## 14. Prossima milestone dopo l'allineamento ufficiale

Leggere la matrice `docs/requisiti_ufficiali.md` e procedere dalla **Fase 1**: la Fase 0 tecnica è già stata eseguita e non va ripetuta. La partecipazione individuale è già confermata: delimitare sistema e obiettivi, consultare i riferimenti metodologici e progettare gli esperimenti prima di sviluppare il DES. Non rendere una raccolta realtime di quattro settimane o l'estensione a 3–5 linee prerequisiti accademici non presenti nel PDF.

**Output atteso:** `docs/study_plan.md` con caso, obiettivi misurabili, fattori/livelli, metriche, strategia temporale preliminare, piano di verifica/validazione e analisi del transitorio; modalità di partecipazione registrata; corrispondenza verificata ai riferimenti richiesti. In seguito implementare il modello base in C, valutarne il transitorio e svolgere gli esperimenti.

**Definizione di completamento:** ogni obiettivo ha esperimenti e risultati attesi documentabili; nessun testo citato è dichiarato letto senza esserlo; ogni nuova checkbox viene spuntata soltanto dopo evidenze. Per i gruppi pianificare l'evoluzione algoritmica e la ripetizione dello studio; la consegna di relazione/codice e le comunicazioni al docente rimangono adempimenti distinti dalla preparazione dei materiali.
