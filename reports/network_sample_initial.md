# Campione Roma Bus — verifica del perimetro

**Storico superato dal riequilibrio del 2026-10-09.** I percorsi degli output
citati sotto ora contengono il campione aggiornato; questa copia conserva solo
la descrizione e i numeri della selezione iniziale. Report corrente: `network_sample.md`.

Verifica: 2026-10-09. Snapshot statico locale acquisito il 2026-10-08;
servizio programmato per lunedì 2026-10-12, partenze nella finestra [07:00,11:00).
Si congela il campione per lo studio dello snapshot, non si certifica il servizio
che sarà effettivamente svolto il 12 ottobre.

| Linea | Operatore GTFS | Partenze direzione 0 / 1 | Stop_id distinti | Varianti ordinate |
|---|---|---:|---:|---:|
| 3NAV | Atac | 56 / 55 | 42 | 2 |
| 19BUS | Atac | 19 / 16 | 91 | 3 |
| 5BUS | Atac | 37 / 38 | 42 | 2 |
| 14BUS | Atac | 30 / 29 | 40 | 2 |
| 314 | TROIANI | 14 / 13 | 115 | 3 |
| 313 | Atac | 16 / 17 | 106 | 3 |

Totali: 340 partenze, 306 stop_id distinti, 12 coppie linea/direzione, 15 varianti.
Una variante è una sequenza ordinata di stop_id e regole pickup/dropoff, distinta
per linea e direzione: la sola shape non basta a definirla. Si conservano tutte
le varianti e le corse originali, incluse le partenze da capolinea intermedi:
19BUS da SCALO S. LORENZO (1 corsa); 313 da L.GO PRENESTE (2); 314 da
COLONNETTI (1). Non si sostituiscono queste corse con percorsi completi inventati.

## Natura dei servizi e limite operativo

L'[avviso ATAC per ottobre 2026](https://www.atac.roma.it/en/media/news/2026/09/21/modernisation-of-the-tramway-network---service-changes-during-august-2026--works-affecting-lines-2---3---5---8--14---19-and-514),
pubblicato il 21 settembre e consultato il 9 ottobre, conferma sostituzione con
autobus delle linee tram 5, 14 e 19 e sostituzione del tratto Porta Maggiore–Valle
Giulia della linea 3. La presenza di quattro servizi sostitutivi rende il campione
adatto a un caso di rete interessata da modifiche del servizio, ma non rappresentativo
di tutte le linee autobus ordinarie di Roma. Le sigle si associano ai servizi per
nomi e capolinea del GTFS e del portale ATAC; non sono misure di affollamento.

**Discrepanza rilevata:** l'avviso indica per il sostitutivo della linea 3 un
capolinea provvisorio a stop_id 71247; questo stop_id non compare nelle varianti
3NAV del campione statico, che terminano a VALLE GIULIA. Non correggere il GTFS
manualmente sulla base del solo avviso. Il modello base userà la topologia dello
snapshot dichiarato; una ricostruzione del servizio reale deviato resta da validare.

## Calendario e confini temporali

Il dataset locale non contiene calendar.txt: il giorno è ricavato dalle aggiunte
e rimozioni in calendar_dates.txt, con service_id associati alle corse. Il campione
è un insieme di partenze, non l'insieme di tutti i mezzi presenti nella finestra.

Sono presenti 50 corse iniziate prima delle 07:00 e non terminate a quell'ora;
68 corse della coorte selezionata terminano dopo le 11:00. L'export della finestra
contiene soltanto le 340 partenze con l'intero percorso, anche oltre le 11:00.
In Fase 2 preparare anche il calendario precedente necessario a inizializzare
i mezzi in viaggio, distinguendo stato iniziale vuoto e scenario caricato.
Fermare gli arrivi della coorte passeggeri alle 11:00; non cancellare eventi già
pianificati delle corse in viaggio. La politica di drenaggio, le ulteriori partenze
e il limite di arresto saranno espliciti; misurare residui e censura.

## Riproducibilità e controlli

Eseguire con Python standard library:

```text
python scripts/select_sample.py
python scripts/audit_sample.py
```

- `network_sample.json`: criterio di selezione, volumi e stop_id condivisi.
- `network_sample_audit.json`: checksum dei sette file sorgente, 15 varianti,
  corse ai confini della finestra e controlli strutturali.
- `data/processed/sample_timetable.csv`: 10.131 righe di passaggi programmati,
  con trip_id, linea, direzione, variante, shape, service_id e orari originali.

Verificate 1.483 corse attive nel giorno per le sei linee: almeno due fermate,
stop_sequence senza duplicati, stop_id e shape_id esistenti, arrivo <= partenza
e ordine temporale non decrescente. Nessun errore nei controlli eseguiti.
Non è una validazione GTFS completa, dei tempi reali o della domanda.
Il core simulativo resta C17; gli script Python sono ausiliari di analisi offline.

## Confini del modello iniziale

Code FIFO separate per linea/direzione, capacità finita dei bus, salite/discese e
sosta dipendente dai passeggeri. Stop_id condiviso non implica uno stallo esclusivo
o un trasbordo. Nessun accoppiamento fisico tra linee introdotto senza specifica:
in Fase 2 definire un eventuale fattore di traffico condiviso e confrontarlo con
tempi indipendenti. La criticità osservata delle linee richiederà dati ulteriori.
