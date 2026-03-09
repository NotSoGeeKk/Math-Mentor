## Integration

### Standard Integrals
- `∫ x^n dx = x^(n+1)/(n+1) + C` (n ≠ -1)
- `∫ 1/x dx = ln|x| + C`
- `∫ e^x dx = e^x + C`
- `∫ sin x dx = -cos x + C`
- `∫ cos x dx = sin x + C`
- `∫ sec²x dx = tan x + C`

### Integration by Parts
`∫ u dv = uv - ∫ v du`
LIATE rule for choosing u: Logarithmic > Inverse trig > Algebraic > Trig > Exponential

### Substitution
If `∫ f(g(x)) * g'(x) dx`, let `t = g(x)`, then `dt = g'(x) dx`.

### Partial Fractions
For `P(x)/Q(x)` where deg(P) < deg(Q):
- Linear factor `(x-a)` → `A/(x-a)`
- Repeated factor `(x-a)^2` → `A/(x-a) + B/(x-a)^2`
- Irreducible quadratic `(x²+bx+c)` → `(Ax+B)/(x²+bx+c)`

### Definite Integral Properties
- `∫_a^b f(x) dx = -∫_b^a f(x) dx`
- `∫_a^b f(x) dx = ∫_a^c f(x) dx + ∫_c^b f(x) dx`
- If f is even: `∫_{-a}^{a} f(x) dx = 2 ∫_0^a f(x) dx`
- If f is odd: `∫_{-a}^{a} f(x) dx = 0`
