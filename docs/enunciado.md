# Laboratorio de Sistemas Distribuidos - 2024/2025 (conv. finalización)

Éste documento es el enunciado de la práctica entregable de la asignatura de Sistemas Distribuídos
del curso 2024/2025 en su convocatoria de finalización.

## Introducción

Se quiere implementar un servicio de gestión de usuarios que pueda ser utilizado por otros sistemas.
Dicho servicio deberá implementarse utilizado el _middleware_ de comunicación ZeroC Ice, utilizando
Python como lenguaje de implementación.

## Requisitos

El servicio de gestión de usuarios debe permitir realizar las siguientes operaciones:

- Gestión de sesiones: un usuario podrá identificarse, obteniendo una sesión que será válida
    durante un tiempo definido.
- Un usuario podrá utilizar el servicio para crear un nuevo usuario identificado por un nombre y una
    contraseña. El servicio comprobará que el nombre de usuario no existe anteriormente en el sistema.
- El servicio debe proporcionar una funcionalidad para verificar que una sesión es legítima, de modo que
    un posible atacante no pueda falsificarla para atacar a otros servicios o suplantar otros usuarios.

Los datos de los usuarios deberán ser almacenados de forma persistente por el servicio, de manera que si
el servicio es reiniciado, no se pierdan los datos de las credenciales de los usuarios. A su vez, las sesiones
no deben ser persistentes entre reinicios.

La validez temporal de cada sesión será de 2 minutos, que podrán ser extendidos siempre y cuando la sesión
esté activa en el momento de solicitarlo y el usuario siga existiendo.

Por último, el servicio se ejecutará de manera redundante, por lo que cada instancia del servicio deberá
sincronzarse con el resto de instancias a través de canales de eventos, de forma que no sea necesario que
cada instancia sepa ninguna información del resto.

## Definición de interfaces

En el fichero Slice se proporciona la definición de las interfaces que deberán ser implementadas.

### `Manager`

Es la interfaz principal del servicio y la única de la que el servicio creará un objeto nada más arrancar.

Éste interfaz proporcionará las funcionalidades para crear y borrar usuarios, crear sesiones y
verificar que una sesión existente es legítima.

```
interface Manager {
    Session* login(string username, string password) throws Unauthorized;
    Session* createUser(string username, string password) throws Unauthorized;
    void removeUser(Session* activeSession) throws SessionExpired, InvalidUser;
    bool verifySession(Session* session);
};
```

- Método `login`: un cliente proporcionará un usuario y contraseña. En caso de ser válidos, el servicio
    creará una sesión (ver interfaz `Session` más adelante) y devolverá un proxy a la misma. En caso de usar
    unas credenciales erróneas, se lanzará la excepción indicada.

- Método `createUser`: al igual que el anterior, el cliente proporcionará un usuario y contraseña. Si el usuario no existe
    anteriormente, se almacenará en la persistencia y se generará una nueva sesión para el mismo. En caso contrario,
    se lanzará la excepción indicada.

- Método `removeUser`: permite eliminar un usuario del sistema. Es necesario que el usuario primero se haya identificado
    y tenga una sesión activa, que será utilizada para verificar que los datos son correctos. Lanzará las excepciones
    correspondientes en cada posible escenario.

- Método `verifyUser`: cumple con la función de verificar que una sesión de usuario es legítima. No comprobará ningún dato sobre
    el usuario o la validez temporal de la sesión, únicamente si esa sesión ha sido generada por una instancia del servicio.

### `Session`

Es la interfaz que representa a una sesión activa de usuario. Se crearán únicamante a través de los métodos `login` y `createUser`
de la interfaz `Manager`, como se ha indicado anteriormente.

```
interface Session {
    idempotent string getUser();
    idempotent bool isAlive();
    void refresh() throws SessionExpired, InvalidUser;
};
```

- Método `getUser`: devolverá el nombre del usuario.
- Método `isAlive`: comprobará el tiempo de validez de la sesión, devolviendo verdadero si han pasado menos de 2 minutos desde
    la creación de la sesión o desde la última renovación. Devolverá falso en todos los demás casos.
- Método `refresh`: si la sesión está activa, ampliará por 2 minutos desde el momento de recepción la validez de la sesión. Si la sesión
    ha expirado o el usuario ha dejado de existir, se lanzarán las excepciones indicadas respectivamente.

## Mecanismo de comunicación entre instancias

Dado que habrá más de una instancia del servicio de gestión de usuarios, se requiere que éstas instancias sean capaces de comunicarse entre ellas.
Para ello, se usará el servicio **IceStorm** para realizar una comunicación indirecta entre ellas a través de un canal de eventos.

Cuando una instancia "A" reciba una petición por parte de un cliente, en ocasiones necesitará consultar con el resto de instancias. Para ello,
enviará una invocación con la consulta al canal de eventos, que será recibido por todas las instancias a la escucha. Dicha consulta incluirá un objeto _callback_ que permitirá enviar la respuesta, si la hubiera.

El envío de consultas se realiza a través de la interfaz `ManagerQuery`, que se describe así:

```
interface ManagerQuery {
    void login(string username, string password, ManagerQueryResponse* responseRcvr);
    void checkUsername(string username, ManagerqueryResponse* responseRcvr);
    void removeUserBySession(Session *activeSession, ManagerqueryResponse* responseRcvr);
    void checkSession(Session *session, ManagerqueryResponse* responseRcvr);
};
```

Si una instancia, a la que llamaremos "B", recibe la consulta y tiene la información necesaria para poder responderla, utilizará el objeto
_callback_ para enviar la respuesta a la instancia "A".

Dicho objecto _callback_ cumplirá con la interfaz siguiente:

```
interface ManagerQueryResponse {
    void sendSession(Session* session);
    void userExists();
    void userRemoved();
    void sessionVerified();
};
```

Si la instancia "A" no recibe ninguna respuesta pasados 5 segundos tras enviar una consulta, deberá actuar en consecuencia dependiendo de
la consulta.


#### Consulta para la identificación de usuarios

Cuando una instancia recibe una petición de `login` de un usuario que no reconoce, deberá enviar una consulta al resto de instancias.
La consulta se realizará a través del método `login` de la interfaz `ManagerQuery`.

- Si la instancia que recibe la consulta no conoce a dicho usuario, simplemente ignorará el mensaje.
- Si la instancia conoce al usuario y las credenciales son correctas, creará un objeto `Session` para el usuario y enviará
    el proxy a través del objeto _callback_, utilizando el método `sendSession`.

Si trascurridos 5 segundos de enviar la consulta no se ha recibido ninguna respuesta, la instancia entenderá que es un usuario desconocido y
rechazará el inicio de sesión.

#### Consulta para la creación de usuarios

Cuando una instancia recibe una petición de `createUser`, debe comprobar que ese usuario no existe previamente en su persistencia,
pero también debe comprobar que no existe en las persistencias de las demás instancias. Para ello, una vez que sabemos que el usuario no
existe en nuestra persistencia, la instancia enviará una consulta a través del método `checkUsername` de la interfaz `Managerquery`.

- Si la instancia que recibe la consulta no conoce ningún usuario con ese identificador, ignorará el mensaje.
- Si la instancia que recibe la consulta tiene registrado a un usuario con ese identificador, realizará la operación `userExists`
    del objeto _callback_ de la interfaz `ManagerQueryResponse`.

Si transcurridos 5 segundos de enviar la consulta no se ha recibido ninguna respuesta, la instancia entenderá que dicho nombre de usuario
no está siendo usado en ninguna otra instancia, por lo que podrá proceder a su creación.

#### Consulta para el borrado de usuario

Cuando una instancia recibe una petición de `removeUser`, debe comprobar si ese usuario existe en su persistencia. Si es así, lo eliminará,
pero si no, enviará una consulta al resto de instanciaws a través del método `ManagerQuery.removeUserBySession`.

- Si la instancia que recibe la consulta no es la propietaria del objeto `Session` recibido, ignorará el mensaje.
- Si la instancia que recibe la consulta es la propietaria del objeto `Session`, procederá a eliminar al usuario de su persistencia. Acto seguido,
    comunicará el borrado del usuario a través de una llamada a la operación `ManagerQueryResponse.userRemoved`.

Si transcurridos 5 segundos de enviar la consulta no se ha recibido ninguna respuesta, la instancia entenderá que dicha `Session` no es válida
en ninguna de las instancias y lanzará la excepción correspondiente como si se tratara de un usuario desconocido.

#### Consulta para la comprobación de la legitimidad de un objeto `Session`

Un cliente u otros servicios pueden necesitar verificar que un determinado objeto `Session`es legítimo. Para ello, consultarán con una instancia
del servicio, pero es posible que dicho objeto `Session` haya sido creado por otra instancia diferente. A través del método
`ManagerQuery.checkSession` la instancia preguntará al resto si alguna reconoce dicho objeto `Session`.

- Si la instancia que recibe la consulta no es la propietaria del objeto `Session` recibido, ignorará el mensaje.
- Si la instancia es la "propietaria" de dicho objeto, entonces invocará al método `ManagerQueryResponse.sessionVerified` del objeto _callback_.

Si transcurridos 5 segundos tras enviar la consulta no se recibe ninguna respuesta, se asumirá que dicho objeto `Session` es desconocido
y, por tanto, ilegítimo.

## Entregable

La práctica se deberá realizar y almacenar en un repositorio Git privado. Dicho repositorio debe ser compartido con los dos profesores de la
asignatura. 

En el repositorio, además, debe aparecer un fichero `README.md` que especifique exactamente cómo debe lanzarse el programa, así como
cualquier otro dato de interés sobre cómo configurar la instancia. También debe incluirse información sobre el formato que se utiliza para
la persistencia.

Se proporciona un repositorio plantilla en GitHub, desde el cuál los alumnos pueden rear su propio repositorio. La plantilla ya contiene muchos
de los requisitos de entrega ya realizados: el fichero `README`, la explicación sobre cómo lanzarlo, el fichero de configuración necesario...

Se recomienda encarecidamente la utilización del repositorio plantilla para la realización del ejercicio.

### Fecha de entrega

En próximas fechas se habilitará una tarea en Campus Virtual para realizar la entrega: únicamente la URL de la página web del repositorio.
La fecha límite de entrega será el día 25 de noviembre de 2024.