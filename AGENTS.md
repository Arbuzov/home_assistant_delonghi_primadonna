Always ensure linting and tests pass:

- Run `isort --check-only custom_components/delonghi_primadonna`.
- Run `flake8 custom_components/delonghi_primadonna`.
- Run `pytest`.

Only commit changes when these checks succeed.

Increase the patch version exactly once per change request. If a version bump has
already been applied for this request, leave the version unchanged in further
commits. For example, if the current version is `1.0.0`, set it to `1.0.1` and
keep that value throughout the merge.
