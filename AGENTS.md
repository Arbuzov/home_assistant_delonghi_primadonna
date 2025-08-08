Always ensure linting passes:

- Run `isort --check-only custom_components/delonghi_primadonna`.
- Run `flake8 custom_components/delonghi_primadonna`.

Only commit changes when these checks succeed.

Increase hotfix version when making changes to the code. Only one increment is allowed per change request. Multiple commits could be included into single change request. For example, if the current version is `1.0.0`, the next hotfix version should be `1.0.1`.
