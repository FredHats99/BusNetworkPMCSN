# Protocollo statistico preliminare consolidato per lo studio

Data: 2026-10-09. Piano di Fase 1; nessuna replica eseguita. Specifica eseguibile,
budget RNG e validazione del codice restano gate delle Fasi 2–3.

## Fondamento accademico consultato

PDF Leemis–Park fornito dall'utente, revisione 2004, checksum in
`methodology_leemis_park.md`. Consultati i seguenti passaggi aggiuntivi:

- Sezione 3.2, pp. 112–115 stampate, PDF 108–111: flussi separati, rischi di
  seed arbitrari, jump multipliers e PlantSeeds/SelectStream della libreria rngs.
- Algorithm 8.1.1, p. 354 stampata, PDF 350, e commenti pp. 355–357, PDF 351–353:
  IC Student, ipotesi e dimensionamento con una stima della dispersione
  (Example 8.1.9). Algorithm 8.1.2 descrive anche un criterio sequenziale;
  per il nostro primo studio si sceglie invece produzione a numerosità fissata.
- Sezione 8.3, pp. 369–372 stampate, PDF 365–368: rilevanza delle condizioni
  iniziali/finali negli studi finiti; repliche e IC su statistiche di replica;
  continuazione dello stato RNG fra repliche (p. 371).
- Kurkowski III.B.1–3 e III.C.1–3: seed, inizializzazione, output sufficienti,
  repliche, correlazione e IC; corrispondenza in `methodology_kurkowski.md`.

Controllate visivamente le pagine PDF 350, 352 e 367. Non si dichiara consultato
integralmente il capitolo 8 o adottato un algoritmo di arresto sequenziale.

## Statistiche e unità sperimentale

Ogni replica riparte dalla medesima definizione di stato iniziale e calendario,
resettando lo stato del sistema ma non riutilizzando la sequenza RNG.
L'unità statistica è un risultato per replica. Non trattare passeggeri, corse o
bin di una stessa replica come osservazioni iid.

Risposta primaria Y: media, nella replica, delle attese accumulate entro le 11:00
dalla coorte di passeggeri entrati in coda tra 07:00 e 11:00. Per passeggero p:
`W_p = min(istante_salita, 11:00) - istante_arrivo`; se non è salito entro
le 11:00 usare `11:00 - istante_arrivo`. Si stima E[Y] sulle repliche, non una
media ottenuta mettendo insieme tutti i passeggeri di tutte le repliche.
È un'attesa limitata alla finestra, non una stima dell'attesa completa censurata.
Se la coorte è vuota, definire Y=0 e riportare il numero di repliche vuote.
La quota non servita è sempre riportata accanto a Y, per evitare conclusioni
favorevoli dovute al solo taglio temporale.

Risposte secondarie: integrale delle code / 14.400 s, frazione con almeno un
imbarco negato, quota non salita entro le 11:00, CV headway separati per
linea/direzione/fermata. Produrre risultati anche per linea. Denominatore nullo
per una quota: convenzione zero e contatore esplicito delle coorti vuote;
CV privo di intervalli sufficienti: NA, con numero di repliche disponibili.
Non dimensionare lo studio per tutte le risposte secondarie né chiamarne garantita
la precisione. Gli IC di CV con campioni incompleti sono esplorativi e segnalati.

## IC e confronti

Livello scelto: 95%, marginale, per medie e differenze prespecificate.
Algorithm 8.1.1 usa `s_n^2 = sum((Y_i-media)^2)/n` e semiampiezza
`t_(n-1,0.975) * s_n / sqrt(n-1)`.
Se si usa la varianza con denominatore n-1, indicare S e usare la formula
equivalente `t_(n-1,0.975) * S / sqrt(n)`. Non mescolare le due convenzioni.

I confronti hanno casualità indipendente anche fra scenari. Per ciascun confronto
A-B formare `D_i=Y_A,i-Y_B,i`, abbinando soltanto l'indice i di run indipendenti;
applicare Algorithm 8.1.1 al campione D. Non si usa accoppiamento con CRN e non
si promette riduzione della varianza. L'indipendenza fra differenze deriva dalla
separazione delle run, non dalla parola "appaiato".

Gli IC Student sono esatti sotto normalità iid; per output non normali la
giustificazione è approssimata/asintotica. Controllare istogrammi, outlier e
stabilità della dispersione nel pilota; 40 run non dimostrano normalità.
Non applicare intervalli binomiali ai passeggeri correlati di una replica.
I cinque confronti non hanno copertura simultanea al 95%: niente dichiarazioni
di significatività globale o selezione del "vincitore" senza analisi ulteriore.

## Precisione e dimensionamento

Scelte locali esplicite: pilota di 40 repliche/scenario, confidenza 95%,
semiampiezza obiettivo w=10 s per Y e per le cinque differenze primarie.
Il pilota dà una stima della dispersione e del costo, non conclusioni definitive.
40 è una numerosità pratica coerente con la discussione delle approssimazioni
a grandi campioni alle pp. 356–357, non una garanzia prescritta dal libro.
10 s è la risoluzione desiderata per confrontare le attese del progetto, non
un requisito della consegna o una misura della precisione dei dati reali.

Dal pilota calcolare S per ogni scenario e differenza. Sull'idea di Example 8.1.9,
iniziare da `n0=max(41, ceil((1.96*S/10)^2))`; aumentare il n pianificato fino a
`t_(n-1,0.975)*S/sqrt(n) <= 10`. Questa ricerca è numerica sulla sola stima pilota,
non un arresto monitorato sui dati di produzione. Scegliere un unico N uguale al
massimo dei n stimati, salvare N e il manifest, poi eseguire N nuove repliche per
scenario con casualità disgiunta dal pilota. Le run pilota non entrano negli IC finali.

Il dimensionamento è un adattamento locale della relazione del testo, non un
nuovo teorema: S pilota è incerto e non garantisce la semiampiezza finale.
Calcolare gli IC a produzione conclusa; se non raggiungono 10 s dichiararlo.
Non estendere automaticamente le run fino a osservare l'IC desiderato.
Se costo, non normalità marcata o budget RNG rendono il piano inadeguato,
documentare la revisione prima della produzione e giustificarla con una fonte.
Nessun tetto arbitrario di 500 run; la fattibilità si valuta con il costo misurato.

## RNG e seed

Generatore candidato scelto per la prima specifica: Lehmer multi-stream rngs
del libro, `a=48271`, `m=2147483647`, 256 stream, jump 8.367.782,
moltiplicatore di jump 22925 (tabella a p. 114).
Usare implementazione del generatore accademico, non progettare un PRNG nuovo.
Questa scelta è condizionata al gate di adeguatezza sotto; non è ancora codice.

Seed radice deterministico scelto: 123456789, valido fra 1 e m-1, senza proprietà
speciali attribuitegli. PlantSeeds una volta all'avvio della campagna. Usare:

| Stream | Uso |
|---|---|
| 0 | Arrivi passeggeri |
| 1 | Destinazioni |
| 2 | Tempi/perturbazioni di viaggio indipendenti |
| 3 | Ambiente condiviso tra linee |
| 4 | Stato iniziale casuale, quando previsto |

Ordine campagna: tutti i piloti per scenario nell'ordine YAML, poi produzione
nello stesso ordine. Continuare gli stati di tutti gli stream fra repliche,
scenari e fasi pilota/produzione come descritto in 8.3; non richiamare PlantSeeds
con lo stesso seed a ogni replica/scenario. Salvare stati iniziali/finali di
tutti i flussi, consumi, scenario, indice, fase, versione RNG e configurazione.
Ripetere volontariamente l'intera campagna con la stessa radice è riproduzione,
non una nuova campagna indipendente.

**Gate RNG prima del pilota e della produzione:** verificare l'implementazione con TestRandom
e riferimento noto; contare tutte le estrazioni, incluse quelle scartate; il
consumo cumulativo di ogni stream della campagna deve restare sotto 8.367.782,
senza wrap né sovrapposizione. Verificare inoltre adeguatezza statistica e
dimensionale rispetto agli input (Kurkowski III.A.3). Il solo budget non basta
a dimostrarla. Se il gate fallisce, scegliere un generatore accademico a periodo
maggiore con strategia documentata, aggiornando il protocollo prima di produrre
risultati. Nessun seed arbitrario aggiunto per aggirare il limite.

## Tempo, transitorio e tracciabilità

Studio finito: metriche principali sulla finestra, nessun warm-up eliminato.
Analisi separata del transitorio per bin di 5 minuti e inizializzazioni dichiarate;
nessun bin è una replica. Il drenaggio eventuale produce metriche separate e
non cambia retroattivamente la definizione di Y. Orizzonte e configurazione
definitivi saranno motivati in Fase 4 prima della produzione.

Registrare fonte e stato dei parametri: gli IC quantificano Monte Carlo a input
fissati, non l'incertezza di domanda, capacità, topologia o modello.
Il piano di Fase 1 è completo come protocollo preliminare; i gate esecutivi non
sono risultati già ottenuti e non completano le Fasi 2–5.
