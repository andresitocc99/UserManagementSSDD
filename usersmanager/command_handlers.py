"""Module containing the handler functions for CLI commands."""

import logging
import os
import sys

from usersmanager.server import Server


def users_manager_server() -> None:
    """Handle for running the server for users manager."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()  # Asegura que los mensajes se impriman en la consola
        ])

    cmd_name = os.path.basename(sys.argv[0])

    logger = logging.getLogger(cmd_name)
    logger.info("Running %s server...", sys.argv[0])

    try:
        server = Server()
        sys.exit(server.main(sys.argv))
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
