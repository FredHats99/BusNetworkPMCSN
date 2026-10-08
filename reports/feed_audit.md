# Audit Fase 0 — 2026-10-08

## Esito

**GO tecnico per sviluppo e test offline. La raccolta continuativa per il progetto resta da avviare dopo chiarimento delle condizioni di riuso.** La Fase 0 ha prodotto un eseguibile C17, build riproducibile e campioni reali parsabili. Le caselle della Fase 0 documentano i controlli iniziali eseguiti; non certificano una licenza di riuso né la conformità completa ai formati.

Fonte primaria consultata: [Roma Mobilità Open Data](https://romamobilita.it/sistemi-e-tecnologie/open-data/), con [note legali](https://romamobilita.it/azienda/note-legali/). La pagina limita l'uso al supporto al viaggio e avverte che aggregazioni possono rappresentare male il servizio. Non è stata individuata una licenza esplicita che confermi riuso scientifico e redistribuzione. Occupazione dichiarata sperimentale dalla fonte. Nessuna richiesta email, raccolta continuativa o pubblicazione dei campioni eseguita.

## Ambiente verificato

- Windows, repository Git già esistente: non reinizializzato; modifiche preesistenti `.idea/` preservate.
- C17, GCC 15.2.0, CMake 4.3.1 e Ninja inclusi in CLion.
- Build Debug e build GCC `-fanalyzer`; warning `-Wall -Wextra -Wpedantic -Werror`.
- 8 test CTest passati: core offline, CLI, CSV valido, orari oltre mezzanotte, coordinate invalide, SHA-256 noto, riferimenti GTFS validi/invalidi e preservazione del file esistente prima del download.
- Configurazione `.clang-format` predisposta; eseguibile formatter non trovato nella toolchain ispezionata. Sanitizer non eseguiti in questa milestone.
- Core/CLI C; WinHTTP per HTTPS Windows. Estrazione ZIP, SHA-256/catalogo e controllo calendario orchestrati con PowerShell. Backend HTTP non-Windows, protobuf-c e integrazione completa dei metadati in C restano decisioni di sviluppo.

## Acquisizioni reali

Campioni: `data/raw/audit-20261008T124020Z/`; URL, UTC, dimensioni e SHA-256 sono in `data/catalog.yaml`. Le richieste hanno restituito HTTP 200, richiesto dal downloader. Non sono stati archiviati header HTTP completi né la durata esatta: non dichiarare queste metriche disponibili.

| Risorsa | Byte | Contenuto osservato |
|---|---:|---|
| Statico | 46.358.630 | ZIP estratto e 7 tabelle parsate |
| Vehicle Positions | 130.947 | 1.224 entità veicolo |
| Trip Updates | 886.422 | 1.224 aggiornamenti di corsa |
| Service Alerts | 77.246 | 146 entità avviso |
| Secondo Vehicle Positions | 130.256 | 1.218 entità veicolo |

Timestamp header Vehicle Positions e Trip Updates del primo campione: `1791463230`; Alerts: `1791463201`; secondo Vehicle Positions: `1791463413`. I due snapshot veicolo differiscono per hash, conteggio e timestamp (183 s tra timestamp feed): dimostrano un aggiornamento, non una frequenza certa di 60 s o continuità storica. Il timestamp client del secondo campione manuale non è stato registrato e resta null nel catalogo; non ricostruito arbitrariamente.

## GTFS statico

| Tabella | Righe dati |
|---|---:|
| agency.txt | 5 |
| calendar_dates.txt | 3.435 |
| routes.txt | 430 |
| shapes.txt | 535.674 |
| stop_times.txt | 5.004.475 |
| stops.txt | 8.301 |
| trips.txt | 165.443 |

- CSV parsati con gestione virgole tra virgolette e campi vuoti; larghezza coerente con gli header.
- Orari GTFS, coordinate e rappresentazione delle sequenze controllati dal programma C. 624.956 valori di arrivo/partenza sono almeno 24:00:00 e non vanno interpretati come semplice ora civile. Nessun errore diagnosticato da questi controlli.
- Nessun duplicato di `stop_id`, `route_id` o `trip_id`; nessun riferimento mancante da trips a routes/service/shapes né da stop_times a trips/stops, secondo `validate-keys`.
- `calendar.txt` non presente; servizi descritti mediante `calendar_dates.txt`. Date da 20260921 a 20261206; 0 date o tipi di eccezione invalidi nel controllo PowerShell. Questo intervallo non garantisce servizio per ogni linea in tutti i giorni.
- Non verificati completamente: unicità delle coppie trip/stop_sequence, ordine temporale all'interno di ogni corsa, coerenza geometrica shape/fermata e tutte le regole semantiche GTFS. I controlli correnti sono un audit iniziale, non una certificazione completa.

Evidenze: `reports/*.txt.audit.txt`, `reports/static_keys.audit.txt`.

## Campi realtime e match

- Vehicle Positions: descriptor trip e vehicle, timestamp e stop_sequence presenti in 1.224/1.224 messaggi. `occupancy_status` presente in 722/1.224 (circa 59%); `occupancy_percentage` in 0/1.224. Nel secondo snapshot: status in 727/1.218. Presenza non implica affidabilità o conteggi passeggeri verificati.
- Trip Updates: descriptor trip in 1.224/1.224; timestamp in 1.223/1.224. 23.347 StopTimeUpdate, tutti con stop_sequence e stop_id. Negli eventi arrival/departure: 29.106 campi delay, 29.464 time e 24.058 uncertainty. Questi denominatori sono eventi/campi, non numero di corse, e non costituiscono passaggi misurati.
- Estrazione dei trip_id dal decoder C: 1.224/1.224 in Vehicle Positions e 1.224/1.224 in Trip Updates trovano corrispondenza in `trips.txt` nello snapshot statico acquisito. Non è ancora un join per istanza di corsa/data di servizio.
- Alerts: 146 messaggi presenti e parsabili strutturalmente; categorie, finestre di validità e selettori degli avvisi non ancora analizzati semanticamente.
- Decoder limitato a wire format e campi ispezionati; rifiuta troncamenti, overflow varint, header/versione mancanti e ID entità assenti. Non applica tutte le regole dello schema protobuf/GTFS-RT. Schema ufficiale e checksum archiviati in `schemas/`.

Evidenze: `reports/vehicles.audit.txt`, `reports/updates.audit.txt`, `reports/alerts.audit.txt`, `reports/vehicles-second.audit.txt` e CSV dei trip_id estratti.

## Riproduzione e limiti

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Analyze
powershell -ExecutionPolicy Bypass -File scripts/audit.ps1
./build/debug/rome_bus_pmcsn.exe validate-keys data/interim/audit-static
./build/debug/rome_bus_pmcsn.exe feed-trip-ids data/raw/audit-20261008T124020Z/vehicles.pb
```

Lo script di audit genera una nuova directory e nuovi metadati; i feed live cambiano, quindi non deve produrre gli stessi conteggi. Per riprodurre esattamente il campione usare i raw e checksum del catalogo. Il flag `-Repeat` acquisisce un secondo campione dopo 60 s, senza attivare un collector persistente.

Prima di avviare una raccolta continuativa: chiarire condizioni di uso, completare il backend collector con metadati atomici/recovery, poi misurare qualità su 48–72 ore se tale raccolta serve agli obiettivi. Nessun G1 superato, nessuna domanda/capienza identificata e nessuna simulazione implementata. Dopo l'allineamento alla specifica ufficiale, la Fase 1 della checklist riguarda sistema, obiettivi e disegno sperimentale; la raccolta estesa è opzionale.

## Verifica end-to-end dello script

Eseguito con successo scripts/audit.ps1 su una nuova acquisizione. Manifest e output: reports/audit-20261008T125406079Z/. Il nuovo snapshot statico ha lo stesso SHA-256 del primo; i feed operativi live sono cambiati come atteso. Test finali: 8/8 passati in Debug e nella build di analisi statica.
