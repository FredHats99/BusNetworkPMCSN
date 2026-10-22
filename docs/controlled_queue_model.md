# Modello controllato: una fermata con servizio periodico a capacità finita

Data: 2026-10-16. Stato: specifica matematica per la verifica del simulatore;
nessuna replica simulativa eseguita per questo documento.

## 1. Scopo e perimetro

Costruire un caso con risultati teorici indipendenti dal simulatore, con cui
verificare arrivi, imbarchi, code residue, coda media temporale e attesa media.
La capacità è finita: possono rimanere persone in attesa di corse successive.
Non si cerca una soluzione analitica dell'intera rete.

Il confronto con la matematica verifica l'implementazione sotto ipotesi
condivise. La validazione rispetto al servizio reale richiede evidenze ulteriori.
Le medie simulate devono essere compatibili con la teoria entro l'incertezza
statistica, non coincidere cifra per cifra.

## 2. Ipotesi

- Una fermata, una linea e un verso; tutti i bus sono compatibili con tutti i
  passeggeri in attesa.
- Arrivi secondo un processo di Poisson omogeneo di tasso costante lambda > 0.
  Il caso controllato non comprende i cambi di fascia della domanda.
- Passaggi agli istanti 0, h, 2h, ... con h > 0 deterministico.
- Ogni passaggio offre esattamente c posti, con c intero positivo.
- C è la capacità fisica fissa dell'autobus; 1 <= c <= C. Il carico a monte
  non è simulato: la disponibilità c è imposta dall'esterno.
- Coda FIFO illimitata, nessun abbandono, nessun cambio di linea.
- Imbarco istantaneo: ogni bus prende fino a c persone e riparte.
- Nessuna contesa fra autobus. Gli arrivi esattamente simultanei al bus hanno
  probabilità zero; l'implementazione deve comunque fissare una precedenza.
- Per il transitorio si parte con coda vuota subito dopo il passaggio a t = 0.

Il modello riguarda l'attesa fino all'imbarco. Il viaggio successivo non
influenza questa coda: non occorre assegnare una destinazione per questo test.
Il mix 50–50 fra tipi di bus del modello completo non è attivo in questo caso.

## 3. Notazione

| Simbolo | Significato | Unità |
|---|---|---|
| lambda | Tasso degli arrivi | passeggeri/minuto |
| h | Intervallo fra bus | minuti |
| C | Capacità fisica fissa del bus | passeggeri |
| c | Posti disponibili fissi per passaggio | passeggeri |
| a = lambda h | Arrivi medi fra passaggi | passeggeri |
| A_k | Arrivi nell'intervallo (kh, (k+1)h) | passeggeri |
| X_k | Coda subito dopo il passaggio k | passeggeri |
| Q^-_(k+1) | Coda subito prima del passaggio k+1 | passeggeri |
| B_(k+1) | Imbarchi al passaggio k+1 | passeggeri |
| Q(t) | Coda all'istante t | passeggeri |
| L_q | Coda media temporale stazionaria | passeggeri |
| W_q | Attesa media stazionaria fino alla salita | minuti |

X indica una variabile con la distribuzione stazionaria di X_k, quando esiste.

## 4. Dinamica esatta

Gli incrementi del processo di Poisson sono indipendenti:

    A_k ~ Poisson(a),       a = lambda h.

A_k è indipendente da X_k. A ogni passaggio:

    Q^-_(k+1) = X_k + A_k
    B_(k+1)   = min(c, X_k + A_k)
    X_(k+1)   = max(0, X_k + A_k - c).

Questa è una ricorrenza di Lindley a incrementi A_k - c. Descrive una coda
servita a lotti: il numero imbarcato dipende da coda e posti disponibili.
Non è una coda M/M/C e non si applica direttamente Pollaczek–Khinchine per M/G/1.

Il bilancio, verificabile su ogni traiettoria, è:

    X_K = X_0 + somma(k=0,...,K-1) A_k - somma(k=1,...,K) B_k.

## 5. Carico e stabilità

La capacità offerta media per unità di tempo è c/h. Definiamo:

    rho = lambda h / c = a/c.

Per a < c esiste un regime stazionario con coda media finita. Per a > c la
domanda supera il servizio e la coda diverge nel lungo periodo. Anche a = c,
con arrivi Poisson non degeneri, non esiste una distribuzione stazionaria
propria. I casi a >= c restano studiabili su un orizzonte finito.

rho non è la frazione di tempo di imbarco: l'imbarco qui è istantaneo.
rho < 1 non garantisce assenza di persone lasciate a terra.

## 6. Calcolo diretto della coda residua media

Non è necessario risolvere tutte le probabilità della catena di Markov.
L'identità di Spitzer, applicata al massimo di una passeggiata aleatoria,
fornisce una serie per la media [1].

Sia Z_n il totale degli arrivi in n intervalli:

    Z_n ~ Poisson(n a).

Con x^+ = max(0,x), per a < c:

    E[X] = somma(n=1,...,infinito) E[(Z_n - nc)^+] / n

         = somma(n=1,...,infinito) (1/n)
           somma(j=nc+1,...,infinito)
           (j-nc) exp(-na) (na)^j / j!.

La serie è esatta; tutti i termini sono non negativi. Un'espressione equivalente,
utile quando sono disponibili code Poisson numericamente affidabili, è:

    E[(Z_n-nc)^+] / n
      = a P(Z_n >= nc) - c P(Z_n >= nc+1).

La sottrazione può perdere precisione nelle code estreme: scegliere un metodo
numerico adeguato, senza confondere la formula esatta con la sua valutazione.

### Controllo del troncamento esterno

Per 0 < a < c, poniamo:

    I = c log(c/a) - c + a > 0.

Una maggiorazione di Chernoff dà:

    E[(Z_n-nc)^+] / n <= a exp(-n I).

Se S_K è la somma dei primi K termini:

    0 <= E[X] - S_K <= a exp(-(K+1)I) / (1-exp(-I)).

Questo limite controlla la coda della serie esterna. Errori di arrotondamento
e troncamenti delle somme Poisson richiedono un controllo separato.
Vicino a rho = 1, I diventa piccolo e il calcolo converge più lentamente.

## 7. Medie stazionarie da confrontare

In regime stazionario la coda residua non cresce mediamente; dal bilancio:

    E[B] = a = lambda h.

La coda media prima del passaggio è:

    E[Q^-] = E[X] + a.

A t minuti dal passaggio, con 0 <= t < h:

    E[Q(kh+t)] = E[X] + lambda t.

Integrando su un intervallo completo:

    L_q = E[X] + lambda h / 2.

Per la legge di Little, dato lambda > 0:

    W_q = L_q / lambda = E[X]/lambda + h/2.

La media ai passaggi e quella temporale sono diverse. La periodicità rende
inoltre la media della coda dipendente dalla fase t del ciclo; L_q è la media
sull'intero ciclo. E[X] riguarda precisamente l'istante dopo il bus.

## 8. Confronto finito da coda vuota

Non è necessario presupporre che il transitorio sia terminato. Con X_0 = 0,
la versione finita dell'identità di Spitzer dà:

    E[X_K] = somma(n=1,...,K) E[(Z_n-nc)^+] / n.

È il valore medio dopo esattamente K passaggi, non la media temporale delle
code osservate fino a quel momento. Su T = Kh:

    E[(1/T) integrale(0,T) Q(t) dt]
      = (1/K) somma(k=0,...,K-1) E[X_k] + lambda h/2.

Queste formule permettono un confronto teorico con repliche finite aventi
stesso stato iniziale e stesso orizzonte, anche quando a >= c (K finito).

Per le attese finite non usare automaticamente L_q/lambda come attesa della
coorte entrata entro T. Gestire separatamente chi attende ancora al termine;
un eventuale drenaggio deve specificare se la generazione degli arrivi continua.

## 9. Esempio illustrativo

Valori di esempio, non parametri congelati del progetto:

    lambda = 0.8 passeggeri/minuto
    h      = 10 minuti
    c      = 10 posti per passaggio
    a      = 8
    rho    = 0.8.

La valutazione numerica della serie dà, arrotondando:

| Indicatore | Valore teorico approssimato |
|---|---:|
| E[X], coda residua media | 0.88 passeggeri |
| E[Q^-], coda media prima del bus | 8.88 passeggeri |
| E[B], imbarchi medi per passaggio | 8 passeggeri |
| L_q, coda media temporale | 4.88 passeggeri |
| W_q, attesa media | 6.10 minuti |

I primi 150 termini esterni danno un limite sulla parte esterna restante
inferiore a 3e-14. Questo non è una certificazione dell'errore totale in virgola
mobile. Nessuno dei valori in tabella è un risultato di simulazione.

## 10. Protocollo di verifica del simulatore

1. Fissare lambda, h, c, C, stato iniziale e orizzonte; dichiarare se il
   confronto è finito o stazionario.
2. Calcolare i riferimenti probabilistici senza usare medie estratte dalle
   simulazioni. Conservare tolleranze e controllo dell'errore numerico.
3. Verificare su ogni replica il bilancio dei passeggeri, FIFO, X_k >= 0 e
   0 <= B_k <= c.
4. Registrare distintamente coda dopo/prima del bus, integrale della coda,
   imbarchi e attese individuali. Non mediare soltanto la coda ai passaggi
   per stimare L_q.
5. Confrontare medie di repliche indipendenti e incertezza con i riferimenti.
   Una singola incompatibilità con un IC non prova automaticamente un bug:
   considerare il livello nominale, confronti multipli, errore numerico,
   transitorio e definizioni delle metriche.
6. Usare almeno casi a bassa domanda e prossimi alla capacità; per a >= c
   confrontare soltanto risultati finiti, senza medie stazionarie.

## 11. Rapporto con il modello completo

Nel modello completo i posti liberi al passaggio k sono:

    R_k = C - N_k^- + D_k,

dove N_k^- è l'occupazione prima delle discese e D_k il numero di discese.
C resta fisso per ciascun mezzo. La media è:

    c_barra = E[R_k] = C - E[N_k^-] + E[D_k].

c fisso e c_barra non sono intercambiabili per calcolare esattamente code e
attese. Sostituire R_k con la sua media elimina variabilità e dipendenze ed è
un'approssimazione, non il riferimento esatto del modello completo.

Le destinazioni uniformi servono a modellare le discese nella rete; non sono
necessarie nel riferimento a fermata singola con c imposto. Il tempo medio a
bordo e l'occupazione media della tratta saranno oggetto di un riferimento
distinto. Non identificare il tempo a bordo con h o con una sosta alla fermata.

Questo documento non chiude la Fase 2 e non modifica le scelte del modello
completo su fasce di 30 minuti, varianti, flotta o arrivi durante l'imbarco.

## Riferimenti

[1] A.J.E.M. Janssen e J.S.H. van Leeuwaarden, *Spitzer's identity for discrete
random walks*. Identità per passeggiate aleatorie riflesse, applicabile alla
ricorrenza di Lindley qui specificata:
https://arxiv.org/abs/1710.09670

Le formule Poisson e il limite di Chernoff riportati sopra sono specializzazioni
al caso A_k ~ Poisson(lambda h); l'esempio numerico è un'applicazione locale.

Documenti del progetto: [modello concettuale](model_spec.md),
[protocollo statistico](statistical_protocol.md).
