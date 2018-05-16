#!/bin/bash
while true
do
  #stress --cpu 16 --io 8 --vm 4 --vm-bytes 1024M &
  stress --cpu 64 --io 32 --vm 8 --vm-bytes 1024M  &
    stress --cpu 64 --io 32 --vm 8 --vm-bytes 1024M  &
done
