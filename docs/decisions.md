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
