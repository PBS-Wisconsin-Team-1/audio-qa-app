#!/bin/bash
# Bash script to stop Redis server and rq-dashboard
pkill redis-server
pkill -f rq-dashboard
