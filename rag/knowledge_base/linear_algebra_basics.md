## Linear Algebra Basics

### Matrix Operations
- Addition: `(A + B)_{ij} = A_{ij} + B_{ij}` (same dimensions only)
- Scalar multiplication: `(kA)_{ij} = k * A_{ij}`
- Multiplication: `(AB)_{ij} = Σ_k A_{ik} * B_{kj}` (columns of A = rows of B)
- `AB ≠ BA` in general

### Transpose
- `(A^T)_{ij} = A_{ji}`
- `(AB)^T = B^T * A^T`

### Determinant (2×2)
`det [[a,b],[c,d]] = ad - bc`

### Determinant (3×3) — Cofactor Expansion
`det(A) = a₁₁(a₂₂a₃₃ - a₂₃a₃₂) - a₁₂(a₂₁a₃₃ - a₂₃a₃₁) + a₁₃(a₂₁a₃₂ - a₂₂a₃₁)`

### Cramer's Rule
For `Ax = b` where A is n×n with `det(A) ≠ 0`:
`x_i = det(A_i) / det(A)`
where `A_i` is A with column i replaced by b.

### Inverse of a 2×2 Matrix
`A⁻¹ = (1/det(A)) * [[d, -b], [-c, a]]`
A matrix is invertible iff `det(A) ≠ 0`.

### Eigenvalues
Eigenvalues λ satisfy `det(A - λI) = 0` (characteristic equation).
