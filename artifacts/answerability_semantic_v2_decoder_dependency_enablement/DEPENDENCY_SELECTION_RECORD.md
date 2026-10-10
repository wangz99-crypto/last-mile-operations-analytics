# Owner-pinned dependency selection

apache-tvm-ffi 0.1.14 was rejected by the owner because it is yanked. The sole authorized replacement
is 0.1.14.post1, a non-yanked CPython 3.12 Windows AMD64 wheel; its exact downloaded artifact's PyPI
metadata confirms yanked=false. The rejected release was not downloaded or queried.
Pydantic 2.13.5 is explicitly pinned; its verified METADATA requires annotated-types>=0.6.0,
pydantic-core==2.46.5, typing-extensions>=4.14.1, and typing-inspection>=0.4.2.
Owner-authorized new transitives are annotated-types 0.8.0, pydantic-core 2.46.5 and typing-inspection
0.4.4. Existing typing-extensions 4.16.0 satisfies all constraints and is preserved without download
or reinstall. No dependency choice used semantic or benchmark performance. No competing decoder
was assessed. Optional email/timezone/cpp extras are inactive and excluded.
