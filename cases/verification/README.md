# Elena verification files moved

The unchanged submitted PDF prints the former paths `cases/verification/verify_elena_trends.py` and `cases/verification/elena-verification-output.txt`.

Their current locations are:
- [Verification script](../elena/verification/verify_elena_trends.py)
- [Saved output](../elena/verification/elena-verification-output.txt)
- [PDF exporter](../elena/verification/build_elena_pdf.py)

From the repository's `prof-build-M2/` application folder, run:

```text
uv run python ../cases/elena/verification/verify_elena_trends.py
```

Only location assumptions changed. The verifier still checks the frozen data at commit `208b0375` and its required SHA-256. The submitted PDF was moved without regeneration.
