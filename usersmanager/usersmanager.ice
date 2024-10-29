// -*- mode: c++ -*-

module UsersManager {
    exception SessionExpired {};
    exception InvalidUser {
        string user;
    };

    exception Unauthorized {
        string reason;
    }

    interface Session {
        idempotent string getUser();
        idempotent bool isAlive();
        void refresh() throws SessionExpired, InvalidUser;
    };

    interface Manager {
        Session* login(string username, string password) throws Unauthorized;
        Session* createUser(string username, string password) throws Unauthorized;
        void removeUser(Session* activeSession) throws SessionExpired, InvalidUser;
        bool verifySession(Session* session);
    };

    // communication between managers
    interface ManagerQueryResponse {
        void sendSession(Session* session);
        void userExists();
        void userRemoved();
        void sessionVerified();
    };

    interface ManagerQuery {
        void login(string username, string password, ManagerQueryResponse* responseRcvr);
        void checkUsername(string username, ManagerQueryResponse* responseRcvr);
        void removeUserBySession(Session *activeSession, ManagerQueryResponse* responseRcvr);
        void checkSession(Session *session, ManagerQueryResponse* responseRcvr);
    };
}
