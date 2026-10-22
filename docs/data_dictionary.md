# Contratto dati iniziale

## Input offline di Fase 2

Contratto, provenienza e limiti: [phase2_inputs.md](phase2_inputs.md).
Gli identificativi restano stringhe; i tempi sono secondi dal giorno locale
di servizio (anche oltre 86400), non timestamp UTC. Le intensità sintetiche
sono passeggeri/secondo e le capacità sono posti passeggeri totali.
Gli orari GTFS sono programmati. Gli archi esportati sono coppie consecutive
di fermate, non segmenti stradali già validati. Le medie di headway mancanti
sono `null`, distinte da zero. I parametri assunti hanno una configurazione
separata dai dati osservati nel file GTFS.

## Feed grezzi e normalizzazione realtime prevista

Raw ZIP/protobuf immutabili in directory per acquisizione UTC. Metadati JSON: feed, path, fetched_at_utc (inizio richiesta), codice di uscita e SHA-256. I dati voluminosi non sono versionati.

| Campo normalizzato previsto | Tipo/unità | Significato |
|---|---|---|
| fetched_at_utc | ISO 8601 UTC | Richiesta client |
| feed_timestamp_utc | Unix seconds UTC, nullable | Header feed |
| observed_at_utc | Unix seconds UTC, nullable | Timestamp veicolo |
| service_date | YYYYMMDD Europe/Rome | Giorno di servizio |
| trip_id, route_id, vehicle_id, stop_id | Stringhe opache, nullable | Non convertire in numeri |
| start_time | Secondi dal giorno di servizio, nullable | Può superare 86400 |
| stop_sequence | Intero, nullable | Ordine fermata |
| latitude, longitude | Gradi, nullable | Coordinate da validare |
| occupancy_status | Enumerazione, nullable | Categoria, non conteggio |
| occupancy_percentage | Percentuale, nullable | Distinta dalla categoria |
| event_confidence | Scala da definire | Qualità inferenza |

Identità prevista: versione statica + trip_id + service_date + start_time ove necessario. Null e zero restano distinti. La pipeline normalizzata e il join non sono ancora implementati.
I contatori `vp_*_descriptor_present` verificano presenza del messaggio, non validità dell'identificatore interno. Nell'audit iniziale `feed_timestamp=0` non distingue assente/zero: non usare come contratto normalizzato. Trip Updates contiene previsioni, non passaggi automaticamente osservati.
