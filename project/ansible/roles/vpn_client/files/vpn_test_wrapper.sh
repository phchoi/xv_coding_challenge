#!/bin/bash

LOCKFILE=/tmp/vpn_test.lock
LOG=/var/log/vpn_test_result.log
# check if duplicate run
if [ -e ${LOCKFILE} ] && kill -0 `cat ${LOCKFILE}`; then
    echo "duplicate run detected"
    exit
fi

# catch all the exit signal
trap "rm -f ${LOCKFILE}; exit" EXIT
echo $$ > ${LOCKFILE}

# loop the test
while true; do
    for i in $(ls /etc/openvpn/*ovpn); do
         python /root/vpn_test.py --config ${i} >> ${LOG}
         sleep 10
    done
done

rm -f ${LOCKFILE}
