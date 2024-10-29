"""remotetypes server application."""

import logging
import Ice
import IceStorm
import traceback

from usersmanager.manager import Manager
import sys  # Importar sys para poder utilizar en el bloque __main__

class Server(Ice.Application):
    """Ice.Application for the server."""

    def __init__(self) -> None:
        """Initialise the Server objects."""
        super().__init__()
        self.logger = logging.getLogger(__file__)

    def run(self, args: list[str]) -> int:
        """Execute the main server actions.

        It will initialise the needed middleware elements in order to execute the server.
        """
        try:
            self.logger.info("Inicializando el servidor...")

            # Crear el servant Manager y el adaptador
            manager_servant = Manager(self.communicator)
            self.logger.info("Manager servant creado.")
            
            # Crear el adaptador de objetos para UsersManager
            adapter = self.communicator().createObjectAdapter("usersmanageradapter")
            self.logger.info("Adaptador creado.")
            
            # Añadir el servant al adaptador y obtener el proxy del objeto
            proxy = adapter.add(manager_servant, self.communicator().stringToIdentity("manager"))
            self.logger.info(f"Proxy configurado: {proxy}")

            # Confirmar que el adaptador se ha activado correctamente
            print(f'Manager proxy disponible en: "{proxy}"')
            self.logger.info('Proxy configurado: "%s"', proxy)

            # Conectar con el TopicManager de IceStorm
            try:
                topic_manager_proxy = self.communicator().stringToProxy("IceStorm/TopicManager:tcp -p 10000")
                topic_manager = IceStorm.TopicManagerPrx.checkedCast(topic_manager_proxy)
                if not topic_manager:
                    raise RuntimeError("No se pudo conectar al TopicManager de IceStorm.")
                self.logger.info("Conectado al TopicManager de IceStorm.")
            except Ice.ConnectionRefusedException as e:
                self.logger.error(f"Error al conectar con el TopicManager de IceStorm: {e}")
                return 1
            except Exception as e:
                self.logger.error(f"Error general al conectar con el TopicManager de IceStorm: {e}")
                return 1

            # Recuperar o crear el canal de eventos "UserEvents"
            try:
                topic = topic_manager.retrieve("UserEvents")
            except IceStorm.NoSuchTopic:
                topic = topic_manager.create("UserEvents")
            self.logger.info("Canal de eventos 'UserEvents' configurado.")

            # Activar el adaptador para permitir conexiones entrantes
            adapter.activate()
            self.logger.info("Adaptador activado. Servidor en espera de conexiones...")
            print("Servidor activado y esperando conexiones...")

            # Esperar la interrupción del servidor
            self.shutdownOnInterrupt()
            self.communicator().waitForShutdown()
            self.logger.info("Servidor cerrado correctamente.")

        except Exception as e:
            traceback.print_exc()
            self.logger.error(f"Error al ejecutar el servidor: {e}")
            return 1
        return 0

if __name__ == "__main__":
    server = Server()
    sys.exit(server.main(sys.argv))
