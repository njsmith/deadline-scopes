========================================
 Deadline scopes for synchronous Python
========================================

This is a proof-of-concept implementation of Trio-style cancel scopes
for synchronous Python code, as described in XX [link to blog post].
It makes it easy to abstractable, composable, user-friendly timeout
support.

Compared to Trio's cancel scopes, this library does have one
limitation: it only supports time-based cancellation, not cancellation
in response to arbitrary events (that is, there's no
``cancel_scope.cancel()`` method) – that's why I call it "deadline
scopes" instead of "cancel scopes". This limitation is imposed by the
underlying Python standard library primitives it uses. However, this
mostly isn't a big deal, since if a single-threaded synchronous
program is stuck inside some blocking operation, then who would call
cancel anyway?

This is an experiment, and I'm not sure how much time I'll spend
developing it further – see `Trio <https://trio.readthedocs.io>`__ for
a more complete Python I/O solution. But if you want to pick it up and
run with it, then go for it.


Examples
========




Details
=======

Read the source for full details, but roughly:
