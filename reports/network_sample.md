# Campione Roma Bus — riequilibrio del perimetro

Verifica: 2026-10-09. Snapshot locale acquisito il 2026-10-08; servizio programmato
per lunedì 2026-10-12, partenze nella finestra [07:00,11:00).
Il perimetro riguarda lo snapshot, non certifica il servizio effettivamente svolto.
La descrizione precedente è conservata in `network_sample_initial.md`.

| Linea | Tipo nel campione | Partenze direzione 0 / 1 | Stop_id distinti | Varianti ordinate |
|---|---|---:|---:|---:|
| 81 | Ordinaria | 15 / 15 | 79 | 2 |
| 628 | Ordinaria | 19 / 18 | 84 | 2 |
| 87 | Ordinaria | 21 / 19 | 66 | 3 |
| 70 | Ordinaria | 20 / 23 | 51 | 3 |
| 5BUS | Sostitutiva tram | 37 / 38 | 42 | 2 |
| 19BUS | Sostitutiva tram | 19 / 16 | 91 | 3 |

Tutte le linee sono Atac (agency_id OP1). Totali: **260 partenze, 310 stop_id
unici, 12 coppie linea/direzione e 15 varianti ordinate**. I sostitutivi hanno
110 partenze (42,3%), contro 280/340 (82,4%) del campione iniziale.
La scelta migliora il bilanciamento tra tipologie, non dimostra rappresentatività
statistica della rete, distribuzione geografica equilibrata o affollamento reale.

## Criterio riproducibile

1. Route_type 3, calendario del giorno selezionato e almeno otto partenze in
   ciascuna direzione nella finestra: soglia sul totale, non frequenza minima in ogni ora.
2. Pool ordinaria con route_short_name numerico; pool sostitutiva esplicita:
   2BUS, 5BUS, 14BUS, 19BUS. Altre sigle speciali sono escluse dal primo campione.
3. Quota quattro ordinarie e due sostitutive. Il seed ordinario deve condividere
   almeno una coppia consecutiva di stop_id con almeno due sostitutivi candidati.
4. A ogni passo scegliere la linea con score più alto fra quelle con almeno una
   coppia consecutiva diretta di fermate condivisa con il campione già scelto.
   Score = partenze / massimo partenze della pool ordinaria +
   min(coppie condivise con l'unione già scelta, 20) / 20. Pareggi per route_id.

La quota e i pesi sono scelte progettuali dichiarate, non un'ottimizzazione
validata. Formula, passi e risultati sono in `network_sample.json` e nello script.
Il nome numerico è un filtro pratico, non una tassonomia ufficiale di tutte le linee.

Il nucleo ordinario è collegato: 81–628 condividono 19 coppie dirette, 81–87 17,
81–70 15 e 87–70 18. I sostitutivi si collegano al nucleo principalmente attraverso
81 (2 coppie con ciascuno); 5BUS–19BUS condividono 33 coppie.
Queste coppie indicano collegamenti topologici nello snapshot, non provano la
stessa geometria stradale o una risorsa fisica contesa. Verificare shape e traffico
prima di usarle per modellare congestione comune.

## Natura dei servizi e limiti

L'[avviso ATAC per ottobre 2026](https://www.atac.roma.it/en/media/news/2026/09/21/modernisation-of-the-tramway-network---service-changes-during-august-2026--works-affecting-lines-2---3---5---8--14---19-and-514)
conferma i servizi sostitutivi di 5 e 19. Le linee ordinarie 70, 81, 87 e 628
sono anche citate nell'[avviso ATAC su corso Rinascimento](https://www.atac.roma.it/tempo-reale/manifestazione-in-corso-rinascimento--stiamo-deviando-le-linee-30-70-81-87-492-e-628).
Quest'ultimo è usato come riscontro dell'identità e del corridoio delle linee,
non come prova di una deviazione attiva nel giorno simulato. Fonti consultate il 2026-10-09.

3NAV è esclusa dal nuovo campione: nello snapshot termina a VALLE GIULIA,
mentre l'avviso ATAC indica un capolinea provvisorio a BELLE ARTI (71247).
Non si certifica che le altre linee siano prive di discrepanze operative.

Ogni variante conserva sequenza ordinata di stop_id e regole pickup/dropoff,
separata per linea/direzione. Conservate anche le partenze intermedie: 19BUS da
SCALO S. LORENZO (1), 70 da PLEBISCITO (1), 87 da PLEBISCITO (1).

## Calendario e confini temporali

Il dataset non contiene calendar.txt: il servizio è ricavato dalle aggiunte e
rimozioni in calendar_dates.txt. Sono presenti **48 corse iniziate prima delle
07:00 e ancora in viaggio**, e **63 partenze della finestra terminate dopo le 11:00**.
L'export contiene soltanto le 260 partenze, ciascuna con l'intero percorso.
In Fase 2 includere il calendario antecedente necessario a rappresentare i mezzi
iniziali; carico e code iniziali richiedono ipotesi proprie. Definire drenaggio,
partenze successive, arresto e attese censurate senza cancellare arbitrariamente
le corse oltre il limite della finestra.

## Audit ed export

Eseguire con Python 3.11+ e standard library:

```text
python scripts/select_sample.py
python scripts/audit_sample.py
```

Output correnti:

- `network_sample.json`: selezione, volumi, intersezioni di fermate e coppie consecutive.
- `network_sample_audit.json`: checksum dei sette file, varianti e controlli.
- `data/processed/sample_timetable.csv`: **8.532 passaggi programmati** con
  trip_id, linea, direzione, variante, shape, servizio e orari originali.

Verificate **1.125 corse giornaliere**, senza errori nei controlli eseguiti:
almeno due fermate, sequenze senza duplicati, stop e shape esistenti, arrivo <=
partenza e tempi non decrescenti. Non è una validazione GTFS completa o operativa.
In tutti gli 8.532 passaggi arrivo e partenza coincidono: il dataset non identifica
soste realistiche. Specificare tempi di viaggio e dwell senza aggiungere due volte
componenti già incorporate nei tempi programmati.

## Modello da specificare in Fase 2

Code FIFO per linea/direzione, capacità finita, salite/discese e dwell dipendente
dai passeggeri. Il campione connesso non basta per un modello interagente: definire
un eventuale fattore di traffico condiviso e confrontarlo con tempi indipendenti.
Stop_id condiviso non implica stallo esclusivo o trasbordo. Domanda e criticità
restano da documentare con input indipendenti o scenari dichiarati.
Il simulatore resta C17; Python è un ausilio offline per selezione e audit.
