# Rules for our final product

1. `hardening-notes.md` holds our main results, our work list, and what every check finds, each under a clear heading. Read it before you start, and write there what you find.
2. Change a file only when our prompt asks for a fix or names the file to write. A check writes only in `hardening-notes.md` and a teammate's own work log; a fix is a separate task.
3. Never fix a problem before we have stated our way and our reason. If we have not, show the evidence, lay out two or three ways, recommend none, and ask. Never write our reasons.
4. Never edit a test to make it pass.
5. Report each problem with what you did, what you saw, and what you expected, and only if you saw it by doing it yourself.
6. Draft only from records (the notes, the commits, the code's output): never invent evidence, and write TODO where a record is missing.
7. A reviewer is a subagent with fresh context: it must not see the chat that did the work.
