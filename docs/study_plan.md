# Piano dello studio — Fase 1

Data: 2026-10-09. Stato: Fase 1 consolidata come piano preliminare dello studio;
input e configurazione eseguibile da specificare in Fase 2.
Progetto individuale C17. Requisiti: `requisiti_ufficiali.md`, R01–R06, R13, R16.

## Sistema e confini proposti

Obiettivo finale indicato dall'utente: simulare insieme tutte le linee, con
attenzione a quelle critiche e trafficate. Primo perimetro: sei linee collegate,
entrambe le direzioni, con fermate direzionali, archi, corse e passeggeri con
destinazione a valle. La dimensione è una scelta di fattibilità, non un minimo
accademico; il simulatore dovrà rappresentare linee tramite dati e identificativi,
senza logica dedicata ai nomi di questo campione.

Campione riequilibrato dal GTFS locale: ordinarie `81`, `628`, `87`, `70` e
sostitutive `5BUS`, `19BUS`; giorno di servizio 2026-10-12, partenze tra 07:00 e
11:00 (estremo finale escluso). Totali: 260 partenze, 310 stop_id distinti,
12 coppie linea/direzione. I sostitutivi coprono il 42,3% delle partenze, contro
l'82,4% del campione iniziale, conservato in `../reports/network_sample_initial.md`.
Selezione riproducibile: `scripts/select_sample.py`; risultati e intersezioni in
`reports/network_sample.json`. Si richiedono almeno otto partenze per direzione;
selezione a quote quattro ordinarie e due sostitutive, con seed ordinario collegato
ad almeno due sostitutivi, poi greedy per frequenza relativa e coppie consecutive
di fermate condivise; score e passi sono registrati nell'output. La pool ordinaria
usa nomi numerici e route_type bus: è un criterio locale che esclude etichette
speciali, non una tassonomia completa del servizio. Il campione è connesso per
coppie dirette di stop_id comuni, non dimostra congestione
stradale, interscambi effettivi o rappresentatività dell'intera città.

Verifica del campione e natura dei servizi in `../reports/network_sample.md`:
15 varianti ordinate, calendario e checksum tracciati; controlli strutturali
senza errori sulle 1.125 corse giornaliere. Si mantengono tutte le varianti.
Due linee sono servizi sostitutivi dei tram; 3NAV è esclusa per la discrepanza
di capolinea rilevata nell'audit precedente. Il perimetro è congelato
come caso sullo snapshot, non come ricostruzione validata del servizio reale.
Non attribuire criticità o carico passeggeri alla sola frequenza GTFS;
affollamento e ritardi richiedono evidenze indipendenti.

Ogni fermata ospita una coda FIFO; gli autobus sono server mobili con servizio
batch e capacità finita. Le discese precedono le salite. La sosta dipende dai
passeggeri serviti e collega domanda, regolarità e attesa. Non si assumono stalli
con capacità limitata senza evidenza. Code inizialmente separate per linea e
direzione anche presso stop_id condivisi; niente trasbordi o abbandoni nel primo
modello verificabile. L'esecuzione congiunta non basta a rappresentare interazioni:
studiare perturbazioni di viaggio indipendenti o condivise sui tratti comuni,
mentre routing tra linee e blocking richiedono un modello e input espliciti.
Le corse entrano da un calendario di partenze esogeno
ed escono al capolinea: nessuna promessa di modellare turni o ricircolo dei mezzi.

Domanda, OD, capacità e tempi operativi sono ipotesi da specificare in Fase 2,
con unità, fonte, stato e incertezza. Le code prodotte saranno risultati condizionati
agli scenari, non stime osservate delle code reali. Nessuna raccolta continua richiesta.

## Domande e risposte misurabili

| Domanda | Indicatori per replica | Confronto |
|---|---|---|
| Come aumenta la congestione al crescere della domanda? | Attesa limitata alla finestra (s), coda media temporale (passeggeri), quota con almeno un imbarco negato e quota non servita | Moltiplicatori domanda 0.75, 1, 1.25 a servizio invariato |
| Quanto incide l'irregolarità del viaggio a parità di tempo medio? | Attesa limitata alla finestra (s), CV degli headway per linea/fermata, imbarchi negati e quota non servita | Variabilità nulla e positiva a domanda centrale |
| Quanto cambia il servizio quando le linee subiscono perturbazioni condivise invece che indipendenti? | Attesa limitata alla finestra (s), quota non servita e CV headway per linea/fermata | SHARED–BASE a domanda centrale e SHARED_D125–D125 a domanda alta, con identiche distribuzioni marginali degli input |

Ipotesi da valutare: più domanda aumenta congestione; maggiore variabilità può
peggiorare attesa e regolarità anche con uguali tempi medi. Non sono risultati acquisiti.
L'obiettivo decisionale è individuare quali condizioni di domanda, regolarità e
dipendenza dell'ambiente peggiorano il servizio nel campione, e se trattare le
linee come sistemi con ambiente indipendente sottostima o sovrastima l'attesa.
Per ogni confronto stimare differenza in secondi e IC: semiampiezza desiderata
10 s; differenze sotto 10 s sono considerate poco rilevanti per questo primo
studio (soglia progettuale, non requisito accademico). Confrontare anche quota
non servita e risultati per linea prima di raccomandare priorità operative.
Un IC che include zero resta inconcludente sul segno; un IC che attraversa
la soglia di rilevanza resta inconcludente sulla rilevanza pratica.
Non presupporre che la correlazione peggiori necessariamente tutte le metriche.
Il miglioramento atteso è una diagnosi utile per priorità operative;
holding e ottimizzazione rimangono estensioni facoltative.

Definizioni: risposta primaria = attesa media di replica limitata alle 11:00
per la coorte entrata nella finestra, includendo chi non è salito; formula e
convenzioni per coorti vuote in `statistical_protocol.md`. L'attesa completa
fino alla salita, quando disponibile, è una metrica separata, non un sostituto
scelto dopo aver visto i risultati. Imbarco negato quando
un passeggero presente e ammissibile resta per capacità insufficiente, contato una
sola volta nella quota passeggeri e separatamente come numero di eventi. CV degli
headway calcolato per fermata/direzione, senza mescolare fermate; non definito
quando mancano intervalli sufficienti. Coda media = integrale della coda / durata.

## Tempo e transitorio

Studio a orizzonte finito di una finestra di servizio, preliminarmente 4 ore.
Il calendario e la domanda possono variare nel tempo; non si presume stazionarietà.
La finestra programmata selezionata è 07:00–11:00 del 2026-10-12.
La Fase 2 specificherà condizioni iniziali coerenti: lo snapshot contiene 48
corse già in viaggio alle 07:00 e 63 partenze della finestra terminate dopo le 11:00.
In Fase 4 confrontare stato vuoto e stato iniziale caricato dichiarato, osservando
code, attese, occupazione e headway in intervalli di 5 minuti. Studiare se e quando
l'effetto iniziale si attenua, senza scartare automaticamente un warm-up.

Separare coorte di arrivi nella finestra e passeggeri iniziali. Al termine
registrare residui e attese censurate, evitando di stimare l'attesa della coorte
dai soli passeggeri serviti. Valutare un drenaggio con servizio esplicitamente
definito in Fase 2; se non tutti salgono, riportare quota non servita e attesa
troncata all'orizzonte per tutta la coorte. L'attesa completa resta non disponibile.
Durata della raccolta, orizzonte simulato e presentazione (20 minuti) sono distinti.

## Disegno e statistica preliminari

Scenari in `../configs/experiments.yaml`: BASE indipendente a domanda centrale,
D075 e D125 con domanda 0.75 e 1.25, REGULAR senza variabilità del viaggio,
SHARED a domanda centrale e SHARED_D125 a domanda alta. Sono sei scenari mirati,
non un fattoriale completo o un minimo ufficiale. Cinque confronti prespecificati.
Parametri assoluti da congelare prima degli esperimenti; nessun livello scelto
per produrre un risultato favorevole. Domanda centrale e livelli sono scenari
assunti, non stime dell'affollamento reale.

Il confronto di variabilità mantiene invariati i tempi medi per arco.
Il confronto indipendente/condiviso mantiene calendario, capacità, domanda, OD,
dwell e distribuzioni marginali delle perturbazioni sugli stessi archi.
Nello scenario condiviso un fattore d'ambiente è comune alle linee sul medesimo
arco validato e bin temporale di 5 minuti; nello scenario indipendente il fattore
ha la stessa legge ma è separato per linea. Fuori dal dominio condiviso il modello
è invariato. Legge, intensità, geometria degli archi e controlli delle distribuzioni
effettivamente generate sono specifiche di Fase 2, da congelare prima delle run.
Questa costruzione è un'ipotesi locale per confrontare dipendenza degli input,
non un algoritmo bus attribuito al libro. Non rappresenta causalità bus-bus,
blocking o capacità della strada: le linee interagiscono con un ambiente comune.

Protocollo in `statistical_protocol.md`, fondato su Leemis–Park 3.2, Algorithm
8.1.1, Example 8.1.9 e sezione 8.3, oltre a Kurkowski III.B/III.C.
Scelte locali dichiarate: 40 piloti per scenario, IC marginali Student al 95%,
semiampiezza 10 s per medie primarie e differenze, produzione nuova a N fissato
dal pilota. Non adottati CRN: confronti con casualità indipendente e differenze
fra repliche indipendenti associate per indice. Numero totale di produzione
determinato dalla dispersione, non un tetto di 500 run.

RNG candidato: rngs del libro con flussi separati e continuazione degli stati,
radice deterministica 123456789 e manifest di tutti gli stati iniziali/finali.
Implementazione, disgiunzione, budget cumulativo e adeguatezza statistica sono
gate prima del pilota/produzione, non prove già superate. Se il periodo è
insufficiente, scegliere una risorsa accademica a periodo maggiore prima delle run.
OD e parametri assunti richiedono sensibilità separata: gli IC Monte Carlo non
misurano l'incertezza delle ipotesi. Verificare già nelle prove preliminari che
tracce e denominatori consentano le metriche pianificate (III.B.3).

## Pertinenza, fattibilità e gate

Il modello tratta code, server mobili batch, capacità finite, stato ed eventi
stocastici: è pertinente alla modellistica prestazionale PMCSN. La rete di sei
linee è generica nei dati e riutilizzabile per l'estensione futura; non occorre
simulare tutta Roma per concludere questo studio individuale.
Il piano richiede 240 run pilota e 6*N di produzione; tempo e memoria si
misureranno nelle prime run, senza promettere un costo non ancora osservato.
Fattibilità iniziale sostenuta da topologia e calendario estratti, perimetro
limitato, assenza di trasbordi/turni e nessuna dipendenza da raccolta continua.
Le interazioni condivise, input assoluti e RNG non sono ancora validati.

Fase 2: congelare concetto, input, dominio condiviso, stato iniziale e arresto,
etichettando osservato/assunto/stimato/calibrato; nessun default silenzioso.
Fase 3: verifica distinta dalla validazione; casi deterministici, bilanci e
metriche, controllo RNG e confronto con dati disponibili o controlli di
plausibilità dichiarati. L'audit GTFS non valida passeggeri o tempi reali.
Fase 4: diagnosticare il transitorio e riesaminare orizzonte e inizializzazione,
senza scarti arbitrari. Fase 5: riesame preproduzione, manifest, run e analisi.
Ogni revisione del disegno resta tracciata prima della produzione.

## Riferimenti e attività ancora aperte

Sezione III di Kurkowski–Camp–Colagrosso letta integralmente il 2026-10-09
dal PDF locale fornito dall'utente. Fonte, checksum, pagine e corrispondenza in
`methodology_kurkowski.md`. L'articolo distingue tipo di simulazione, verifica e
validazione, adeguatezza PRNG, input espliciti, caratterizzazione degli scenari,
inizializzazione, raccolta delle metriche, repliche, IC e ripetibilità.

Consultate anche le procedure metodologiche nel PDF Leemis–Park fornito
dall'utente: sviluppo del modello (sei passi) e studio (cinque passi), mappati in
`methodology_leemis_park.md`. Il frontespizio indica revisione dicembre 2004 e
numerazione 1.1.1/1.1.2; la consegna cita 2006 e 1.1/1.2: identità bibliografica
non verificata, differenza documentata. La consultazione e mappatura del punto 1.2
sono concluse sui testi forniti; l'esecuzione dei passi resta nelle fasi successive.
I dettagli DOE sono rinviati da Kurkowski ad altre fonti; le procedure iniziali
Leemis–Park non fissano da sole parametri, PRNG o formule statistiche.

La Fase 1 è conclusa come pianificazione preliminare: obiettivi, confronti,
tipo temporale, protocollo e fattibilità sono espliciti. La Fase 2 renderà
eseguibili rete e input; Fase 3 verifica
bilanci, capacità e casi deterministici e documenta la validazione; Fase 4 motiva
inizializzazione e orizzonte; Fase 5 produce grafici e tabelle con incertezza.
