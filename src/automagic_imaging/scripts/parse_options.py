import argparse
import sys

def version(options):
    '''Prints the version information.
    '''

    print "{name}, version {version}\n".format(name=options['long_name'],
                                               version=options['version'])

def usage(options):
    '''Gives useful usage information.
    '''

    version(options)

    print '''\
usage: {} [-hvn] [-l log]

Create bootable disk images from Radmind.

    h : prints this help message
    v : prints the version information
    n : prevents logs from being written to file and enables console output

    l log : use 'log' as the logging output location\
'''.format(options['name'])
    sys.exit(0)

def parse(options):
    '''Parses the options given to ls_manager.py.
    '''

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help',
                        action='store_true')
    parser.add_argument('-v', '--version',
                        action='store_true')
    parser.add_argument('-n', '--no-log',
                        action='store_true')
    parser.add_argument('-l', '--log')

    if args.help:
        usage(options)
    if args.version:
        version(options)
        sys.exit(0)
    options['log'] = not args.no_log
    options['log_dest'] = args.log
    if not args.action:
        print "Error: You must specify an action!"
        sys.exit(5)
