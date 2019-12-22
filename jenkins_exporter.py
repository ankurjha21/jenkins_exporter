#!/usr/bin/python

import re
import time
import requests
import argparse
from pprint import pprint

import os
from sys import exit

import http.server
import socketserver


DEBUG = int(os.environ.get('DEBUG', '0'))

class JenkinsMetrics(object):
    def __init__(self, target, host, user, password, insecure):
        self._target = target.rstrip("/")
        self._host = host
        self._user = user
        self._password = password
        self._insecure = insecure

    def collect(self):
        # Request exactly the information we need from Jenkins
        url = '{0}/prometheus/'.format(self._target)

        if self._user and self._password:
            response = requests.get(url, auth=(self._user, self._password), headers={'host': self._host}, verify=(not self._insecure))
        else:
            response = requests.get(url, headers={'host': self._host}, verify=(not self._insecure))

        if DEBUG:
            print(response.text)

        if response.status_code != requests.codes.ok:
            raise Exception("Call to url %s failed with status: %s" % (url, response.status_code))

        return response.text


def parse_args():
    parser = argparse.ArgumentParser(
        description='jenkins exporter args jenkins address and port'
    )
    parser.add_argument(
        '-j', '--jenkins',
        metavar='jenkins',
        required=False,
        help='server url from the jenkins api',
        default=os.environ.get('JENKINS_SERVER', 'http://jenkins:8080')
    )
    parser.add_argument(
        '--host',
        metavar='host',
        required=True,
        help='server host header',
        default='None'
    )
    parser.add_argument(
        '--user',
        metavar='user',
        required=False,
        help='jenkins api user',
        default=os.environ.get('JENKINS_USER')
    )
    parser.add_argument(
        '--password',
        metavar='password',
        required=False,
        help='jenkins api password',
        default=os.environ.get('JENKINS_PASSWORD')
    )
    parser.add_argument(
        '-p', '--port',
        metavar='port',
        required=False,
        type=int,
        help='Listen to this port',
        default=int(os.environ.get('VIRTUAL_PORT', '9118'))
    )
    parser.add_argument(
        '-k', '--insecure',
        dest='insecure',
        required=False,
        action='store_true',
        help='Allow connection to insecure Jenkins API',
        default=False
    )
    return parser.parse_args()


def main():
    class MetricRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            jenkinsMetrics = JenkinsMetrics(args.jenkins, args.host, args.user, args.password, args.insecure)

            self.send_response(200)
            self.end_headers()

            self.wfile.write(bytes(jenkinsMetrics.collect(), "ascii"))
            
            return

    try:
        args = parse_args()
        port = int(args.port)

        with socketserver.TCPServer(("", args.port), MetricRequestHandler) as httpd:
            print("serving at port", args.port)
            httpd.serve_forever()

        server.serve_forever()
    except KeyboardInterrupt:
        print(" Interrupted")
        exit(0)


if __name__ == "__main__":
    main()
