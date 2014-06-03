#!/usr/bin/env python

import automagic_imaging
import datetime
import os
import subprocess
import sys
import time

def main():
    set_globals()
    automagic_imaging.scripts.parse_options.parse(options)
    if os.geteuid() != 0:
        print("You must be root to execute this script!")
        sys.exit(1)
    setup_logger()

    logger.info("********************************************************************************")
    logger.info("STARTING IMAGING")

    # Eventually make it able to run one image at a time manually.
    # For now, always use a config file.
    if not options['config']:
        options['config'] = '/etc/radmind_auto_image_creator/config.ini'

    with_config()
    logger.info("FINISHED IMAGING")

def with_config():
    logger.info("Using config file '" + os.path.abspath(options['config']) + "'")
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

    issue_image = None

    for image in config.images:
        if issue_image:
            # If there was a problem previously, unmount the previous image.
            # This is here because you can't unmount a volume while inside it...
            logger.error("Image " + str(issue_image.name)) + " did not complete successfully.")
            failure_unmount(issue_image)
            issue_image = None
        # Start logging for this image.
        logger.info("--------------------------------------------------------------------------------")
        logger.info("Processing image '" + str(image) + "'")
        # Change directory to the temporary location.
        with ChDir(options['tmp_dir']):
            # Create the blank sparse image
            logger.info("Creating image named '" + str(image) + "'...")
            try:
                i = automagic_imaging.images.Image(make=True, name=image, volume=config.images[image]['volume'])
            except:
                logger.error(sys.exc_info()[1].message)
                continue
            logger.info("Created image '" + i.path + "'")

            # Mount sparse image to write to
            logger.info("Mounting image...")
            try:
                i.mount()
            except:
                logger.error(sys.exc_info()[1].message)
                continue
            logger.info("Mounted image at '" + i.mount_point + "'")

            # Enable ownership
            logger.info("Enabling ownership of volume...")
            try:
                i.enable_ownership()
            except:
                logger.error(sys.exc_info()[1].message)
                issue_image = i
                continue
            logger.info("Volume ownership enabled.")

            # Clean volume
            logger.info("Emptying volume of all contents...")
            try:
                i.clean()
            except:
                logger.error(sys.exc_info()[1].message)
                issue_image = i
                continue
            logger.info("Volume cleaned.")

            with ChDir(i.mount_point):
                # Radmind
                logger.info("Beginning radmind cycle...")

                # ktcheck
                logger.info("Running ktcheck...")
                try:
                    automagic_imaging.scripts.radmind.run_ktcheck(
                        cert=config.images[image]['cert'],
                        rserver=options['rserver'],
                        logfile='./private/var/log/radmind/imaging_ktcheck.log'
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    issue_image = i
                    continue
                logger.info("Completed ktcheck.")

                # fsdiff
                # fsdiff output goes to:
                fsdiff_out = './private/var/log/radmind/fsdiff_output.T'
                logger.info("Running fsdiff with output to '" + os.path.abspath(fsdiff_out) + "'...")
                try:
                    automagic_imaging.scripts.radmind.run_fsdiff(
                        outfile=fsdiff_out,
                        logfile='./private/var/log/radmind/imaging_fsdiff.log'
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    issue_image = i
                    continue
                logger.info("Completed fsdiff.")

                # lapply
                # Move fsdiff output for lapply (for redundancy)
                lapply_in = './private/var/log/radmind/lapply_input.T'
                subprocess.call(['cp', fsdiff_out, lapply_in])
                logger.info("Running lapply with input from '" + os.path.abspath(lapply_in) + "'...")
                try:
                    automagic_imaging.scripts.radmind.run_lapply(
                        cert=config.images[image]['cert'],
                        rserver=options['rserver'],
                        infile=lapply_in,
                        logfile='./private/var/log/radmind/imaging_lapply.log'
                    )
                except:
                    logger.error(sys.exc_info()[1].message)
                    issue_image = i
                    continue
                logger.info("Completed lapply.")

                # Xhooks post-maintenance
                logger.info("Beginning post-maintenance...")
                try:
                    automagic_imaging.scripts.radmind.run_post_maintenance()
                except:
                    logger.error(sys.exc_info()[1].message)
                    issue_image = i
                    continue
                logger.info("Completed post-maintenance.")

                # Get the system's OS version and build version for file naming.
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

            # Bless volume to make it mountable
            logger.info("Blessing volume...")
            bless_label = image + ' ' + version
            try:
                i.bless(bless_label)
            except:
                logger.error(sys.exc_info()[1].message)
                issue_image = i
                continue
            logger.info("Volume blessed.")

            # Unmount volume for conversion
            logger.info("Unmounting volume...")
            try:
                i.unmount()
            except:
                logger.error(sys.exc_info()[1].message)
                issue_image = i
                continue
            logger.info("Volume unmounted.")

            # Craft new file name in the form:
            # {out_dir}/YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD.dmg
            date = datetime.datetime.now().strftime('%Y.%m.%d')
            convert_name = options['out_dir'] + '/' + date + '_' + image.upper() + '_' + version + '_' + build + '.dmg'

            # Convert from .sparseimage to read-only .dmg
            logger.info("Converting image to read-only at '" + convert_name + "'")
            try:
                i.convert(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                continue
            logger.info("Image converted.")

            # Remove sparse image
            logger.info("Removing original sparse image...")
            try:
                os.remove('./' + image + '.sparseimage')
            except:
                logger.error(sys.exc_info()[1].message)
                continue
            logger.info("Image removed.")

            # Scan image for ASR use
            logger.info("Scanning image for asr use...")
            try:
                automagic_imaging.images.scan(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                continue
            logger.info("Image scanned.")

            # Done
            logger.info("Successfully finished " + str(image) + ".")

def failure_unmount(image):
    if image:
        if image.mounted:
            attempt = 3
            while (attempt > 0):
                time.sleep(2)
                try:
                    image.unmount(force=True)
                    logger.info("Successfully unmounted '" + str(image.name) + "'")
                    return
                except:
                    try:
                        time.sleep(2)
                        automagic_imaging.images.detach(image.mount_point, force=True)
                        time.sleep(2)
                        image.unmount(force=True)
                        logger.info("Successfully unmounted '" + str(image.name) + "'")
                        return
                    except:
                        logger.error("Could not unmount image '" + str(image.name) +
                                     "' on device " + image.disk_id + " during premature exit. " +
                                     str(attempt - 1) + " attempts remaining.")
                attempt -= 1
            logger.error("Failed to unmount image '" + str(image.name) +
                         "' during premature exit. Please unmount manually from " + image.disk_id + ".")

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
