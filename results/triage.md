# A339592 bounded triage checks (2026-09-25)

No production source, persistent computation state, b-file extension or campaign command was created. Python 3 standard-library disposable CLI calculations only; wall/CPU/RSS were not measured.

## Inputs and mathematical construction

- `M_0=1`; `M_k=M_(k-1)+sum_{t=0}^{k-2} M_t M_(k-2-t)` for `k>=1`, from `M=1+zM+z^2 M^2`.
- For labels `i>j`, an edge iff `[z^(i-j-1)] M(z)^j` is odd. Powers were built by integer coefficient convolution; an edge test used the coefficient parity.
- Enumerated all `2^n` bit masks for each `1<=n<=13`, accepting a mask only when no selected vertex had a selected neighbor. This includes the empty mask.

## Observations

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| count | 2 | 3 | 4 | 7 | 9 | 13 | 17 | 26 | 29 | 48 | 55 | 95 | **104** |
| edges | 0 | 1 | 3 | 4 | 7 | 10 | 14 | 17 | 23 | 26 | 32 | 35 | 42 |

Rows 1–12 agree exactly with the local indexed b-file and the source paper's Table 1. At 13, a second enumeration chose each independent subset of the seven odd vertices and added `2^(number of even vertices nonadjacent to it)`. There were 15 valid odd subsets and this sum was **104**. This checks the counting partition, but both calculations share the coefficient-derived graph.

Even–even adjacency was zero at tested orders 7, 12, 13. Odd-induced self-similarity failed at relabelled pair `(3,1)` (original vertices `(5,1)`), illustrating the source's Motzkin/non-io distinction. The n=13 direct domain has 8192 subsets; the proved consecutive-edge/path bound permits at most 610.

**Classification:** 104 is a finite triage diagnostic, not an admitted result, independent graph-construction verification, official campaign output, or proposed b-file modification.
