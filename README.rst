========================================
 Deadline scopes for synchronous Python
========================================

This is a proof-of-concept implementation of Trio-style cancel scopes
for synchronous Python code, as described in my post `Timeouts and
cancellation for humans
<https://vorpus.org/blog/timeouts-and-cancellation-for-humans/>`__. It
makes it easy to implement abstractable, composable, user-friendly
timeout support.

Compared to Trio's cancel scopes, this library has a limitation: it
only supports time-based cancellation, not cancellation in response to
arbitrary events (that is, there's no ``cancel_scope.cancel()``
method) – that's why I call it "deadline scopes" instead of "cancel
scopes". This limitation is imposed by the underlying Python standard
library primitives it uses. However, this mostly isn't a big deal,
since if a single-threaded synchronous program is stuck inside some
blocking operation, then who would call cancel anyway?

This is an experiment, and I'm not sure how much time I'll spend
developing it further – see `Trio <https://trio.readthedocs.io>`__ for
a more complete Python I/O solution. But if you want to pick it up and
run with it, then go for it. Or I guess it wouldn't be too hard to add
support to ``requests``, since `we're working on rewriting its I/O
layer anyway... hmm <https://github.com/njsmith/urllib3/issues/1>`__.


Example
=======

.. code-block:: python

   from deadline_scopes import deadline_socket, fail_after

   sock = deadline_socket()  # like socket.socket()

   # 5 second timeout on everything inside this block
   with fail_after(5):
       # Make a request to http://httpbin.org/delay/10, which should
       # take 10 seconds to complete
       print("connection")
       sock.connect(("httpbin.org", 80))
       print("sending")
       sock.sendall(b"GET /delay/10 HTTP/1.1\r\nHost: httpbin.org\r\n\r\n")
       while True:
           # Read and discard body
           data = sock.recv(1024)
           print(data)
           if not data:
               break

See the code for more details.
