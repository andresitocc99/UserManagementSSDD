import sys
import os
import Ice

# Añadir el directorio generado por slice2py al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "usersmanager"))

# Importar el módulo generado
import usersmanager_ice

# Acceder al módulo `UsersManager` dentro de `usersmanager_ice`
um = usersmanager_ice._M_UsersManager

def print_menu():
    print("\nSeleccione una acción:")
    print("1. Iniciar sesión (login)")
    print("2. Crear usuario")
    print("3. Eliminar usuario")
    print("4. Verificar legitimidad de sesión")
    print("5. Cerrar programa")

def main():
    with Ice.initialize(sys.argv) as communicator:
        try:
            # Crear un proxy al servidor manager
            proxy = communicator.stringToProxy("manager:tcp -h localhost -p 10002")
            manager = um.ManagerPrx.checkedCast(proxy)

            if not manager:
                raise RuntimeError("Invalid proxy")

            session = None

            while True:
                print_menu()
                option = input("Seleccione la acción que desea realizar: ")

                if option == "1":
                    username = input("Ingrese el nombre de usuario: ")
                    password = input("Ingrese la contraseña: ")
                    try:
                        session = manager.login(username, password)
                        print("Inicio de sesión exitoso.")
                    except um.Unauthorized as e:
                        print(f"Error de autenticación: {e.reason}")

                elif option == "2":
                    username = input("Ingrese el nombre de usuario: ")
                    password = input("Ingrese la contraseña: ")
                    try:
                        session = manager.createUser(username, password)
                        print("Usuario creado exitosamente.")
                    except um.Unauthorized as e:
                        print(f"Error: {e.reason}")

                elif option == "3":
                    # Eliminar usuario
                    if session:
                        try:
                            manager.removeUser(session)
                            print("Usuario eliminado correctamente.")
                            session = None  # Limpiar la sesión eliminada
                        except (um.Unauthorized, um.InvalidUser) as e:
                            print(f"Error al eliminar usuario: {e}")
                    else:
                        print("Inicia sesión para poder eliminar el usuario.") 

                elif option == "4":
                    if session:
                        try:
                            manager.verifySession(session)
                            print("Sesión válida.")
                        except um.Unauthorized as e:
                            print(f"Error: {e.reason}")
                    else:
                        print("Inicia sesión para verificar la legitimidad de la sesión.")
                
                elif option == "5":
                    break
                
                else:
                    print("Opción inválida. Intente de nuevo.")
    
        except Ice.ConnectionRefusedException:
            print("No se pudo conectar al servidor en el puerto 10000. Asegúrate de que el servidor está en ejecución.")

if __name__ == "__main__":
    main()
