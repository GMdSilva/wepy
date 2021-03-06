#!/bin/bash

trap teardown SIGINT

teardown () {
    echo "caught signal tearing processes down"

    kill "$node_exporter_pid"
    echo "Killed node_exporter proc"

    kill "$nvidia_exporter_pid"
    echo "Killed nvidia_exporter proc"

    exit 1
}

# run the node exporters

./_bin/node_exporter &
node_exporter_pid="$!"
echo "Started the node_exporter as PID: $node_exporter_pid"

./_bin/nvidia_gpu_prometheus_exporter &
nvidia_exporter_pid="$!"
echo "Started the nvidia_gpu_prometheus_exporter as PID: $nvidia_exporter_pid"

# then run the job
echo "Running main process"
python source/we_pympler.py 10000 10000 10 || teardown

teardown
