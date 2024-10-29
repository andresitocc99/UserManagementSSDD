"""Delated response mechanism interfaces implementation."""

import UsersManager as um


class ManagerQueryResponse(um.ManagerQueryResponse):
    """Skeleton for the ManagerQueryResponse interface implementation."""

    def __init__(self, callback):
        self.callback = callback  # Método o función que se ejecutará con la respuesta


    def sendSession(self, session, current=None):
        """Responder con una sesión si se encuentra una válida en otra instancia."""
        try:
            print("Sesión encontrada y enviada.")
            self.callback(session)
        except Exception as e:
            print(f"Error al enviar la sesión: {e}")

    def userExists(self, current=None):
        """Responder indicando que el usuario existe en otra instancia."""
        print("El usuario existe en otra instancia.")
        self.callback(True)  # Activar el evento para notificar que el usuario ya existe


    def userRemoved(self, current=None):
        """Responder indicando que el usuario ha sido eliminado en otra instancia."""
        print("El usuario ha sido eliminado en otra instancia.")
        self.callback(True)

    def sessionVerified(self, current=None):
        """Responder indicando que la sesión ha sido verificada en otra instancia."""
        print("La sesión ha sido verificada en otra instancia.")
        self.callback(True)



class ManagerQuery(um.ManagerQuery):
    """Skeleton for the ManagerQuery interface implementation."""

    def __init__(self, local_user_store, active_sessions):
        self.local_user_store = local_user_store
        self.active_sessions = active_sessions

    def create_session(self, username):
        """Crear una nueva sesión para el usuario dado."""
        # Generar una nueva sesión y agregarla a las sesiones activas
        session = um.Session(username)
        session_id = session.getSessionID()
        self.active_sessions[session_id] = session
        return session

    def login(self, username, password, response_rcvr, current=None):
        """Consulta para verificar si el usuario puede iniciar sesión en otra instancia."""
        # Validar entradas
        if not isinstance(username, str) or not isinstance(password, str):
            print("Error: El nombre de usuario y la contraseña deben ser cadenas de texto.")
            return
        if not isinstance(response_rcvr, um.ManagerQueryResponsePrx):
            print("Error: response_rcvr no es un proxy válido de ManagerQueryResponse.")
            return

        try:
            if username in self.local_user_store:
                if self.local_user_store[username] == password:
                    session = self.create_session(username)
                    response_rcvr.sendSession(session)
                else:
                    print(f"Credenciales incorrectas para el usuario {username}")
            else:
                print(f"Usuario {username} no encontrado en esta instancia.")
        except Exception as e:
            print(f"Error al manejar la consulta de login para el usuario {username}: {e}")

    def checkUsername(self, username, response_rcvr, current=None):
        """Consulta para verificar si el nombre de usuario existe en otras instancias."""
        # Validar entradas
        if not isinstance(username, str):
            print("Error: El nombre de usuario debe ser una cadena de texto.")
            return
        if not isinstance(response_rcvr, um.ManagerQueryResponsePrx):
            print("Error: response_rcvr no es un proxy válido de ManagerQueryResponse.")
            return
        try:
            if username in self.local_user_store:
                response_rcvr.userExists()
        except Exception as e:
            print(f"Error al verificar el nombre de usuario {username}: {e}")

    def removeUserBySession(self, active_session, response_rcvr, current=None):
        """Consulta para eliminar al usuario si la sesión es válida en otras instancias."""
        try:
            # Puedes usar `current` para imprimir información adicional sobre la solicitud
            if current:
                print(f"Solicitud recibida desde: {current.con}")

            session_id = active_session.getSessionID()

            # Comprobar si la sesión está activa y pertenece a esta instancia
            if session_id in self.active_sessions and self.active_sessions[session_id].isAlive():
                # Eliminar la sesión activa y el usuario asociado
                del self.active_sessions[session_id]
                del self.local_user_store[active_session.getUser()]
                
                # Llamar al callback para confirmar que el usuario fue eliminado
                response_rcvr.userRemoved()
                print(f"Usuario '{active_session.getUser()}' eliminado y confirmación enviada.")
            else:
                # Si la sesión no pertenece a esta instancia, se ignora la solicitud
                print(f"La sesión '{session_id}' no es válida o no pertenece a esta instancia.")
                
        except Exception as e:
            print(f"Error al intentar eliminar el usuario: {e}")

    def checkSession(self, session, response_rcvr, current=None):
        """Consulta para verificar la validez de la sesión en otras instancias."""
        # Comprobar si el objeto recibido es un proxy de sesión válido
        if not isinstance(session, um.SessionPrx):
            print("La entrada proporcionada no es un proxy de sesión válido.")
            return

        try:
            session_id = session.getSessionID()

            # Verificar si la sesión pertenece a esta instancia
            if session_id in self.active_sessions and self.active_sessions[session_id].isAlive():
                # Llamar al método sessionVerified del objeto callback
                response_rcvr.sessionVerified()
                print(f"Sesión '{session_id}' verificada y confirmada como legítima en esta instancia.")
            else:
                # Si no es propietaria, ignora la solicitud
                print(f"La sesión '{session_id}' no es propiedad de esta instancia, se ignora la solicitud.")
        except Exception as e:
            print(f"Error al verificar la sesión: {e}")
