#!/usr/bin/env python

import automagic_imaging
import datetime
import os
import subprocess
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

    if not os.path.exists(options['tmp_dir']):
        options['tmp_dir'] = '/tmp'
    if not os.path.exists(options['out_dir']):
        options['out_dir'] = '/tmp'

    options['tmp_dir'] = os.path.abspath(options['tmp_dir'])
    options['out_dir'] = os.path.abspath(options['out_dir'])

    if options['tmp_dir'].endswith('/'):
        options['tmp_dir'] = options['tmp_dir'][:-1]
    if options['out_dir'].endswith('/'):
        options['out_dir'] = options['out_dir'][:-1]

    for image in config.images:
        logger.info("Processing image '" + str(image) + "'")
        # Change directory to the temporary location.
        with ChDir(options['tmp_dir']):
            # Create the blank sparse image.
            logger.info("Creating image named '" + str(image) + "'...")
            try:
                i = automagic_imaging.images.Image(make=True, name=image, volume=config.images[image]['volume'])
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(10)
            logger.info("Created image '" + i.path + "'")

            # Mount sparse image.
            logger.info("Mounting image...")
            try:
                i.mount()
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(11)
            logger.info("Mounted image at '" + i.mount_point + "'")

            # Enable ownership
            logger.info("Enabling ownership of volume...")
            try:
                i.enable_ownership()
            except:
                logger.error(sys.exc_info()[1].message)
                exit(12, i)
            logger.info("Volume ownership enabled.")

            # Clean volume
            logger.info("Emptying volume of all contents...")
            try:
                i.clean()
            except:
                logger.error(sys.exc_info()[1].message)
                exit(13, i)
            logger.info("Volume cleaned.")

            with ChDir(i.mount_point):
                # Radmind
                logger.info("Beginning radmind cycle...")
                # ktcheck
                logger.info("Running ktcheck...")
                try:
                    automagic_imaging.scripts.radmind.run_ktcheck(
                        cert=config.images[image]['cert'],
                        rserver=options['rserver']
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    exit(20, i)
                logger.info("Completed ktcheck.")
                # fsdiff
                fsdiff_out = options['tmp_dir'] + '/' + str(image) + '.T'
                logger.info("Running fsdiff with output to '" + fsdiff_out + "'...")
                try:
                    automagic_imaging.scripts.radmind.run_fsdiff(
                        outfile=fsdiff_out
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    exit(21, i)
                logger.info("Completed fsdiff.")
                # lapply
                logger.info("Running lapply with input from '" + fsdiff_out + "'...")
                try:
                    automagic_imaging.scripts.radmind.run_lapply(
                        cert=config.images[image]['cert'],
                        rserver=options['rserver'],
                        infile=fsdiff_out
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    exit(22, i)
                logger.info("Completed lapply.")
                # post-maintenance
                logger.info("Beginning post-maintenance...")
                try:
                    automagic_imaging.scripts.radmind.run_post_maintenance()
                except:
                    logger.error(sys.exc_info()[1].message)
                    exit(23, i)
                logger.info("Completed post-maintenance.")

                # Get the system's OS version and build version.
                # (This is the file used by `/usr/bin/sw_vers`)
                version_command = [
                    'defaults',
                    'read',
                    os.path.abspath('./System/Library/CoreServices/SystemVersion'),
                    'ProductVersion'
                ]
                build_command = [
                    'defaults',
                    'read',
                    os.path.abspath('./System/Library/CoreServices/SystemVersion'),
                    'ProductBuildVersion'
                ]
                version = subprocess.check_output(version_command).strip('\n')
                logger.info("Using system version: " + version)
                build = subprocess.check_output(build_command).strip('\n')
                logger.info("Using system build version: " + build)

            # Bless
            logger.info("Blessing volume...")
            bless_label = image + ' ' + version
            try:
                i.bless(bless_label)
            except:
                logger.error(sys.exc_info()[1].message)
                exit(14, i)
            logger.info("Volume blessed.")

            # Unmount
            logger.info("Unmounting volume...")
            try:
                i.unmount()
            except:
                logger.error(sys.exc_info()[1].message)
                exit(15, i)
            logger.info("Volume unmounted.")

            # Craft new file name in the form:
            # YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD
            date = datetime.datetime.now().strftime('%Y.%m.%d')
            convert_name = options['out_dir'] + '/' + date + '_' + image.upper() + '_' + version + '_' + build + '.dmg'

            # Convert
            logger.info("Converting image to read-only at '" + convert_name + "'")
            try:
                i.convert(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(16)
            logger.info("Image converted.")

            # Remove sparse image.
            logger.info("Removing original sparse image...")
            try:
                os.remove('./' + image + '.sparseimage')
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(17)
            logger.info("Image removed.")

            # Scan
            logger.info("Scanning image for asr use...")
            try:
                automagic_imaging.images.scan(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                sys.exit(18)
            logger.info("Image scanned.")

def exit(code, image=None):
    if image:
        if image.mounted:
            try:
                image.unmount()
            except:
                logger.critical("Could not unmount image '" + str(image) + "' during premature exit.")
    sys.exit(code)

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
