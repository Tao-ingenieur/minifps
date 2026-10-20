# Repository instructions

- Keep `src/minifps.py` as a small launcher; implement features in focused modules under `src/woodland/`.
- Put virtual environments, exe files, logs and build outputs only in sibling `minifps-local`.
- For every user-facing published change, update `VERSION`, `CHANGELOG.md`, and README's module map and gameplay instructions.
- Follow `CONTRIBUTING.md` for validation, annotated version tags, and GitHub release notes. Preserve existing release tags.
- Changes to scoring or round state must pass `python -m unittest discover -s tests -v` and the engine `--smoke-test`.

- Never commit player save files or profiles. Persistence changes must preserve local high scores, validate imported data, and pass persistence tests.
