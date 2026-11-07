# c_kernel/Makefile (Windows/MinGW Version)
CC      ?= gcc
CFLAGS  ?= -O2 -Wall -Wextra -std=c99 -fPIC
LIBS    := -lm

# Force .dll extension for Windows
LIB     := libthermo.dll
LDFLAGS := -shared

OBJ := thermo.o
HDR := thermo.h

.PHONY: all lib test clean

all: lib test

lib: $(LIB)

$(LIB): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)

$(OBJ): thermo.c $(HDR)
	$(CC) $(CFLAGS) -c -o $@ $<

test: test_thermo.exe
	./test_thermo.exe

test_thermo.exe: test_thermo.c thermo.c $(HDR)
	$(CC) $(CFLAGS) -o $@ test_thermo.c thermo.c $(LIBS)

clean:
	del /Q *.o *.dll test_thermo.exe 2>NUL