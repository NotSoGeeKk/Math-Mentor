## Limits

### Standard Limits
- `lim (x→0) sin(x)/x = 1`
- `lim (x→0) (1 - cos x)/x^2 = 1/2`
- `lim (x→0) tan(x)/x = 1`
- `lim (x→0) (e^x - 1)/x = 1`
- `lim (x→0) ln(1+x)/x = 1`
- `lim (x→∞) (1 + 1/n)^n = e`

### L'Hôpital's Rule
If `lim f(x)/g(x)` gives `0/0` or `∞/∞`, then:
`lim f(x)/g(x) = lim f'(x)/g'(x)`
Can be applied repeatedly if the result is still indeterminate.

### Squeeze Theorem
If `g(x) ≤ f(x) ≤ h(x)` near `a`, and `lim g(x) = lim h(x) = L`, then `lim f(x) = L`.

### Limits at Infinity
- For rational functions `P(x)/Q(x)`: compare leading term degrees.
  - deg(P) < deg(Q) → limit is 0
  - deg(P) = deg(Q) → limit is ratio of leading coefficients
  - deg(P) > deg(Q) → limit is ±∞

### Continuity
`f(x)` is continuous at `x = a` iff `lim (x→a) f(x) = f(a)`.
