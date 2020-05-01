#ifndef  INCLUDE_CLIENT_HH_
#define INCLUDE_CLIENT_HH_

#include "socket.hh"

class Client {
 private:
    SocketAcceptor const& _acceptor;

 public:
    explicit Client(SocketAcceptor const& acceptor);
    void run_thread() const;
    void handle(const Socket_t& sock) const;
};

#endif  // INCLUDE_CLIENT_HH_
