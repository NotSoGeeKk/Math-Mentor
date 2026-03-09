## Probability Basics

### Fundamental Rules
- `P(A or B) = P(A) + P(B) - P(A and B)`
- `P(A and B) = P(A) * P(B|A)`
- `P(not A) = 1 - P(A)`

### Bayes' Theorem
`P(A|B) = P(B|A) * P(A) / P(B)`

### Conditional Probability
`P(A|B) = P(A ∩ B) / P(B)`, provided `P(B) > 0`

### Permutations & Combinations
- Permutations (order matters): `P(n, r) = n! / (n-r)!`
- Combinations (order doesn't matter): `C(n, r) = n! / [r! * (n-r)!]`
- `C(n, r) = C(n, n-r)`

### Binomial Distribution
For `n` independent trials, each with success probability `p`:
- `P(X = k) = C(n,k) * p^k * (1-p)^(n-k)`
- Mean: `μ = np`
- Variance: `σ² = np(1-p)`

### Independent Events
Events A and B are independent iff `P(A ∩ B) = P(A) * P(B)`
