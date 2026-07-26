"""Third-party data sources that live outside the audited website itself.

Everything here does real network I/O, so -- exactly like ``checks/runner.py``
-- it is deliberately separate from the check modules, which stay pure and
offline-testable.
"""
