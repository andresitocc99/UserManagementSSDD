# authentication repository template

[![Linters](https://github.com/UCLM-ESI/ssdd-usersmanager/actions/workflows/linters.yml/badge.svg)](https://github.com/UCLM-ESI/ssdd-usersmanager/actions/workflows/linters.yml)
[![Type checking](https://github.com/UCLM-ESI/ssdd-usersmanager/actions/workflows/typechecking.yml/badge.svg)](https://github.com/UCLM-ESI/ssdd-usersmanager/actions/workflows/typechecking.yml)

Template for the SSDD laboratory 2024-2025 (Finalization edition)

## Installation

To locally install the package, just run

```
pip install .
```

Or, if you want to modify it during your development,

```
pip install -e .
```

## Execution

To run the template server, just install the package and run

```
users-manager --Ice.Config=config/users-manager.config
```

## Configuration

This template only allows to configure the server endpoint. To do so, you need to modify
the file `config/users-manager.config` and change the existing line.

For example, if you want to make your server to listen always in the same TCP port, your file
should look like

```
usermanageradapter.Endpoints=tcp -p 10000
```

## Running tests and linters locally

If you want to run the tests and/or linters, you need to install the dependencies for them:

- To install test dependencies: `pip install .[tests]`
- To install linters dependencies: `pip install .[linters]`

All the tests runners and linters are configured in the `pyproject.toml`.

## Continuous integration

This repository is already configured to run the following workflows:

- Ruff: checks the format, code style and docs style of the source code.
- Pylint: same as Ruff, but it evaluates the code. If the code is rated under a given threshold, it fails.
- MyPy: checks the types definitions and the usages, showing possible errors.

If you create your repository from this template, you will get all those CI for free.

## Slice usage

The Slice file is provided inside the `usersmanager` directory. It is only loaded once when the `usersmanager`
package is loaded by Python. It makes your life much easier, as you don't need to load the Slice in every module
or submodule that you define.

The code loading the Slice is inside the `__init__.py` file.