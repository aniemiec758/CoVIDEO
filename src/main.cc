/**
 * This file parses the command line arguments and correctly
 * starts your server. You should not need to edit this file
 */

#include <unistd.h>
#include <sys/resource.h>

#include <csignal>
#include <cstdio>
#include <iostream>
#include <thread>

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
    Server server(*acceptor);
    server.new_users();
    delete acceptor;
}
