"""remotetypes server application."""

import logging
import Ice
import IceStorm
import traceback
import os
import json

from usersmanager.manager import Manager
import sys  # Importar sys para poder utilizar en el bloque __main__

class Server(Ice.Application):
    """Ice.Application for the server."""

    def __init__(self) -> None:
        """Initialise the Server objects."""
        super().__init__()
        self.logger = logging.getLogger(__file__)
        self.filename = "users.json"
        self.check_or_create_users_file(self.filename)

    def check_or_create_users_file(self, filename):
        """Verifica si el archivo de usuarios existe, si no, lo crea vacío."""
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                json.dump({}, file)  # Crea un archivo JSON vacío
            print(f"{filename} no existía y ha sido creado.")


    def run(self, args: list[str]) -> int:
        """Execute the main server actions.

        It will initialise the needed middleware elements in order to execute the server.
        """
        try:
            self.logger.info("Inicializando el servidor...")

            try:
                topic_manager_proxy = self.communicator().stringToProxy("IceStorm/TopicManager:tcp -h localhost -p 10000")
                print(f"Proxy del TopicManager obtenido: {topic_manager_proxy}")

                # Usar uncheckedCast para evitar problemas con el tipo del proxy
                topic_manager = IceStorm.TopicManagerPrx.uncheckedCast(topic_manager_proxy)
                if not topic_manager:
                    raise RuntimeError("No se pudo conectar al TopicManager de IceStorm.")
                else:
                    self.logger.info("Conexión al TopicManager sin verificación de tipo (uncheckedCast).")
                
                # Intentar crear o recuperar el tópico 'UserEvents'
                try:
                    self.topic = topic_manager.retrieve("UserEvents")
                    self.logger.info("Tópico 'UserEvents' recuperado.")
                except IceStorm.NoSuchTopic:
                    traceback.print_exc()
                    self.topic = topic_manager.create("UserEvents")
                    self.logger.info("Tópico 'UserEvents' creado.")
            except Exception as e:
                print(f"Error al configurar IceStorm: {e}")
                traceback.print_exc()
                self.logger.error(f"Error al configurar IceStorm: {e}")
                raise

            # Crear el servant Manager y el adaptador
            manager_servant = Manager(self.communicator(), topic_manager)
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
