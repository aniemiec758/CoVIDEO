/**
 * This file parses the command line arguments and correctly
 * starts your server. You should not need to edit this file
 */

#include <unistd.h>
#include <sys/resource.h>

#include <csignal>
#include <cstdio>
#include <iostream>

#include "server.hh"
#include "socket.hh"
#include "tcp.hh"

#define BOUND_PORTNO 25565

extern "C" void signal_handler(int signal) {
    exit(0);
}

int main(int argc, char** argv) {
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
    enum concurrency_mode mode = E_NO_CONCURRENCY;
    int port_no = BOUND_PORTNO;

    char usage[] = "USAGE: cvdoserver [PORT_NO]\n";

    if (argc > 2) {
        fputs(usage, stdout);
        return 0;
    }

    if (argc == 2) {
        port_no = atoi(argv[1]);
    }
    printf("port: %d\n", port_no);

    SocketAcceptor* acceptor = new TCPSocketAcceptor(port_no);
    Socket_t sock = _acceptor:
    Server server(*acceptor);
    server.run_thread();
    /*switch (mode) {
    case E_FORK_PER_REQUEST:
        server.run_fork();
        break;
    case E_THREAD_PER_REQUEST:
        server.run_thread();
        break;
    case E_THREAD_POOL:
        server.run_thread_pool(num_threads);
        break;
    default:
        server.run_linear();
        break;
    }*/
    delete acceptor;
}
