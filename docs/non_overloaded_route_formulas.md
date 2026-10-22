# Formulazioni medie della tratta in regime non sovraccarico

Data: 2026-10-16. Stato: riferimento matematico per la verifica del modello
con posti disponibili variabili. Nessuna simulazione eseguita per il documento.

## 1. Scopo e dominio di validità

Raccogliere le formulazioni concordate per occupazione, discese, posti
disponibili, imbarchi e tempo a bordo. I posti disponibili non sono imposti
dall'esterno: derivano dal carico trasportato dalle fermate precedenti.

Qui «non sovraccarico» significa un regime stabile delle code, con medie
finite e senza accumulo persistente. Non basta osservare un riempimento medio
inferiore al 100%. La stabilità è un'ipotesi di queste formule, non un risultato
dimostrato da esse.

Il riferimento considera:

1. Una linea in un verso con percorso semplice di m fermate ordinate,
   numerate da 1 a m, senza varianti, fermate ripetute o restrizioni di salita
   e discesa nelle posizioni interne.
2. Bus che iniziano il percorso vuoti, con capacità C fissa e uguale per tutti
   i mezzi. C non varia durante la corsa.
3. Passaggi periodici ogni h minuti a ciascuna fermata, senza sorpassi; per il
   riferimento dei tempi si usano durate deterministiche fra fermate.
4. Arrivi Poisson con tasso costante lambda_i alla fermata i, per i < m.
   Nessun arrivo di nuovi viaggiatori al capolinea finale. I processi alle
   diverse origini sono indipendenti nel riferimento.
5. Destinazione assegnata all'arrivo, uniforme fra le fermate successive e
   indipendente dalle scelte degli altri passeggeri. FIFO senza selezione
   della destinazione: tutti i bus servono tutte le fermate successive.
6. Nessun abbandono, trasbordo o cambio di linea. Tutti gli arrivi vengono
   infine imbarcati. Discese prima delle salite.
7. Imbarco istantaneo per l'identità che usa la coda presente all'arrivo.
   Le identità di conservazione restano valide anche con sosta, ma tempi,
   intervalli e insieme dei passeggeri imbarcabili devono essere ridefiniti.

Queste ipotesi costruiscono un riferimento della tratta a capacità finita,
non una soluzione esatta della rete GTFS con tutte le sue caratteristiche.
La scelta uniforme delle destinazioni non implica tassi uguali alle origini:
lambda_i uguali è un'ulteriore specializzazione, usata solo dove dichiarata.

## 2. Notazione

| Simbolo | Definizione | Unità |
|---|---|---|
| m | Numero di fermate del percorso | — |
| i, a, j | Fermata corrente, origine, destinazione | — |
| k | Indice della corsa | — |
| C | Capacità fissa di ciascun autobus | passeggeri |
| h | Intervallo fra passaggi | minuti |
| lambda_i | Tasso degli arrivi alla fermata i | passeggeri/minuto |
| N_i^- | Occupazione prima delle discese alla fermata i | passeggeri |
| D_i | Persone che scendono in i | passeggeri |
| S_i | Persone rimaste a bordo dopo le discese | passeggeri |
| R_i | Posti disponibili dopo le discese, prima delle salite | passeggeri |
| Q_i | Coda subito prima dell'imbarco in i | passeggeri |
| B_i | Persone imbarcate in i | passeggeri |
| N_i^+ | Occupazione alla partenza da i | passeggeri |
| T_serv | Tempo a bordo del singolo passeggero | minuti |
| W_q | Attesa del passeggero prima della salita | minuti |

Le variabili senza indice k si riferiscono a una corsa osservata nel regime
stabile ai passaggi della fermata indicata. Le medie sono medie fra passaggi,
non automaticamente medie temporali. S_i è un conteggio; T_serv è un tempo:
si evita di usare la stessa lettera per entrambe le quantità.

## 3. Bilanci esatti per ciascuna visita

Le seguenti identità non richiedono stabilità:

    S_i   = N_i^- - D_i
    R_i   = C - S_i
    B_i   = min(Q_i, R_i)
    N_i^+ = S_i + B_i.

Il minimo presuppone imbarco istantaneo e compatibilità di tutti i presenti.
Fra due fermate non ci sono salite o discese:

    N_(i+1)^- = N_i^+.

Quindi:

    E[B_i] = E[N_i^+] - E[S_i]
           = E[N_(i+1)^-] - E[S_i].

Non usare N_(i+1)^+: comprende anche il servizio nella fermata successiva.

## 4. Conservazione del flusso in regime stabile

Gli arrivi medi fra passaggi alla fermata i sono lambda_i h. In regime
stabile, senza abbandoni, gli imbarchi medi devono coincidere:

    E[B_i] = lambda_i h,           1 <= i < m.

È ammesso che qualcuno debba aspettare più bus: l'uguaglianza riguarda il
flusso medio, non il servizio al primo passaggio. Al capolinea finale B_m = 0.

Questa relazione è il punto di partenza delle formule di occupazione.
Ritrovarla sostituendo tali formule è una verifica algebrica di coerenza,
non una dimostrazione indipendente della stabilità.

## 5. Probabilità di permanenza e discesa

Per chi arriva alla fermata a:

    P(destinazione = j | origine = a) = 1/(m-a),   j = a+1,...,m.

Prima delle discese in i > a, rimane a bordo chi ha destinazione >= i:

    P(destinazione >= i | origine = a) = (m-i+1)/(m-a).

Dopo le discese in i >= a, rimane chi ha destinazione > i:

    P(destinazione > i | origine = a) = (m-i)/(m-a).

Per una persona già a bordo prima di i, la probabilità condizionata di
scendere è 1/(m-i+1). In questo riferimento con ammissione indipendente dalla
destinazione residua, la corrispondente legge aggregata è:

    D_i | N_i^- = n ~ Binomiale(n, 1/(m-i+1)).

In particolare:

    E[D_i] = E[N_i^-]/(m-i+1)
    E[S_i] = (m-i)/(m-i+1) E[N_i^-].

Questo non implica N_i^- ~ Binomiale(C,p). Nel simulatore D_i si ottiene
contando le destinazioni già assegnate, senza una seconda estrazione.

## 6. Occupazione media prima e dopo il servizio

Ogni origine a contribuisce con gli imbarchi medi lambda_a h moltiplicati
per la probabilità di permanenza. Si ottiene:

    E[N_i^-] = h somma(a=1,...,i-1)
                 lambda_a (m-i+1)/(m-a),        1 <= i <= m.

Dopo il servizio, per i < m:

    E[N_i^+] = h somma(a=1,...,i)
                 lambda_a (m-i)/(m-a).

Ai confini:

    E[N_1^-] = 0
    E[N_m^+] = 0
    E[D_m]   = E[N_m^-].

Si verifica inoltre E[N_i^+] = E[N_(i+1)^-]. Non assumere invece che
E[N_i^-] = E[N_(i+1)^-]: richiederebbe imbarchi medi uguali alle discese
medie in quella fermata.

### Tassi uguali alle origini

Se lambda_a = lambda per tutte le prime m-1 fermate:

    E[N_i^-] = lambda h (m-i+1)
                somma(a=1,...,i-1) 1/(m-a)

    E[N_i^+] = lambda h (m-i)
                somma(a=1,...,i) 1/(m-a),       i < m.

## 7. Posti disponibili e imbarchi medi

Per linearità dell'attesa:

    E[R_i] = C - E[N_i^-] + E[D_i]
           = C - (m-i)/(m-i+1) E[N_i^-].

Sostituendo l'occupazione:

    E[R_i] = C - h somma(a=1,...,i-1)
                         lambda_a (m-i)/(m-a).

Si può dunque calcolare la disponibilità media senza imporre R_i costante.
Dal bilancio della visita:

    E[min(Q_i, C-S_i)] = E[N_i^+] - E[S_i] = lambda_i h,   i < m.

Non è stata usata l'uguaglianza generalmente falsa:

    E[min(Q_i,R_i)] = min(E[Q_i],E[R_i]).

Conoscere E[R_i] e E[B_i] non determina E[Q_i] o E[W_q]: sistemi con gli
stessi flussi e disponibilità media possono avere code e attese diverse.
Non usare E[R_i] come c fisso nella serie del caso controllato senza
dichiarare esplicitamente l'approssimazione.

## 8. Tempo medio a bordo

Siano t_ij i tempi deterministici fra salita in i e discesa in j:

    E[T_serv | origine = i] = (1/(m-i)) somma(j=i+1,...,m) t_ij.

Con Lambda = somma(i=1,...,m-1) lambda_i > 0, la conservazione del flusso
permette di pesare per i tassi alle origini:

    E[T_serv] = (1/Lambda) somma(i=1,...,m-1)
                              lambda_i E[T_serv | origine = i].

Se ogni tratto dura tau:

    E[T_serv | origine = i] = tau (m-i+1)/2.

Se anche i tassi sono uguali:

    Lambda = (m-1)lambda
    E[T_serv] = tau (m+2)/4.

Questo tempo esclude l'attesa prima della salita. Se il servizio introduce
ritardi e soste dipendenti dal carico, i t_ij non sono più gli stessi tempi
deterministici del riferimento e queste sostituzioni non sono automatiche.

## 9. Occupazione media dell'intera tratta

Sia tau_i il tempo fisso sul tratto i -> i+1 e T_r la somma dei tau_i.
Con servizio istantaneo alle fermate, la media per tempo di percorrenza è:

    N_barra = (1/T_r) somma(i=1,...,m-1) tau_i E[N_i^+].

Con tratti di uguale durata tau:

    N_barra = (1/(m-1)) somma(i=1,...,m-1) E[N_i^+].

Con tassi uguali lambda e tratti di uguale durata:

    N_barra = lambda h (m+2)/4.

Per l'intera linea in quel verso, Little fornisce:

    L_bordo = Lambda E[T_serv].

L_bordo conta i passeggeri contemporaneamente presenti su tutti i bus.
Con frequenza 1/h e durata fissa T_r, il numero medio di bus presenti è
M = T_r/h e N_barra = L_bordo/M, con media pesata per tempo-bus.

Per bus identici, il grado medio di riempimento è:

    u_barra = N_barra/C.

Nel caso omogeneo:

    u_barra = lambda h (m+2)/(4C).

Non identificare questo indicatore con lambda E[T_serv] di una coda a un
solo server. Non è una condizione sufficiente di stabilità delle code.

## 10. Esempio algebrico illustrativo

Supponiamo m = 5, lambda_i = 1 passeggero/minuto per i < 5, h = 10 minuti,
C = 40 e tau = 2 minuti. I valori sono illustrativi e il regime stabile è
assunto; la tabella non ne costituisce una prova.

| Fermata i | E[N_i^-] | E[D_i] | E[R_i] | E[B_i] | E[N_i^+] |
|---|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 40 | 10 | 10 |
| 2 | 10 | 2.5000 | 32.5000 | 10 | 17.5000 |
| 3 | 17.5000 | 5.8333 | 28.3333 | 10 | 21.6667 |
| 4 | 21.6667 | 10.8333 | 29.1667 | 10 | 20.8333 |
| 5 | 20.8333 | 20.8333 | 40 | 0 | 0 |

Ulteriori riferimenti:

    E[T_serv] = 3.5 minuti
    N_barra   = 17.5 passeggeri per bus
    u_barra   = 0.4375
    Lambda    = 4 passeggeri/minuto
    L_bordo   = 14 passeggeri
    T_r       = 8 minuti
    M         = 0.8 bus mediamente presenti.

M è una media temporale e può non essere intero: la tratta dura meno
dell'intervallo fra partenze. La tabella è calcolata dalle formule e non
contiene risultati di simulazione.

## 11. Verifica, stabilità e limiti

Le previsioni devono rispettare E[N_i^-] <= C, E[N_i^+] <= C e
E[B_i] <= E[R_i]. Una violazione invalida le ipotesi usate per quello
scenario. Il rispetto di tali limiti da solo non dimostra stabilità.

Per il confronto simulativo:

- Configurare lo stesso percorso, C, h, lambda_i, destinazioni e tempi.
- Confrontare medie ai passaggi con medie ai passaggi e occupazione temporale
  con occupazione temporale; non mescolare pesi e denominatori.
- Analizzare il transitorio e usare repliche indipendenti con incertezza
  statistica. Non attendersi uguaglianza numerica esatta delle medie.
- Verificare i bilanci su ciascuna replica, anche durante il transitorio.
- Non dedurre la stabilità soltanto dalle medie di occupazione: esaminare
  l'andamento delle code e la domanda rispetto al servizio sui tratti critici.

Su una finestra finita il bilancio generale è:

    Q_i(T) - Q_i(t0) = A_i[t0,T) - B_i[t0,T).

Pertanto l'uguaglianza tra flusso entrante e servito non va imposta se la
coda cambia mediamente fra inizio e fine. In sovraccarico E[B_i] non può
essere sostituito da lambda_i h e le formule di occupazione di questo
documento non si applicano come previsioni stazionarie.

Con fasce di 30 minuti, varianti, flotta mista, tempi casuali e soste non
istantanee, conservare i bilanci esatti del modello generale. Applicare
queste espressioni soltanto in configurazioni che rispettano le ipotesi;
eventuali approssimazioni locali per fascia devono essere dichiarate e
non presuppongono un equilibrio istantaneo al cambio del tasso.

## 12. Collegamenti

Le espressioni sono derivate dai bilanci, dalla scelta uniforme della
destinazione e dalle ipotesi elencate: non sono formule M/M/C applicate al bus.

- [Modello completo e misure finite](network_queue_model.md).
- [Caso controllato: coda e attesa con posti disponibili fissi](controlled_queue_model.md).
- [Specifica concettuale e decisioni aperte](model_spec.md).
- [Protocollo statistico](statistical_protocol.md).
