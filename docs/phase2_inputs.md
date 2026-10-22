# Input di Fase 2: estrazione offline e configurazione sintetica

Data: 2026-10-16. L'estrazione è eseguita sullo snapshot già acquisito;
non sono stati scaricati nuovi feed né avviate raccolte realtime.
Il simulatore non è stato implementato o eseguito. Aggiornamento 2026-10-22:
Fase 2 congelata nel [contratto operativo](phase2_operational_contract.md).
Le scelte sintetiche inizialmente proposte sono ora la specifica di lavoro,
non dati calibrati o risultati validati.

## Dati estratti

Fonte: `data/interim/audit-static`, servizio del 2026-10-12. L'estrattore
verifica calendario, riferimenti alle fermate, ordinamento temporale e
restrizioni di salita/discesa supportate. Conserva orari oltre le 24:00 come
secondi dal giorno di servizio, senza convertirli in orari modulo 24.

| Risultato | Quantità |
|---|---:|
| Corse attive nell'intero giorno, sei linee | 1.125 |
| Partenze in [07:00,11:00) | 260 |
| Corse già in viaggio alle 07:00 | 48 |
| Partenze della finestra con arrivo dopo le 11:00 | 63 |
| Fermate distinte | 310 |
| Coppie dirette di fermate consecutive | 323 |
| Code linea-direzione-fermata con destinazioni possibili nel perimetro operativo | 413 |
| Varianti delle sole partenze della finestra | 15 |
| Varianti includendo le corse già in viaggio | 16 |
| Varianti nell'intero giorno | 17 |

La sedicesima variante operativa appartiene alla 628, direzione 0, ed è
necessaria per una corsa partita prima delle 07:00. Non modifica il conteggio
storico di 15 varianti delle sole partenze nella finestra.

Gli output in `data/processed/phase2/` comprendono:

- `trips.json`: corse del giorno con tempi e sequenze integrali, ruolo rispetto
  alla finestra e riferimento alla variante. Le corse fuori finestra sono
  conservate per possibili estensioni, non automaticamente simulate.
- `patterns.json`, `stops.json`, `shapes.json`: varianti, coordinate delle
  fermate e geometrie ordinate originali.
- `arcs.json`: coppie di fermate consecutive, linee che le attraversano e gap
  programmati per tutte le corse esportate. Non sono archi stradali già validati.
- `queues.json`: destinazioni ammissibili e passaggi nella finestra, ricavati
  dalle corse iniziali e dalle partenze della finestra; conteggi e headway
  interni a ciascuna fascia di 30 minuti.
- `manifest.json`: hash degli input e degli output, perimetro e limiti.

Per ogni fascia, il numero di passaggi è distinto dalla media degli headway
interni. Con meno di due passaggi tale media è nulla come dato mancante
(`null`), non zero. Non vengono inventati intervalli ai bordi della fascia.
L'output contiene gli orari completi per eventuali altri stimatori.

Le geometrie sono esportate, ma non è verificata la coincidenza stradale di
due segmenti: condividere una coppia di stop_id non dimostra di percorrere lo
stesso tratto fisico. Il successivo controllo delle shape definisce 62 gruppi
compatibili nello snapshot; criteri e limiti nel contratto operativo.

## Cosa significano i tempi

Tutti i tempi esportati sono programmati. Nel campione nessuna visita ha
arrival diverso da departure e tutti i gap fra fermate consecutive sono
positivi. Questo non dimostra che la sosta reale sia nulla.

Il gap è `arrival_successiva - departure_corrente`; la sua media descrive
gli orari del file, non una distribuzione empirica dei viaggi.

È concordata una sosta di riferimento sintetica di 15 secondi:

    viaggio_riferimento_i = gap_programmato_i - 15 secondi
    intervallo_simulato_i = sosta_effettiva_i + viaggio_simulato_i.

La seconda espressione è riferita all'arrivo in i fino all'arrivo in i+1;
nel campione arrival_i = departure_i, perciò la prima uguaglianza fissa una
decomposizione convenzionale del gap, non un'identificazione di tempi reali.
Il calendario delle partenze al capolinea deve essere ancorato separatamente:
non aggiungere automaticamente una sosta prima della prima partenza programmata.
Gestione di prima/ultima fermata e stato iniziale restano nella specifica eventi.

Con sosta effettiva uguale a 15 secondi e viaggio deterministico di riferimento
si ricostruisce esattamente ciascun gap GTFS. Una sosta maggiore introduce il
relativo incremento, prima di eventuali perturbazioni del viaggio. Non si
aggiunge la sosta effettiva al gap intero. I 15 secondi non sono una stima
osservata e richiederanno sensibilità.

`travel_reference.json` conserva gap originale, sosta di riferimento e viaggio
derivato per le corse iniziali e le partenze della finestra. I gap originali
restano invariati in `trips.json`. L'estrattore rifiuta tempi derivati non
positivi senza correggerli silenziosamente. La distribuzione della variabilità
è specificata in [travel_time_model.md](travel_time_model.md); la sosta effettiva
è definita di seguito.

### Sosta effettiva concordata

Coefficienti sintetici configurabili, non stimati da misure: apertura porte
2 secondi, discesa 1 secondo/persona, salita 2 secondi/persona, chiusura porte
3 secondi. Un unico flusso effettivo, discese prima delle salite. Con D persone
in discesa e B effettivamente imbarcate, per una fermata servita:

    T_sosta = 5 + D + 2B secondi.

Se nessuno deve scendere e nessun passeggero compatibile aspetta all'arrivo,
la fermata è saltata e T_sosta = 0. Le code incompatibili non obbligano il
bus a fermarsi. Chi arriva durante apertura, discese o imbarco si accoda e
può salire se compatibile e se resta posto. L'imbarco prosegue finché ci sono
passeggeri compatibili e posti; quando una delle condizioni viene meno inizia
la chiusura. I nuovi arrivati durante la chiusura attendono un bus successivo.
Non si attende volontariamente un prossimo arrivo con coda compatibile vuota.

B comprende anche chi arriva durante la visita. La formula dà la durata
finale: non programmare l'intera sosta all'arrivo usando solo la coda allora
presente. Per esempio D = 10 e B = 20 danno 55 secondi.

Eventi simultanei e imbarco iniziale sono specificati nel contratto operativo.
Le regole delle fermate interne non modificano implicitamente le partenze
esogene o la gestione delle corse iniziali.

### Capolinea e corse: regole concordate

Prima/ultima fermata e partenza di ogni variante provengono dal GTFS.
Ogni corsa usa un mezzo dedicato e parte all'orario programmato; non sono
modellati turni, ricircolo o trasferimento dei ritardi fra corse mediante
lo stesso mezzo. Al capolinea finale tutti i passeggeri rimasti scendono,
poi la corsa termina, senza un successivo viaggio di ritorno implicito.

L'imbarco iniziale è istantaneo in FIFO compatibile all'orario GTFS, fino alla
capacità. Al capolinea finale apertura 2 s e discesa 1 s/persona in ordine
a bordo, con completamento individuale delle discese; nessuna chiusura finale
simulata. La corsa vuota termina all'arrivo.

## Parametri sintetici adottati per la specifica

Fonte configurabile: `configs/phase2_assumptions.json`. Output derivato:
`data/processed/phase2/synthetic_scenarios.json`. È una specifica esplicita,
non una calibrazione né un simulatore già pronto alla produzione.

### Flotta

Valori rappresentativi proposti: 109 passeggeri per lo standard da 12 m e
162 per l'articolato da 18 m. Le fonti descrivono rispettivamente una
fornitura da 12 m con capacità fino a 109 e una fornitura ibrida da 18 m
da 162: i valori non sono assegnazioni osservate sulle linee campione.

- [Roma Capitale, fornitura di bus da 12 m](https://www.comune.roma.it/web/it/notizia.page?contentId=NWS417627).
- [Roma Mobilità, ibridi da 18 m](https://romamobilita.it/primo-piano/giubileo-roma-nuovi-15-bus-ibridi-linee-della-periferia/).

Il mix è approssimativamente 50–50: ordinamento per partenza e trip_id,
alternanza standard/articolato in ciascuna coppia linea-direzione sull'intero
giorno, iniziando dallo standard. Si ottengono 565 standard e 560 articolati;
la differenza dipende dai gruppi con numero dispari di corse. Una sottofinestra
non ha necessariamente esattamente il 50%. L'assegnazione è deterministica,
riutilizzabile in tutti gli scenari senza introdurre casualità aggiuntiva.

### Domanda e destinazioni

- Poisson indipendenti per coda, tassi in passeggeri/secondo.
- Otto fasce da 30 minuti; moltiplicatori temporali inizialmente tutti 1.
  La capacità di variare per fascia è presente, ma non si inventa un picco
  mattutino in assenza di evidenze.
- Tasso uguale tra code della stessa linea-direzione, con scala distinta
  fra le dodici coppie linea-direzione.
- Destinazione uniforme fra stop_id distinti raggiungibili a valle da almeno
  una variante operativa; si estrae all'arrivo. Ogni corsa può imbarcare solo
  chi raggiunge la propria destinazione successivamente su quella corsa.
  Le varianti esportate non hanno fermate ripetute.

La scala è costruita senza usare risultati di simulazione:

1. Per ogni linea-direzione si usa come intervallo nominale 14.400 diviso
   il numero di partenze nella finestra. Non è una misura degli headway reali
   né una garanzia per ogni singola fascia o fermata.
2. Per ciascuna variante operativa si calcola il massimo, sui tratti, del
   coefficiente teorico di occupazione con tasso unitario alle origini:
   `K = max_i somma(a=1,...,i) (m-i)/(m-a)`.
3. Il tasso base è `0.85 * capacità_media_assegnata / (h_nominale * K_max)`.
   Le capacità medie sono calcolate sulle partenze della finestra.

I tassi base per coda sono fra circa 0,442 e 2,220 passeggeri/minuto, secondo
la coppia linea-direzione. Questi numeri sono sintetici, non flussi osservati.

Si mantengono i moltiplicatori preliminari D075 = 0,75, BASE = 1 e D125 = 1,25:
i corrispondenti target nominali sono 0,6375, 0,85 e 1,0625 della capacità
media sul tratto di riferimento. Il target maggiore di 1 indica pressione
nominale oltre capacità, non una prova della dinamica delle code del modello
completo. Le medie stazionarie non si applicano in sovraccarico.

La normalizzazione usa la formula del percorso semplice come scala. Frequenze
diverse delle varianti, destinazioni nell'unione e capacità eterogenee la
rendono un riferimento approssimato per il campione; non dimostra stabilità
né garantisce le tre condizioni di domanda effettivamente ottenute. Prima
della produzione occorrono le verifiche preliminari già previste.

### Tempi e confini consolidati

Un CV positivo di 0,2 e moltiplicatori lognormali di media 1 sono ora
formalizzati come valori di lavoro sintetici in [travel_time_model.md](travel_time_model.md),
senza fit empirico. REGULAR usa fattore 1. Le chiavi ambientali sono separate
per linea, coppia diretta di fermate e intervallo di 5 minuti, con riuso nella
replica. Dentro il dominio geometrico si usa shared_arc_id e si elimina la
linea dalla chiave soltanto negli scenari condivisi; fuori dal dominio il
meccanismo è invariato. Le marginali effettive restano un gate del simulatore.

Le posizioni iniziali dei 48 bus sono di calendario. Sono esportati uno stato
senza passeggeri e uno caricato sintetico, con metà capacità a bordo e code
costruite da lambda*h_nominale/2, per il confronto del transitorio. Destinazioni
e anzianità sono esplicite; i passeggeri iniziali hanno coorte distinta. Nessuno
stato è una ricostruzione reale o un equilibrio già dimostrato.

Per il termine si adotta arresto alle 11:00 senza drenaggio, registrando
code, passeggeri a bordo e corse residue; le attese della coorte sono limitate
alla finestra secondo il protocollo. Gli eventi esattamente alle 11:00 non
sono elaborati. Regole complete nel contratto operativo.

## Riproduzione e controlli

Con Python 3.11 o successivo disponibile:

```powershell
python scripts/prepare_phase2.py
python scripts/prepare_shared_geometry.py
python scripts/prepare_phase2_scenarios.py
python scripts/prepare_initial_states.py
python tests/test_phase2_geometry.py
python scripts/audit_phase2_inputs.py
```

Python è un helper offline, non una nuova dipendenza del core C o della build.
I dati derivati sono ignorati da Git e rigenerabili dallo snapshot conservato;
script, ipotesi e report sono gli artefatti versionabili. I raw non vengono
modificati. Gli script sovrascrivono soltanto i propri output derivati.

Manifest sintetico dell'estrazione: `reports/phase2_input_manifest.json`.
Controlli: `reports/phase2_input_checks.json`. Sono passati hash di input/output,
confronto con i conteggi dell'audit precedente, unicità delle assegnazioni,
normalizzazione nominale della domanda e tassi positivi finiti su otto fasce.
Questi controlli non sono validazione del simulatore, della domanda o delle
geometrie condivise. Non sono stati eseguiti esperimenti Monte Carlo.

## Stato della fase

Il percorso adottato è GTFS programmato più ipotesi sintetiche tracciate.
Non sono necessari collector o fit realtime per questa prima specifica.
Riuso e redistribuzione dei feed mantengono lo stato documentato nel catalogo;
nessuna nuova conclusione sulle condizioni d'uso è introdotta qui.

La Fase 2 è conclusa come specifica dal contratto operativo e dal manifest
`reports/phase2_freeze.json`. I campi operativi sono risolti; il numero di
repliche di produzione resta intenzionalmente da stimare dal pilota in Fase 5.
Implementazione, RNG e marginali sulle traiettorie sono gate di Fase 3;
inizializzazione e orizzonte saranno valutati in Fase 4, senza implicare che
lo studio del transitorio sia già eseguito.
