
"""
Global variable containing the most recently loaded configuration.
It's literally just a dict (with string keys)

`GLOBAL_CONFIG` should NOT be altered directly. Instead, use the `configure`
context manager or variants like `configure_from_args`.

A "default" config can be achieved by chaining a `configure` with default
values into the modified values.
"""
GLOBAL_CONFIG = dict()

