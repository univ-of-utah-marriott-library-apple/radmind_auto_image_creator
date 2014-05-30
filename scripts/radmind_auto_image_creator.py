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

    # Eventually make it able to run one image at a time manually.
    # For now, always use a config file.
    if not options['config']:
        options['config'] = '/etc/radmind_auto_image_creator/config.ini'

    with_config()

def with_config():
    logger.info("Using config file '" + options['config'] + "'")
    config = automagic_imaging.configurator.Configurator(options['config'])

    if not options['tmp_dir']:
        options['tmp_dir'] = config.globals['tmp_dir']
    if not options['out_dir']:
        options['out_dir'] = config.globals['out_dir']
    if not options['rserver']:
        options['rserver'] = config.globals['rserver']

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

            # Enable ownership
            try:
                i.enable_ownership()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(12)
            logger.info("Image ownership enabled.")

            # Clean volume
            try:
                i.clean()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(13)
            logger.info("Volume cleaned successfully.")

            with ChDir(i.mount_point):
                # Radmind
                try:
                    automagic_imaging.scripts.radmind.full(
                        cert=config.images[image]['cert'],
                        rserver=options['rserver']
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    sys.exit(20)

                # Get the system's OS version and build version.
                # (This is the file used by `/usr/bin/sw_vers`)
                vers = [
                    'defaults',
                    'read',
                    os.path.abspath('./System/Library/CoreServices/SystemVersion'),
                    'ProductVersion'
                ]
                build = [
                    'defaults',
                    'read',
                    os.path.abspath('./System/Library/CoreServices/SystemVersion'),
                    'ProductBuildVersion'
                ]
                version = subprocess.check_output(vers).strip('\n')
                build = subprocess.check_output(build).strip('\n')

            # Bless
            bless_label = image + ' ' + version
            try:
                i.bless(bless_label)
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(14)
            logger.info("Volume blessed successfully.")

            # Unmount
            try:
                i.unmount()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(15)
            logger.info("Image unmounted.")

            # Craft new file name in the form:
            # YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD
            date = datetime.datetime.now().strftime('%Y.%m.%d')
            convert_name = date + '_' + image.upper() + '_' + version + '_' + build

            # Convert
            try:
                i.convert(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(16)
            logger.info("Converted to read-only at '" + "'")

            # Remove sparse image.
            os.remove('./' + image + '.sparseimage')

            # Scan
            try:
                i.scan()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(17)
            logger.info("Image successfully scanned.")

def set_globals():
    global options
    options = {}
    options['long_name'] = "Radmind Auto Image Creator"
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = automagic_imaging.__version__

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
