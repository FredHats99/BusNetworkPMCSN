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
