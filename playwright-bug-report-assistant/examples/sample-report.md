# Checkout confirmation was not displayed

> Sanitized demonstration output; not a client incident.

## Summary

- Status: failed
- Category: assertion
- Analysis provider: deterministic
- Stability: insufficient history

## Simple explanation

The checkout test expected a confirmation message, but the page displayed a payment error.

## Likely causes

1. The application returned a different value.
2. The assertion may describe older behavior.
3. The page may not have finished updating.

## Related code

`tests/checkout.spec.ts:18` — synthetic demonstration location.
