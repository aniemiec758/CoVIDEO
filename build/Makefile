TOP_DIR=..
SRC_DIR=$(TOP_DIR)/src
INC_DIR=$(TOP_DIR)/inc
BUILD_DIR=.
OBJ_DIR=$(BUILD_DIR)/obj

CC=g++
CFLAGS= -I ${INC_DIR} -g -Wall -Wextra -pedantic -c
LDFLAGS= -pthread

# Source definitions
SRC=$(wildcard $(SRC_DIR)/*.cc)

# Object definitions
OBJ=$(patsubst $(SRC_DIR)/%.cc,$(OBJ_DIR)/%.o,$(SRC))

TARGET=cvdoserver

# Require build directories and targets
all: dirs $(TARGET)

# Make directories
dirs: $(OBJ_DIR)

$(OBJ_DIR):
	mkdir -p $@

# Link each target from correct obj files
$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) $^ -o $@

# Compile all CVDO objects
$(OBJ): $(OBJ_DIR)/%.o : $(SRC_DIR)/%.cc
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f -r $(OBJ_DIR)
	rm -f $(TARGET)
