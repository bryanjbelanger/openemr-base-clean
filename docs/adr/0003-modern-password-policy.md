# Modern password policy (NIST 800-63B) over legacy periodic rotation

OpenEMR's password complexity/length/expiration policy exists and is configurable but is currently unset. Many HIPAA-adjacent compliance conventions still expect mandatory 90-day rotation; current NIST 800-63B guidance recommends against forced periodic rotation in favor of length and breach-list screening.

**Decision**: minimum 12-character length, no forced periodic rotation (rotate only on suspected compromise), block passwords found in known-breach lists. No mandatory 90-day expiration.

**Why**: forced rotation is now understood to push users toward weaker, predictable patterns (incrementing a suffix) and doesn't defend against the actual threats — credential stuffing and phishing — the way length and breach-screening do. This deliberately departs from what some auditors expect a HIPAA-covered system to have, so it's recorded here to explain why the "obvious" 90-day rotation isn't present.
