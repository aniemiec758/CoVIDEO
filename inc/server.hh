#ifndef  INCLUDE_SERVER_HH_
#define INCLUDE_SERVER_HH_

#include <mutex>
#include <vector>
#include <memory>

#include "socket.hh"

class Server {
 private:
    SocketAcceptor const& _acceptor;
    std::mutex _socks_mutex;
    std::string pause_auto;

 public:
    explicit Server(SocketAcceptor const& acceptor);
    ~Server();
    void new_users();
    void command_listener(Socket_t& sock);

    std::vector<Socket_t> _socks;
};

#endif  // INCLUDE_SERVER_HH_
