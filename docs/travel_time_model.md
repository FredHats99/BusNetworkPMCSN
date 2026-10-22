# Tempi di viaggio: riferimento e variabilità sintetica

Specifica della variabilità, consolidata con il
[contratto operativo del 2026-10-22](phase2_operational_contract.md).
Il CV = 0,2 è un valore di lavoro sintetico e configurabile, non calibrato.
Il simulatore e la generazione casuale non sono implementati da questo documento.

## Tempo di riferimento

Per la corsa k e il tratto i -> i+1, sia Delta_(k,i) il gap programmato GTFS.
La decomposizione già concordata definisce:

    t_ref_(k,i) = Delta_(k,i) - 15 secondi > 0.

La sosta effettiva è separata: per una fermata servita dura 5 + D + 2B
secondi; è zero se la visita viene saltata. Non aggiungere questa sosta al gap
GTFS intero. Capolinea e stato iniziale richiedono le proprie regole.

## Legge positiva e parametrizzazione

Il tempo simulato sul tratto è:

    T_(k,i) = t_ref_(k,i) F,

con fattore positivo F. Per gli scenari a variabilità positiva:

    F = exp(ell + sigma Z),       Z ~ Normale(0,1)
    sigma^2 = log(1 + v^2)
    ell = -sigma^2 / 2,

dove v è il coefficiente di variazione configurato. Ne segue esattamente:

    E[F] = 1
    Var(F) = v^2
    CV(F) = v.

Con v = 0,2, sigma è circa 0,19804 e ell circa -0,01961. I parametri ell e
sigma sono quelli della normale del logaritmo, non media e deviazione standard
dei secondi di viaggio. Per un fattore marginale estratto senza selezione:

    E[T_(k,i)] = t_ref_(k,i)
    SD(T_(k,i)) = 0,2 t_ref_(k,i).

Per esempio un gap programmato di 100 secondi dà t_ref = 85 secondi e una
deviazione standard marginale di 17 secondi. Il CV 20% non è un limite agli
scostamenti: sono possibili valori più lontani, sempre positivi. Non si
tronca la distribuzione né si arrotonda prima della registrazione degli eventi.

REGULAR usa F = 1 e dunque T = t_ref, con la stessa media nominale. Arrivi,
destinazioni, capacità e soste mantengono le proprie regole; REGULAR non rende
deterministico l'intero sistema.

## Dipendenza e scelta del fattore

Coerentemente con il disegno preliminare, il riferimento di ambiente è
suddiviso in intervalli da 300 secondi, distinti dalle fasce di domanda da
1800 secondi. Al momento di partire effettivamente verso il tratto:

    b = floor(secondi_di_servizio_della_partenza / 300).

Il fattore della modalità indipendente fra linee è identificato da:

    (route_id, from_stop_id, to_stop_id, b).

La tabella ambientale della replica ha fattori indipendenti per chiavi
diverse; una chiave già visitata restituisce lo stesso fattore. Bus della
stessa linea sullo stesso tratto e nello stesso intervallo condividono quindi
il fattore. Non si sostiene indipendenza fra tutti i viaggi individuali.

Le coppie di stop_id sono qui etichette dell'ambiente sintetico interno alla
linea. Non certificano da sole la geometria condivisa fra linee. Il controllo
successivo sulle shape definisce 62 gruppi compatibili nello snapshot.
Dentro tali gruppi, la modalità indipendente usa (route_id, shared_arc_id, b),
SHARED usa (shared_arc_id, b). La mappatura è identica nei confronti e fuori
dal dominio il meccanismo resta quello delle coppie di fermate per linea.
La corrispondenza delle shape non è validazione del servizio reale su strada.

L'implementazione dovrà conservare i fattori per replica, usare i flussi RNG
previsti e registrare un ordine di generazione riproducibile. Non si adottano
CRN fra scenari; la stessa chiave non implica la stessa estrazione in scenari
indipendenti. Un fattore è selezionato all'ingresso e non cambia durante il
tratto anche se il bus attraversa il confine di un intervallo ambientale.

## Limite della conservazione delle medie

La tabella ambientale ha esattamente la stessa legge marginale di riferimento
per ogni chiave, con media 1. Tuttavia i tempi effettivi di ingresso dipendono
da ritardi precedenti e soste, e possono riutilizzare fattori già incontrati.
Non è dimostrato che i fattori campionati dalle traiettorie abbiano sempre
la medesima distribuzione della tabella non condizionata.

Occorre quindi verificare nelle prove del simulatore le distribuzioni e le
medie effettivamente utilizzate e il confronto REGULAR/variabile e
indipendente/condiviso. Non dichiarare già superato il gate delle marginali
del disegno sperimentale. Le formule della tratta a tempi deterministici
restano riferimenti di verifica nelle loro configurazioni, non risultati
automatici dell'ambiente dipendente dai tempi di visita.

## Configurazione e controlli disponibili

Parametri in `configs/phase2_assumptions.json`, sezione travel. La preparazione
scrive parametri lognormali e tempi base in
`data/processed/phase2/travel_reference.json`. L'audit controlla analiticamente
media e CV del fattore, F = 1 in REGULAR, positività dei tempi base e
ricostruzione dei gap GTFS con i 15 secondi. Non è un test Monte Carlo né una
validazione empirica.

Geometria condivisa, capolinea, precedenze e stati iniziali sono specificati
nel contratto operativo. Restano in Fase 3 implementazione e gate dei valori
effettivamente generati. Il CV richiede sensibilità separata dall'incertezza
Monte Carlo.

Documenti collegati: [input](phase2_inputs.md), [modello completo](network_queue_model.md),
[riferimento stabile](non_overloaded_route_formulas.md).
