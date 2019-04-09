#!/usr/bin/env python

import re
import os
import sys
import time
import signal
import socket
import requests
import argparse
import subprocess

# Logic:
# - parsing the arguments for configuration runtime options
# - start creating vpn connection object from class vpn_session()
# - check if config path is a valid path before starting openvpn, otherwise exit with status 1
# - if config file exists, try starting it 
# - as the return code of openvpn client is a bit messed up (no matter it can connect to remote or not, it return with status code 0). To get around this, I poll the stdout to do some sort of pattern matching to catch the connection status 
# - if connection fail, keep retries every 10 secs until number of tries reached. Exit and skip testing.
# - once the connection is up, move on to next step, create object from class connection_test()
# - try doing dns lookup
# - try fetching pages

# TODO: 
# - should be testing a list of sites, instead of 1 site
# - should be testing a list of dns , instead of 1 dns
# - logging should be done via native logger
# - didn't handle stderr of openvpn client properly at this point
# - because of improper handling on stderr, it can't catch duplicate run or others runtime failure
# - maybe some sort of client configuration syntax validation
# - move arg parsers to a wrapper class so things under __main__ can be tidy up a bit
# - reformat it to match with PEP8 standard


class vpn_session(object):

    # instantiate all the class variables. perform config path check upon init
    def __init__(self, args):
        self._config = args.pop('config')
        self._tries = args.pop('tries')
        self._interval = args.pop('interval')
        self._start_time = None
        self._end_time = None
        self._secs_taken = None
        self._proc = None
        self._success_pattern = '.*Initialization Sequence Completed.*'
        self._error_pattern = '.*Error.*'
        self._vpn_state = None
        self._connect_count = 0
        self.config_path_check()

    # check if the config path is a valid file
    # unfortunately no pattern check is available yet
    def config_path_check(self):
        if not os.path.isfile(self._config):
            sys.exit(1)

    # start setting up vpn connection
    def start(self):
        cmd = '/usr/sbin/openvpn --config %s' % (self._config)
        self._connect_count += 1
        self._start_time = time.time()
        print('%s INFO: Starting %s out of %s tries with profile %s ... ') % (self.time_now(), self._connect_count, self._tries, self._config)
        self._proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
        # monitor the connection states until success or failure
        while True:
            output = self._proc.stdout.readline()
            if output == '' and self._proc.poll() is not None:
                break
            elif output:
                if re.match(self._success_pattern, output):
                    print("%s INFO: %s" % (self.time_now(), output.strip()))
                    self._end_time = time.time()
                    self._secs_taken = self._end_time - self._start_time
                    self._vpn_state = True
                    print('%s INFO: VPN profile %s connected successfully in %s secs' % (self.time_now(), self._config, self._secs_taken))
                    break
                elif re.match(self._error_pattern, output):
                    print("%s ERROR: %s" % (self.time_now(), output.strip()))
                    self._end_time = time.time()
                    self._secs_taken = self._end_time - self._start_time
                    print('%s ERROR: VPN profile %s failed to connect in %s secs' % (self.time_now(), self._config, self._secs_taken))
                    self._vpn_state = False
                    self.stop()
                    break

    def time_now(self):
        return time.strftime('%X %x %Z')

    # a wrapper method to do restart
    def retry(self):
        self.start()

    def stop(self):
        # this is a bit tricky, as vpn process is launched with subprocess.Popen with option shell=true
        # we need to kill all the child process under the subprocess shell
        pgid = os.getpgid(self._proc.pid)
        os.killpg(pgid, signal.SIGTERM)

    # main logic of vpn connections go here
    # so it will check if the vpn connection is up.
    # If not it will retries till it match the maximum number of retries
    def main(self):
        self.start()
        while not self._vpn_state:
            if self._connect_count < self._tries :
                time.sleep(self._interval)
                self.retry()
            else:
                print('%s All vpn connection attempts failed' % (self.time_now()))
                sys.exit(1)
        if self._vpn_state:
            pass
        

class connection_test(object):

    def __init__(self, args):
        self._url = args.pop('url')
        self._dns = args.pop('dns')
        self._start_time = None
        self._end_time = None
        self._test_duration = None

    def time_now(self):
        return time.strftime('%X %x %Z')

    # resolve dns
    def dns_test(self):
        self._start_time = time.time()
        try:
            socket.setdefaulttimeout(60)
            socket.gethostbyname(self._dns)
            self._end_time = time.time()
            self._test_duration = self._end_time - self._start_time
            print '%s INFO: DNS %s resolved successfully in %s secs' % (self.time_now(), self._dns, self._test_duration)
        except:
            self._end_time = time.time()
            self._test_duration = self._end_time - self._start_time
            print '%s ERROR: DNS %s failed to resolve in %s secs' % (self.time_now(), self._dns, self._test_duration)

    # poll the target url 
    def url_test(self):
        try:
            r = requests.get(self._url, timeout=60)
            self._end_time = time.time()
            self._test_duration = self._end_time - self._start_time
            print '%s INFO: Successfully fetched %s in %s secs. Return code %s Data size %s bytes' % (self.time_now(), self._url, self._test_duration, r.status_code, r.headers['content-length'])
        except requests.exceptions.RequestException as e:
            self._end_time = time.time()
            self._test_duration = self._end_time - self._start_time
            print '%s ERROR: Failed to fetch %s in %s secs' % (self.time_now(), self._url, self._test_duration)
            print '%s ERROR: %s' % (self.time_now(), e)

    def main(self):
        self.dns_test()
        self.url_test()
        

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, action='store', default='/etc/openvpn/client.ovpn', help='Openvpn client config, default: /etc/openvpn/client.ovpn')
    parser.add_argument('-u', '--url', type=str, action='store', default='http://www.google.com', help='URL to test, default: www.google.com')
    parser.add_argument('-d', '--dns', type=str, action='store', default='www.google.com', help='DNS name to test, default: www.google.com')
    parser.add_argument('-i', '--interval', type=int, action='store', default=10, help='Retry interval upon connection failure, default: 10 secs')
    parser.add_argument('-t', '--tries', type=int, action='store', default=3, help='Number of total tries upon connection failure, default: 3 times')
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # parse the arguments
    args = parser.parse_args()

    # taking a timestamp upon start of everythin
    test_start_time = time.time()

    # instantiate the vpn instance
    vpn = vpn_session(vars(args))

    # start setting up vpn, exit(1) if it failed to connect even after retries
    vpn.main()

    # if vpn is up, test start
    test = connection_test(vars(args))
    test.main()

    # tearing down vpn session
    vpn.stop()

    # get timestamp for overall test duration
    test_end_time = time.time()
    test_duration = test_end_time - test_start_time
    print('%s INFO: Test completed in %s secs' % (time.strftime('%X %x %Z'), test_duration))

