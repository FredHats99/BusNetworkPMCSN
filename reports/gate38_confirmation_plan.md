# Gate 3.8 — piano di conferma e diagnosi mirata

Solo dati diagnostici v1: 8904 controlli, stima minima 670 nuove repliche per caso per semiampiezze attese entro metà margine; numerosità fissata prima della conferma: **672 per caso, 8064 totali**.

Margini, famiglia e regole decisionali restano quelli v1. Le 384 repliche precedenti non entrano negli IC di conferma. Le stime di dispersione sono incerte; il piano non garantisce né la precisione finale né l'accettazione.

## Scomposizione dei casi critici

| Caso | Arco | Differenza osservata (s) | Composizione riferimenti (s) | Perturbazioni (s) |
|---|---|---:|---:|---:|
| SHARED_D125 / loaded_synthetic − D125 | arc / 81 / 0 / 52 / 309 | -10.021907 | 0.011310 | -10.033217 |
| SHARED_D125 / empty_passengers − D125 | arc / 81 / 1 / 113 / 221 | 7.716366 | 0.052865 | 7.663501 |
| SHARED / empty_passengers − BASE | arc / 81 / 0 / 138 / 99 | -6.274732 | 0.000000 | -6.274732 |
| SHARED_D125 / empty_passengers − D125 | arc / 628 / 0 / 263 / 243 | -6.177822 | 0.000000 | -6.177822 |
| SHARED / empty_passengers − BASE | arc / 87 / 1 / 6 / 3 | -6.125190 | 0.000000 | -6.125190 |
| SHARED / empty_passengers − BASE | arc / 81 / 1 / 113 / 221 | -5.920766 | 0.000000 | -5.920766 |
| SHARED_D125 / loaded_synthetic − D125 | arc / 81 / 1 / 62 / 307 | 5.667139 | -0.046726 | 5.713866 |

Il JSON conserva anche statistiche per replica separate fra chiavi nuove, riusi e bin ambientali. Le celle con osservazioni assenti non sono imputate a zero; sono statistiche descrittive, senza decisioni aggiuntive sui margini.

Consumi finali v1 degli stream 0–3: `[31812118, 31653526, 3915562, 2737232]`. Prefisso della conferma: `33554432` per ciascuno stream, strettamente oltre tutti gli estremi precedenti. La conferma continua gli stati fra tutti i casi.

Una differenza di perturbazione osservata non distingue da sola fluttuazione Monte Carlo e selezione endogena. La nuova campagna indipendente è l'evidenza decisiva secondo il protocollo congelato.
