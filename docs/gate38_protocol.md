# Gate 3.8 — protocollo diagnostico, versione 1.0

Data: 2026-10-22. Criteri in `configs/gate38_criteria.json`, salvati prima della
nuova campagna. Le prove smoke precedenti sono esplorative; non vengono incluse.
La nuova campagna usa la radice dichiarata e scarta, contando, 1048576 uniformi
per ciascuno dei quattro stream usati, oltre i consumi delle precedenti prove.
Gli stream continuano fra tutte le repliche e tutti i casi. Non si adottano CRN.

Si eseguono 32 repliche per ciascuno dei sei scenari e ciascuno dei due stati
iniziali: 384 repliche diagnostiche, distinte dal pilota e dalla produzione.
Numerosità fissa, senza estensioni o modifica dei margini in base agli esiti.

## Popolazione e misure

Si registrano tutti gli ingressi nei segmenti con partenza in [07:00,11:00),
anche se l'arrivo cade alle 11:00 o dopo: il tempo assegnato è noto al simulatore.
Filtrare soltanto i viaggi completati introdurrebbe una selezione sui tempi.
I primi tratti residui dei bus già in viaggio sono deterministici da contratto
e sono esclusi dalla verifica della distribuzione perturbata.

Ogni record conserva replica, corsa, sequenze, fermate, dominio geometrico,
istante di partenza, arrivo previsto simulato, riferimento, durata, fattore,
bin ambientale, chiave, indice nella tabella e indicatore di riuso.
Il manifest traduce gli indici delle fermate negli stop_id congelati.

Statistiche per replica, poi inferenza fra repliche: media e CV dei fattori,
CDF empirica ai quantili teorici 0.10/0.25/0.50/0.75/0.90, tempi medi simulati
e di riferimento per arco, scostamento medio in secondi dal riferimento.
Si separano rete, linea/direzione e dominio condiviso/non condiviso.
Gli archi obbligatori sono coppie dirette di stop per linea/direzione con almeno
una partenza nominale ammissibile entro T, dopo la prima visita dei bus iniziali.
Il loro insieme è fissato dagli input, non dalla frequenza osservata nelle run.
Archi osservati fuori da questo insieme sono riportati separatamente.

## Controlli esatti e confronto statistico

I controlli esatti verificano chiavi, bin, riusi, durata = riferimento * fattore,
positività, copertura dei record, parametri comuni e consumo RNG: due uniformi
per chiave nuova, zero per i riusi; REGULAR sempre 1 senza estrazioni di viaggio.
Le suite software rimangono un requisito distinto del gate.

Margini locali, scelti prima delle nuove run:

| Grandezza | Banda ammessa |
|---|---|
| Media del fattore, rispetto a 1 o differenza fra scenari | ±0.02 |
| CV del fattore, rispetto a 0.2 o differenza fra scenari variabili | ±0.03 |
| CDF ai cinque quantili, rispetto alla probabilità teorica o differenza | ±0.03 |
| Scostamento medio dal riferimento per arco e differenza dei tempi medi per arco | ±10 s |

Il margine in secondi riprende la risoluzione progettuale dello studio; non è
una garanzia che un errore di 10 s su un arco produca al massimo 10 s sull'attesa.
Gli altri margini sono tolleranze ingegneristiche, non precisione dei dati reali.
Controlli più fini per arco, composizione dei riferimenti, bin e chiavi nuove
sono diagnostiche aggiuntive e non sostituiscono i requisiti obbligatori.

Si usano IC Student bilaterali con correzione Bonferroni sull'intera famiglia
degli asserti obbligatori, compresi quelli senza copertura. Confidenza nominale
simultanea 95%, approssimata per statistiche di replica non normali.
Per i confronti si formano differenze fra repliche indipendenti associate per
indice; i passaggi nella stessa replica non sono trattati come iid.
Questa regola di inclusione dell'IC è conservativa rispetto a un test di
equivalenza TOST marginale al 5%; non si usa la sola mancata significatività.

- **Superato:** IC interamente interno alla banda.
- **Non superato:** IC interamente esterno alla banda.
- **Inconcludente:** IC attraversa un limite, oppure copertura insufficiente.

Ogni gruppo obbligatorio richiede tutte le 32 statistiche di replica; niente
imputazione a zero di archi assenti. Per CV servono almeno due osservazioni
nella replica. REGULAR è controllato esattamente, senza confrontare il suo CV
con quello degli scenari variabili. BASE–REGULAR confronta solo i tempi medi;
SHARED–BASE e SHARED_D125–D125 confrontano anche le marginali dei fattori.

Il gate è accettato solo se passano tutti i requisiti esatti e tutti gli asserti
obbligatori. Un risultato inconcludente non è né equivalenza dimostrata né prova
di un difetto del modello. Eventuali ulteriori prove richiedono una nuova
versione motivata del protocollo, conservando i risultati di questa campagna.

## Fonti metodologiche e limiti

IC fra repliche coerenti con `docs/statistical_protocol.md`. Consultati per
il calcolo numerico e la gestione degli intervalli:
[NIST, test e intervalli](https://itl.nist.gov/div898/handbook/prc/section1/prc15.htm),
[NIST, intervalli Bonferroni](https://www.nist.gov/system/files/documents/2017/05/09/combine-1.pdf),
[DLMF, beta incompleta](https://dlmf.nist.gov/8.17).
La griglia di CDF non dimostra identità dell'intera distribuzione; non si
esprimono garanzie sulle code estreme. L'accettazione eventuale vale per questo
perimetro, orizzonte, stati iniziali e tolleranze. Non calibra domanda/OD/tempi
reali e non conclude l'analisi del transitorio.
