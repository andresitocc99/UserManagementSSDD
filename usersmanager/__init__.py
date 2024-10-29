"""Package for the remoteset distribution."""

import os

import Ice

try:
    import UsersManager  # noqa: F401

except ImportError:
    slice_path = os.path.join(
        os.path.dirname(__file__),
        "usersmanager.ice",
    )

    Ice.loadSlice(slice_path)
    import UsersManager  # noqa: F401
