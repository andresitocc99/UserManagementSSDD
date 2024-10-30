"""Needed classes for implementing the Manager interface."""

from typing import Optional

import Ice
import IceStorm
import UsersManager as um
from usersmanager.session import Session
from usersmanager.delayed_response import ManagerQuery, ManagerQueryResponse
import json
import os
import traceback
import threading


class Manager(um.Manager):
    """Skeleton for the Manager implementation."""

    def __init__(self,communicator,topic_manager):
        self.users = {}
        self.sessions = {}
        self.communicator = communicator
        self.topic_manager = topic_manager

        self.topic = None
        self.setup_ice_storm()
        self.filename = "users.json"
        self.load_users_from_file(self.filename)

    def save_users_to_file(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.users, file)

    def load_users_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                self.users = json.load(file)
        except json.JSONDecodeError:
            # Si el archivo está vacío o no tiene un JSON válido, inicializa self.users como un diccionario vacío
            self.users = {}
            print(f"{filename} estaba vacío o corrupto. Inicializando como un diccionario vacío.")
        

    def setup_ice_storm(self):
        """Setup IceStorm TopicManager and event topic."""
        try:
            # Obtener o crear el canal de eventos "UserEvents"
            try:
                self.topic = self.topic_manager.retrieve("UserEvents")
            except IceStorm.NoSuchTopic:
                self.topic = self.topic_manager.create("UserEvents")

            # Configurar como publicador
            self.publisher = um.ManagerQueryPrx.uncheckedCast(self.topic.getPublisher())

            # Configurar como suscriptor
            subscriber_adapter = self.communicator.createObjectAdapter("SubscriberAdapter")
            subscriber = ManagerQuery(self.users, self.sessions)  # Implementación de la interfaz ManagerQuery
            subscriber_proxy = subscriber_adapter.addWithUUID(subscriber)
            subscriber_adapter.activate()
            
            self.topic.subscribeAndGetPublisher({}, subscriber_proxy)
            print("Suscrito al topic 'UserEvents' para recibir mensajes.")

        except Exception as e:
            print(f"Error al configurar IceStorm: {e}")
            traceback.print_exc()

    def login(self, username: str, password: str, current: Optional[Ice.Current] = None) -> um.SessionPrx:
        """Create and return a Session object proxy if the credentials are valid."""
        if username in self.users and self.users[username] == password:
            # Crear una nueva sesión para el usuario
            session = Session(username)
            session_id = session.getSessionID()  # Suponiendo que hay un método para obtener el ID de sesión
            self.sessions[session_id] = session

            # Crear el adaptador si no está creado
            adapter = current.adapter

            # Agregar la sesión al adaptador y crear el proxy
            proxy = adapter.addWithUUID(session)
            
            # Convertir a um.SessionPrx y devolver el proxy
            return um.SessionPrx.checkedCast(proxy)
        else:
            # Publicar un evento para consultar a otras instancias
            try:
                response_event = threading.Event()  # Para esperar la respuesta
                callback_adapter = self.communicator.createObjectAdapter("callbackAdapter")  # Adaptador sin nombre específico
                callback = ManagerQueryResponse(response_event)  # Callback con el evento
                proxy_callback = callback_adapter.addWithUUID(callback)
                callback_adapter.activate()

                topic = self.get_or_setup_topic()

                publisher = self.topic.getPublisher()
                query_publisher = um.ManagerQueryPrx.uncheckedCast(publisher)

                query_publisher.login(username, password, um.ManagerQueryResponsePrx.uncheckedCast(proxy_callback))

                print(f"Evento de verificación de login para usuario '{username}' publicado.")
                
                # Esperar la respuesta hasta 5 segundos antes de lanzar la excepción
                if not response_event.wait(timeout=5):
                    # Si después de 5 segundos no hay respuesta, lanzar una excepción
                    raise um.Unauthorized("Usuario desconocido o credenciales inválidas.")
                
                print(f"Evento de verificación de login para usuario '{username}' publicado.")
            except Exception as e:
                print(f"Error al publicar el evento de login: {e}")

            # Esperar la respuesta del canal (esto debería manejarse de forma asíncrona)
            raise um.Unauthorized("Credenciales inválidas o usuario desconocido.")

    def createUser(self, username: str, password: str, current: Optional[Ice.Current] = None) -> um.SessionPrx:
        """Create a new user and perform a login, returning a Session proxy."""
        if username in self.users:
            raise um.Unauthorized(f"El usuario '{username}' ya existe.")

        try:
            response_event = threading.Event()
            callback_adapter = self.communicator.createObjectAdapter("")  # Adaptador callback
            callback = ManagerQueryResponse(response_event)
            proxy_callback = callback_adapter.addWithUUID(callback)
            callback_adapter.activate()

            # Publicar un evento de verificación de usuario en el canal de IceStorm
            self.publisher.checkUsername(username, um.ManagerQueryResponsePrx.uncheckedCast(proxy_callback))
            print(f"Evento de verificación del nombre de usuario '{username}' publicado.")

            if not response_event.wait(timeout=5):
                print(f"No se recibió respuesta en 5 segundos, procediendo a crear el usuario '{username}'.")

                # Registrar el nuevo usuario
                self.users[username] = password

                # Crear una nueva sesión para el usuario recién creado
                session = Session(username)
                session_id = session.getSessionID()
                self.sessions[session_id] = session

                proxy = current.adapter.addWithUUID(session)
                self.save_users_to_file(self.filename)
                return um.SessionPrx.checkedCast(proxy)
            else:
                raise um.Unauthorized(f"El usuario '{username}' ya existe en otra instancia.")

        except Exception as e:
            print(f"Error al publicar el evento de verificación del nombre de usuario: {e}")
            traceback.print_exc()
            raise um.Unauthorized(f"Error al verificar si el usuario ya existe: {e}")

    def removeUser(self, active_session: um.SessionPrx, current: Optional[Ice.Current] = None) -> None:
        """Delete a user from the database, if the session is valid."""

        # Verificar si la sesión está activa llamando al método remoto a través del proxy
        if not active_session.isAlive():
            raise um.SessionExpired("La sesión ha expirado.")

        # Obtener el nombre de usuario de la sesión activa llamando a través del proxy
        username = active_session.getUser()  # Llamada a través del proxy para obtener el nombre del usuario

        # Si el usuario existe localmente, eliminarlo directamente
        if username in self.users:
            # Eliminar al usuario de la base de datos local
            del self.users[username]

            # Eliminar la sesión de las sesiones activas usando el nombre del usuario
            session_to_remove = None
            for session_id, session in self.sessions.items():
                if session.getUser() == username:
                    session_to_remove = session_id
                    break

            if session_to_remove:
                del self.sessions[session_to_remove]
                self.save_users_to_file(self.filename)

            print(f"Usuario '{username}' eliminado exitosamente de la instancia local.")
            return

        try:
            response_event = threading.Event()
            callback_adapter = self.communicator.createObjectAdapter("")
            callback = ManagerQueryResponse(response_event)
            proxy_callback = callback_adapter.addWithUUID(callback)
            callback_adapter.activate()

            publisher = self.topic.getPublisher()
            query_publisher = um.ManagerQueryPrx.uncheckedCast(publisher)
            query_publisher.removeUserBySession(active_session, um.ManagerQueryResponsePrx.uncheckedCast(proxy_callback))

            print(f"Consulta de eliminación de usuario '{username}' enviada.")

            # Esperar la respuesta hasta 5 segundos antes de lanzar la excepción
            if not response_event.wait(timeout=5):
                raise um.Unauthorized(f"No se recibió respuesta para la eliminación de usuario '{username}'.")

        except Exception as e:
            print(f"Error al enviar la consulta de eliminación de usuario: {e}")

    def verifySession(self, session: um.SessionPrx, current: Optional[Ice.Current] = None) -> bool:
        """Check if the Session is legitimate."""
        session_id = session.getSessionID()
        # Verificar si la sesión existe en las sesiones locales
        if session_id in self.sessions and self.sessions[session_id].isAlive():
            print(f"Sesión '{session_id}' verificada localmente como legítima.")
            return True

        # Si la sesión no está en las sesiones locales, consultar otras instancias
        try:
            # Configurar el callback y el evento para esperar la respuesta
            response_event = threading.Event()
            callback_adapter = self.communicator.createObjectAdapter("")  # Adaptador sin nombre específico
            callback = ManagerQueryResponse(response_event)
            proxy_callback = callback_adapter.addWithUUID(callback)
            callback_adapter.activate()

            publisher = self.topic.getPublisher()
            query_publisher = um.ManagerQueryPrx.uncheckedCast(publisher)

            # Enviar la consulta para verificar la sesión
            query_publisher.checkSession(session, um.ManagerQueryResponsePrx.uncheckedCast(proxy_callback))
            print(f"Evento de verificación de sesión '{session_id}' publicado.")

            # Esperar la respuesta hasta 5 segundos
            if response_event.wait(timeout=5):
                return True  # La sesión fue verificada como legítima por otra instancia

        except Exception as e:
            print(f"Error al publicar el evento de verificación de sesión: {e}")

        # Si no se recibe respuesta en 5 segundos, se asume como ilegítima
        print(f"La sesión '{session_id}' no fue verificada y se considera ilegítima.")
        return False
