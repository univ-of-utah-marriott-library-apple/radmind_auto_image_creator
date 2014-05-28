#!/usr/bin/env python

import automagic_imaging
import os
import sys

def main():
    set_globals()
    automagic_imaging.scripts.parse_options.parse(options)
    if os.geteuid() != 0:
        print("You must be root to execute this script!")
        sys.exit(1)
    setup_logger()

    if not options['config']:
        options['config'] = '/etc/radmind_auto_image_creator/config.ini'

    config = automagic_imaging.configurator.Configurator(options['config'])

    options['tmp_dir'] = config.globals['tmp_dir']
    options['out_dir'] = config.globals['out_dir']

    for image in config.images:
        # Change directory to the temporary location.
        with ChDir(options['tmp_dir']):
            # Create the blank sparse image.
            i = automagic_imaging.images.Image(create=True, name=image, volume=config.images[image]['volume'])

            # Mount sparse image.
            i.mount()

            with ChDir(i.mount_point):
                # Radmind

                # Bless

            # Unmount
            i.unmount()

            # Convert
            i.convert()

            # Remove sparse image.
            os.remove('./' + image + '.sparseimage')

            # Scan

def set_globals():
    global options
    options = {}
    options['long_name'] = "Radmind Auto Image Creator"
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = '0.2.2'

def setup_logger():
    global logger
    logger = automagic_imaging.scripts.logger.logger(options['log'],
                                                     options['log_dest'],
                                                     options['name'])

class ChDir:
    def __init__(self, newPath):
        self.savedPath = os.getcwd()
        os.chdir(newPath)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.savedPath)

if __name__ == "__main__":
    main()
