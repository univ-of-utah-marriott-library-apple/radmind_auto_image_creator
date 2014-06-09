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
usage: {} [-hvni] [-l log] [-c config] [-t tmp_dir] [-o out_dir]
          [-r rserver] [-C cert] [-I image] [-V volume]

Create bootable disk images from Radmind.

    h : prints this help message
    v : prints the version information
    n : prevents logs from being written to file and enables console output
    i : provides an interactive method of getting imaging information; this will
        only create one image per run, and will override any other information
        you provide

    l log     : use 'log' as the logging output location
    c config  : use 'config' as the configuration file
    t tmp_dir : use 'tmp_dir' as the temporary directory for sparse images
    o out_dir : use 'out_dir' as the output directory for dmg images
    r rserver : use 'rserver' as the local radmind server
    C cert    : use 'cert' as the certificate (for Manual or Interactive modes)
    I image   : use 'image' as the name of the image to be created (for Manual
                or Interactive modes)
    V volume  : use 'volume' as the name of the bootable volume for the image
                (for Manual or Interactive modes)\
'''.format(options['name'])
    sys.exit(0)

def parse(options):
    '''Parses the options.
    '''

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help',
                        action='store_true')
    parser.add_argument('-v', '--version',
                        action='store_true')
    parser.add_argument('-n', '--no-log',
                        action='store_true')
    parser.add_argument('-i', '--interactive',
                        action='store_true')
    parser.add_argument('-l', '--log')
    parser.add_argument('-c', '--config')
    parser.add_argument('-t', '--tmp_dir')
    parser.add_argument('-o', '--out_dir')
    parser.add_argument('-r', '--rserver')
    parser.add_argument('-C', '--cert')
    parser.add_argument('-I', '--image-name')
    parser.add_argument('-V', '--volume-name')
    args = parser.parse_args()

    if args.help:
        usage(options)
    if args.version:
        version(options)
        sys.exit(0)
    options['log'] = not args.no_log
    options['log_dest'] = args.log
    options['config'] = args.config
    options['interactive'] = args.interactive
    options['tmp_dir'] = args.tmp_dir
    options['out_dir'] = args.out_dir
    options['rserver'] = args.rserver
    options['cert'] = args.cert
    options['image'] = args.image_name
    options['volname'] = args.volume_name
