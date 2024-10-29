"""Needed classes for implementing the Session interface."""

import UsersManager as um
import uuid
import time


class Session(um.Session):
    """Skeleton for the Session implementation."""
    
    def __init__(self, username):
        self.username = username
        self.session_id = str(uuid.uuid4())  # Generar un identificador único para la sesión
        self.creation_time = time.time()  # Almacenar el tiempo de creación de la sesión
        self.alive = True

    def getUser(self, current=None) -> str:
        """Devuelve el nombre del usuario asociado con la sesión."""
        return self.username

    def isAlive(self, current=None) -> bool:
        """Verifica si la sesión aún es válida (menos de 2 minutos desde la creación o última renovación)."""
        # Comprobar si la sesión sigue siendo válida (tiempo desde la creación menor a 120 segundos)
        return (time.time() - self.creation_time) < 120

    def refresh(self, current=None) -> None:
        """Extiende la validez de la sesión si aún está activa."""
        # Verificar si la sesión sigue activa antes de extenderla
        if not self.isAlive(current):
            raise um.SessionExpired("La sesión ha expirado y no puede ser renovada.")
        
        # Extender el tiempo de validez reiniciando el temporizador de 2 minutos
        self.creation_time = time.time()
        print(f"Sesión renovada para el usuario {self.getUser(current)} hasta dentro de 2 minutos.")

    def getSessionID(self, current=None) -> str:
        """Devuelve el ID único de la sesión."""
        return self.session_id
