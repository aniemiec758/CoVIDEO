/**
 * This file contains the primary logic for your server. It is responsible for
 * handling socket communication - parsing HTTP requests and sending HTTP responses
 * to the client. 
 */

#include <functional>
#include <iostream>
#include <sstream>
#include <vector>
#include <thread>

#include "server.hh"
#include "errors.hh"

Server::Server(SocketAcceptor const& acceptor) : _acceptor(acceptor) {
    pause_auto = "ON";
}

Server::~Server() {}

struct server_meta {
    Server * serverptr;
    Socket_t * socket;
};

void listener_dispatch(server_meta * sm) {
    sm->serverptr->command_listener(*(sm->socket));
    delete sm;
}

void Server::new_users() {
  while (1) {
    Socket_t sock = _acceptor.accept_connection();
    _socks_mutex.lock();
    server_meta * sm = new server_meta;
    sm->serverptr = this;
    _socks.push_back(std::move(sock));
    sm->socket = &(_socks.back());
    std::thread t = std::thread(listener_dispatch, sm);
    t.detach();
    _socks_mutex.unlock();
    
  }
}

void Server::command_listener(Socket_t& sock) {
  std::string line;
  while(!(line = sock->readline()).empty())
  {
    std::cout << line;
    if (line == "get-pause-auto\r\n")
    {
      sock->write(pause_auto);
      continue;
    }
    for (int i = 0; i < _socks.size(); i++)
    {
       if (_socks[i] == sock) continue;
       if (line == "toggle-auto ON\r\n") pause_auto = "ON";
       else if (line == "toggle-auto OFF\r\n") pause_auto = "OFF";
       _socks[i]->write(line);
    }
  }
  _socks_mutex.lock();
  for (int i = 0; i < _socks.size(); i++)
  {
    if (_socks[i] == sock)
    {
        _socks.erase(_socks.begin()+i);
        _socks_mutex.unlock();
        return;
    }
  }
  std::cout << "SOCK REMOVE ERROR!" << std::endl;
  _socks_mutex.unlock();
}

// matches the prefix and call the corresponding handler. You are free to implement
// the different routes however you please
/*
std::vector<Route_t> route_map = {
  std::make_pair("/cgi-bin", handle_cgi_bin),
  std::make_pair("/", handle_htdocs),
  std::make_pair("", handle_default)
};
*/
