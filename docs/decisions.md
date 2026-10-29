# Decisioni — 2026-10-08

- C17 richiesto; GCC 15.2.0 e CMake 4.3.1 inclusi in CLion verificati su Windows. CTest e analisi statica GCC; nessuna installazione esterna.
- Core offline senza dipendenze. Primo downloader con WinHTTP di sistema, TLS verificato; portabilità HTTP su altri sistemi ancora da implementare. libcurl resta un'alternativa.
- Decoder protobuf limitato all'audit strutturale; non certifica conformità semantica GTFS-RT. protobuf-c e codice generato restano da valutare per la pipeline.
- Estrazione ZIP e registrazione SHA-256 orchestrate con PowerShell nella milestone iniziale; core e CLI sono C. Integrazione completa in C ancora aperta.
- Pagina fonte consultata: https://romamobilita.it/sistemi-e-tecnologie/open-data/. Limita l'uso al supporto al viaggio: riuso scientifico e redistribuzione non confermati. Non attivare raccolta continuativa prima di chiarire questo punto.
- Nessuna linea, domanda, capienza o distribuzione scelta.

## Allineamento alla specifica ufficiale

- Fonte: `C:/Users/feder/Desktop/progetto2526.pdf`, AA 2025/2026, due pagine lette integralmente e controllate visivamente. Tracciamento in `docs/requisiti_ufficiali.md`.
- L'utente conferma progetto **individuale**: presentazione massimo 20 minuti, algoritmo migliorativo facoltativo. Le regole per gruppi sono conservate nella matrice come non applicabili alla modalità attuale.
- Disegno degli esperimenti prima dell'implementazione DES; analisi del transitorio obbligatoria e separata da warm-up/medie globali.
- Quattro settimane di raccolta, 3–5 linee e almeno tre scenari non sono minimi ufficiali: restano scelte da motivare e ridimensionare rispetto agli obiettivi.
- Fase 0 tecnica preservata; prossimo passo Fase 1 (sistema, obiettivi, riferimenti metodologici, disegno sperimentale).
- Algoritmi 1.1/1.2 di Leemis–Park e sezione III dell'articolo citato non ancora letti: consultazione e corrispondenza restano attività aperte.

## Avvio Fase 1 — 2026-10-09

- Prima proposta documentata in `study_plan.md`: una linea/direzione, studio finito, scenari di domanda e variabilità dei tempi di viaggio. Linea concreta e parametri assoluti ancora da scegliere.
- Disegno preliminare in `../configs/experiments.yaml`; non è una configurazione eseguibile. Non avviati collector o simulazioni.
- Riferimenti reperiti inizialmente, lettura e mappatura ancora aperte. La Fase 1 non è dichiarata conclusa.

## Estensione del perimetro richiesta dall'utente — 2026-10-09

- Obiettivo finale: simulazione congiunta dell'intera rete, in particolare linee critiche e trafficate. La proposta iniziale di una sola linea è superata.
- Primo campione proposto: sei linee, entrambe le direzioni, scelte dal GTFS locale per frequenza e connessione tramite stop_id. Dettagli nel piano dello studio e in `../reports/network_sample.json`.
- Frequenza programmata e fermate condivise non misurano traffico o domanda. Verificare natura dei servizi NAV/BUS e varianti prima di consolidare il campione; interazioni tra linee da specificare in Fase 2.

## Consolidamento del campione — 2026-10-09

- Perimetro selezionato: sei linee e tutte le 15 varianti di fermate del servizio 2026-10-12, partenze 07:00–11:00. Report `../reports/network_sample.md`, audit con checksum ed export dei passaggi programmati.
- Servizi sostitutivi tram confermati dall'avviso ATAC per ottobre; rilevata discrepanza tra capolinea 3NAV nello snapshot e stop provvisorio dell'avviso. Studiare lo snapshot dichiarato senza correzioni arbitrarie o affermazioni di validazione operativa.
- Controlli strutturali superati su 1.483 corse giornaliere. Gestire in Fase 2 le 50 corse già in viaggio all'inizio e le 68 partenze che arrivano oltre la finestra. Nessuna simulazione eseguita.

## Riequilibrio autorizzato dall'utente — 2026-10-09

- Il campione precedente è superato: selezionate 81, 628, 87, 70 (ordinarie) e 5BUS, 19BUS (sostitutive). Tutte Atac, entrambe le direzioni; non si cerca rappresentatività degli operatori.
- Quote 4+2, seed ordinario collegato ad almeno due sostitutivi e selezione per frequenza/coppie consecutive di fermate condivise. Esclusa 3NAV per la discrepanza nota; algoritmo, formula e passi riproducibili nel nuovo output.
- 260 partenze, 310 stop_id, 15 varianti; 1.125 corse giornaliere controllate senza errori. Sostitutivi: 110 partenze, 42,3% del campione. Confini temporali aggiornati: 48 corse già in viaggio, 63 arrivi oltre le 11:00.
- Report, audit, export e configurazioni riallineati. Frequenza non equivale a domanda; il campione connesso resta locale, non una graduatoria delle linee più critiche.

## Lettura metodologica Kurkowski–Camp–Colagrosso — 2026-10-09

- Sezione III del PDF locale fornito dall'utente letta integralmente; corrispondenza fonte/applicazione e checksum in `methodology_kurkowski.md`. Parte Kurkowski del punto 1.2 conclusa, Leemis–Park ancora aperto.
- Confermati i principi di studio finito dichiarato, verifica/validazione prima degli esperimenti, inizializzazione motivata, PRNG adeguato e seed tracciati, input espliciti, output granulari, repliche e IC, risultati ripetibili.
- Il testo non prescrive numero di linee, score greedy, 30/500 repliche, tolleranza 5 s/5%, Student o common random numbers. Ritirati 30/500 e tolleranza come valori operativi; protocollo numerico da consolidare con fonti accademiche. Il 95% resta un candidato locale esplicito.
- Nessun algoritmo simulativo implementato né esperimento eseguito durante la lettura. Il campione autorizzato resta una scelta locale, non una procedura attribuita al documento.

## Lettura metodologica Leemis–Park — 2026-10-09

- PDF fornito dall'utente consultato nelle sezioni 1.1.2/1.1.3: sei passi di sviluppo e cinque di studio. Fonte, checksum e corrispondenza in `methodology_leemis_park.md`.
- Versione effettiva: revisione dicembre 2004, Algorithm 1.1.1/1.1.2; la consegna cita l'edizione 2006 e 1.1/1.2. Nessuna identità tra edizioni dichiarata come verificata. Consultazione e mappatura del punto 1.2 completate sui testi forniti.
- Distinguere modello concettuale, specifica degli input e programma; iterare i passi 2–6, tenere separate verifica e validazione. Disegno preliminare ora, produzione solo dopo il modello verificato/validato e lo studio del transitorio richiesto dalla consegna.
- Nessun nuovo algoritmo, scelta RNG o formula statistica dedotti da queste procedure generali; Fase 1 ancora aperta per consolidamento degli obiettivi, esperimenti e protocollo statistico.

## Chiusura della pianificazione Fase 1 — 2026-10-09

- Consolidati obiettivi, natura finita, sei scenari e cinque confronti. Aggiunto confronto di perturbazioni indipendenti/condivise a domanda centrale e alta, con identiche leggi marginali; ambiente comune distinto da contesa fisica tra bus.
- Consultati passaggi aggiuntivi Leemis–Park 3.2 e 8.1/8.3. Protocollo in `statistical_protocol.md`: IC Student, risultati di replica, stima della numerosità da pilota e produzione nuova a N fissato. Nessun nuovo algoritmo statistico inventato.
- Scelte locali motivate e distinte dalle fonti: 40 piloti/scenario, 95% marginale, 10 s di semiampiezza per attese e confronti primari. Eliminati 30 piloti e tetto 500; casualità indipendente senza CRN. Precisione e costo saranno misurati, non presupposti.
- RNG candidato rngs accademico, radice 123456789, flussi separati continuati fra run; disgiunzione, budget cumulativo e adeguatezza gate prima del pilota e della produzione. Nessun PRNG implementato/validato durante la pianificazione.
- Aggiornati piano, ipotesi, configurazioni, README e caselle 1.4–1.8. Fase 1 conclusa come disegno preliminare; Fasi 2–5 ancora aperte. Nessuna replica eseguita e nessun parametro di domanda presentato come osservato/calibrato.

## Congelamento della specifica Fase 2 — 2026-10-22

- Su richiesta di chiudere i punti residui, adottate regole semplici e documentate
  in `phase2_operational_contract.md`: imbarco iniziale istantaneo a orario GTFS,
  mezzo dedicato per corsa, discesa finale sequenziale, priorità deterministiche.
- Arresto in [07:00,11:00), senza drenaggio e con residui espliciti. Salita
  completata come termine dell'attesa; prenotazione del passeggero evita doppi
  imbarchi e resta nella coda fino al completamento.
- Stati iniziali vuoto e caricato sintetico: stessi 48 bus nelle posizioni
  programmate, 3.240 persone iniziali a bordo nello stato caricato e code
  dipendenti dal livello di domanda; coorti iniziali separate. Non sono stati
  osservati, equilibrati o ricostruiti con una simulazione del passato.
- Verificate le shape: 62 gruppi di tratti compatibili fra linee, 3.978 segmenti
  operativi mappati, con soglie geometriche esplicite. Non è validazione operativa
  su strada. BASE/SHARED usano la stessa mappa, cambiando la dipendenza dei fattori.
- Configurazioni e input congelati con hash; collector e pipeline empirica non
  applicabili. Specifica di Fase 2 completa, nessuna replica o implementazione
  del simulatore dichiarata. RNG e marginali effettive restano gate di Fase 3;
  lo studio obbligatorio del transitorio resta in Fase 4.

## Studio del transitorio completato - 2026-10-29

- Eseguite tutte le 192 repliche congelate (16 x 6 scenari x 2 stati), senza
  selezione, ripetizione o estensione. Audit di hash, contatori, checkpoint,
  griglia e bilanci in `../reports/phase4_completion.json`; analisi in
  `../reports/transient_analysis.md`. Lezioni e pagine in `phase4_academic_basis.md`.
- D125 e SHARED_D125 mostrano accumulo nella finestra e differenze di coda
  nell'ultima ora ancora visibili fra vuoto e caricato. Smaltimento dei
  passeggeri iniziali non equivale a scomparsa dell'effetto sui nuovi arrivi.
  Nessun regime stazionario/periodico o tempo universale di convergenza certificato.
- Confermati 07:00-11:00, warm-up zero e arresto senza drenaggio: oggetto
  dello studio e' il mattino finito. Scartate le alternative di eliminare
  un tratto iniziale a posteriori o allungare fino a osservare un plateau:
  cambierebbero la statistica e richiederebbero nuovi input e budget.
- Stato vuoto scelto come controllo convenzionale per il confronto principale
  successivo, senza aggiungere un carico sintetico preesistente non osservato.
  Non e' dichiarato piu' realistico o equivalente al caricato; le conclusioni
  future saranno condizionate a tale scelta e accompagnate dalla sensibilita
  caricata separata. Non scegliere lo stato in base all'attesa piu' favorevole.
- Precisione finale non rivendicata: N=16 e' diagnostico; nei casi D125 le
  semiampiezze marginali dell'attesa superano ancora 10 s. Pilota di Fase 5
  nuovo, poi produzione nuova a N fissato, senza pooling con gate o transitorio.
- Prossimo cursore RNG `[673381021,669931629,66381872,40754238]`, dal ledger
  completato. Slot inutilizzati bruciati; riserve future ancora coperte.
  Nessuna modifica al modello C o alle evidenze del gate 3.8.
