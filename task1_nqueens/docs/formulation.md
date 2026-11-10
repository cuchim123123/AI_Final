# Formulation: N-Queens as Propositional Logic (R1)

## Variables
`X(r,c)` is True iff square (r,c) (0 ≤ r,c < N) holds a queen. DIMACS id: `r*N + c + 1`, so there are N² variables.

## Constraints
1. **Row ALO:** each row has at least one queen: `(X(r,0) ∨ … ∨ X(r,N-1))`. N clauses.
2. **At-most-one (AMO)** on every row, column, diagonal (`r−c` constant) and anti-diagonal (`r+c` constant): for each pair A≠B on the same line, `¬(A ∧ B)`.
3. Optional: column ALO (redundant; flag `--column-alo`, default off).

Rows ALO + row AMO give exactly one queen per row. Together with column AMO, that makes N queens on N distinct columns, so there are exactly N queens and none attack.

## Constraint-discovery algorithm
Implemented in `ConstraintGenerator.lines()` (`nqueens/constraints.py`).
1. For each square (r,c), compute four keys: `("row",r)`, `("col",c)`, `("diag",r−c)`, `("anti",r+c)`.
2. Append the square to `buckets[key]`.
3. Every bucket with ≥ 2 squares is a `Line` (a set of mutually attacking squares).

Cost: O(N²) bucketing, plus O(Σ k²) to enumerate the pairs of each line.

## Conversion to CNF
`CNFEncoder` (`nqueens/cnf.py`):
- ALO is already a clause.
- AMO uses De Morgan: `¬(A ∧ B) ≡ (¬A ∨ ¬B)`, one binary clause per pair of each line.
- The formula is a conjunction of clauses, so no auxiliary (Tseitin) variables are needed.

## Clause count (default encoding)

`N + 2·N·C(N,2) + 4·C(N,3) + 2·C(N,2)`, which is Θ(N³). For N=4 this is 80; for N=8 it is 736. Tests check it against the encoder for N=4..10, with and without column ALO (which adds N).

## Optional optimization: sequential-counter AMO encoding
`SequentialCounterAMO` (`nqueens/amo.py`) replaces the pairwise clauses of a line of k squares x_1..x_k with k−1 auxiliary variables s_i ("some x_j with j ≤ i is True") and 3k−4 clauses:

```
(¬x_1 ∨ s_1)
(¬x_i ∨ s_i), (¬s_{i-1} ∨ s_i), (¬x_i ∨ ¬s_{i-1})   for 1 < i < k
(¬x_k ∨ ¬s_{k-1})
```

This makes the formula Θ(N²) instead of Θ(N³) (for N=4: 112 clauses, which is more than the pairwise 80; for N=64: 47,692 vs 428,800). It is logically equivalent on the board variables; the tests enumerate all solutions of N=6 with both encodings. Experiments show it makes Glucose *slower* (see the README).

## Min-Conflicts representation
The local search uses one queen per column (`rows[c]`), the standard Lecture 08 formulation. It admits the same set of solutions as the SAT model, but it builds the row/column constraint into the representation instead of using clauses.
