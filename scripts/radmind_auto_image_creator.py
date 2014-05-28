#!/usr/bin/env python

import sys

import automagic_imaging.scripts

def set_globals():
    global options
    options = {}
    options['long_name'] = "Radmind Auto Image Creator"
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = '0.2'

def setup_logger():
    global logger
    logger = automagic_imaging.scripts.logger.logger(options['log'],
                                                     options['log_dest'],
                                                     options['name'])

def main():
    set_globals()
    automagic_imaging.scripts.parse_options.parse()
    setup_logger()

if __name__ == "__main__":
    main()
