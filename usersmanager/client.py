import sys
import os
import Ice

# Añadir el directorio generado por slice2py al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "usersmanager"))

# Importar el módulo generado
import usersmanager_ice

# Acceder al módulo `UsersManager` dentro de `usersmanager_ice`
um = usersmanager_ice._M_UsersManager

def main():
    with Ice.initialize(sys.argv) as communicator:
        try:
            # Crear un proxy al servidor manager
            proxy = communicator.stringToProxy("manager:tcp -h localhost -p 10000")
            manager = um.ManagerPrx.checkedCast(proxy)

            if not manager:
                raise RuntimeError("Invalid proxy")

            # Crear un usuario
            try:
                session = manager.createUser("testuser", "password")
                print("Usuario creado correctamente.")
            except um.Unauthorized as e:
                print(f"Error al crear usuario: {e.reason}")

            # Iniciar sesión
            try:
                session = manager.login("testuser", "password")
                print("Inicio de sesión exitoso.")
            except um.Unauthorized as e:
                print(f"Error de autenticación: {e.reason}")

            # Verificar la sesión
            try:
                is_verified = manager.verifySession(session)
                print(f"Sesión verificada: {is_verified}")
            except Ice.Exception as e:
                print(f"Error al verificar la sesión: {str(e)}")

            # Renovar la sesión
            try:
                session.refresh()
                print("Sesión renovada correctamente.")
            except (um.SessionExpired, um.InvalidUser) as e:
                print(f"Error al renovar la sesión: {str(e)}")
            
        except Ice.ConnectionRefusedException:
            print("No se pudo conectar al servidor en el puerto 10000. Asegúrate de que el servidor está en ejecución.")

if __name__ == "__main__":
    main()
