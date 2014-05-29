#!/usr/bin/env python

import automagic_imaging
import datetime
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

    logger.info("Using config file '" + options['config'] + "'")
    config = automagic_imaging.configurator.Configurator(options['config'])

    options['tmp_dir'] = config.globals['tmp_dir']
    options['out_dir'] = config.globals['out_dir']

    for image in config.images:
        # Change directory to the temporary location.
        with ChDir(options['tmp_dir']):
            # Create the blank sparse image.
            logger.info("Creating image '" + str(image) + "'...")
            try:
                i = automagic_imaging.images.Image(make=True, name=image, volume=config.images[image]['volume'])
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(10)
            logger.info("Created successfully at '" + i.path + "'")

            # Mount sparse image.
            try:
                i.mount()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(11)
            logger.info("Mounted image at '" + i.mount_point + "'")

            with ChDir(i.mount_point):
                pass
                # Radmind

                # Bless

            # Unmount
            try:
                i.unmount()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(12)
            logger.info("Image unmounted.")

            # Craft new file name in the form:
            # YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD
            date = datetime.datetime.now().strftime('%Y.%m.%d')
            version = '10.9.2' # Hardcoding for testing; temporary
            build = '13C64'    # Hardcoding for testing; temporary
            convert_name = date + '_' + image.upper() + '_' + version + '_' + build

            # Convert
            try:
                i.convert(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(13)
            logger.info("Converted to read-only at '" + "'")

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
