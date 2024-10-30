# AUTHENTICATION REPOSITORY

Implementation for the SSDD laboratory 2024-2025 (Finalization edition)

## Installation

To locally install the package, just run

```bash
pip install .
```

Or, if you want to modify it during your development,

```bash
pip install -e .
```

## Execution

To run the implementation, run:

1. ```icestorm```:

```bash
. ./run_icestorm
```

2. ```usersmanager```:

```bash
users-manager --Ice.Config=config/users-manager.config
```

3. Run the client which we will work with:

```bash
. ./run_client
```


To run the template server, just install the package and run

```bash
users-manager --Ice.Config=config/users-manager.config
```