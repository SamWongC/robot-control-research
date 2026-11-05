# Local publication handoff

Suggested repository name: `robot-control-research`.

Suggested description: **Reproducible experiments on delayed control and contact simulation, with frozen benchmarks, numerical audits, and negative results.**

This directory is the upload-ready copy. The original research folder remains unchanged. There is no remote configured and no upload was performed during preparation. The accompanying ZIP contains this directory's public files, not environments or private thesis correspondence.

When ready to publish, create an empty repository in your own GitHub account, then use GitHub Desktop to add this folder and publish it. Review the visible file list before publishing. Use Git rather than manually selecting thousands of files in a browser. A ZIP is a transfer/backup artifact; uploading only the ZIP would not expose the readable repository layout.

The repository currently has no chosen open-source license. Add one only when you have decided the intended reuse terms. The project title intentionally does not imply RA-L acceptance or affiliation with a laboratory.

The full frozen evidence is included to preserve provenance. Large runtime caches and virtual environments are excluded. Future runs belong in ignored `runs/`; do not commit a new collection of outputs over historical files. The release manifest can be regenerated for a new release after intentional changes; it is not expected to validate changed files forever.
