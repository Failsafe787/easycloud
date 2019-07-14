#!/bin/bash

# author: Davide Monfrecola, Stefano Garione, Giorgio Gambino, Luca Banzato
# copyright: Copyright (C) 2019"
# credits: Andrea Lombardo, Irene Lovotti
# license: GPL v3
# version: 0.10.0
# maintainer: Luca Banzato
# email: 20005492@studenti.uniupo.it
# status: Prototype


PYTHON3="python3"
PIP3="pip3"
SCRIPT="easycloud_launcher.py"

run() {
    $PYTHON3 $SCRIPT $1
}

run_debug() {
    LIBCLOUD_DEBUG=logs/libcloud_debug.log LIBCLOUD_DEBUG_PRETTY_PRINT_RESPONSE=1 $PYTHON3 $SCRIPT
}

check_app() {
    if ! [ -x "$(command -v $1)" ]; then
        return 1
    fi
    return 0
}


if ! check_app "$PYTHON3"; then
    echo "python3 is not installed or missing from PATH environment variable"
elif ! check_app "$PIP3"; then
    echo "pip3 is not installed or missing from PATH environment variable"
elif [ ! -f $SCRIPT ]; then
    echo "The main program script is missing ($SCRIPT)"
else
    if [ "$#" = "1" ] && [ "$1" = "--debug" ]; then
        run_debug
    else
        run "$@"
    fi
fi
