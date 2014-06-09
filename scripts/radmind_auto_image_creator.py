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

    if options['interactive']:
        # Prompts the user for each item.
        interactive()
    elif options['config']:
        # Uses a config file for information.
        with_config()
    elif (options['tmp_dir'] and options['out_dir'] and options['rserver'] and
          options['cert'] and options['image'] and options['volname']):
        # Uses all of the manually-input information from the command line.
        produce_image()
    else:
        # The user probably did something wrong, but don't let all their work
        # go to waste!
        interactive()

    logger.info("--------------------------------------------------------------------------------")
    logger.info("FINISHED IMAGING")

def interactive():
    '''An interactive, prompting method of getting values from the user.'''
    # Set up default values for interactive mode.
    defaults = {}
    defaults['tmp_dir'] = '/tmp' if not options['tmp_dir'] else options['tmp_dir']
    defaults['out_dir'] = '/tmp' if not options['out_dir'] else options['out_dir']
    defaults['rserver'] = 'radmind.example.com' if not options['rserver'] else options['rserver']
    defaults['cert']    = None if not options['cert'] else options['cert']
    defaults['image']   = None if not options['image'] else options['image']
    defaults['volname'] = None if not options['volname'] else options['volname']
    # Now get the input from the user.
    logger.info("Using interactive imaging mode:")
    print("")
    print("INTERACTIVE MODE")
    print("----------------")

    options['tmp_dir'] = get_input(
                            prompt = "Temporary directory",
                            value  = defaults['tmp_dir'],
                            dir    = True
    )
    logger.info("  tmp_dir = '" + options['tmp_dir'] + "'")
    options['out_dir'] = get_input(
                            prompt = "Output directory",
                            value  = defaults['out_dir'],
                            dir    = True
    )
    logger.info("  out_dir = '" + options['out_dir'] + "'")
    options['rserver'] = get_input(
                            prompt = "Radmind server address",
                            value  = defaults['rserver']
    )
    logger.info("  rserver = '" + options['rserver'] + "'")
    options['cert'] = get_input(
                            prompt = "Path to certificate (.pem)",
                            value  = None if not defaults['cert'] else defaults['cert'],
                            file   = True
    )
    logger.info("  cert    = '" + options['cert'] + "'")
    options['image'] = get_input(
                            prompt = "Image name",
                            value  = None if not defaults['image'] else defaults['image']
    )
    logger.info("  image   = '" + options['image'] + "'")
    options['volname'] = get_input(
                            prompt = "Name of bootable volume",
                            value  = None if not defaults['image'] else defaults['image']
    )
    logger.info("  volname = '" + options['volname'] + "'")

    # Do the stuff here.
    produce_image()

def get_input(prompt, value=None, file=False, dir=False):
    '''Various ways to get input and test it. Retains original value if no
    new, valid value is given.
    '''
    if not value:
        value = ''
        # If there's no default, then the user must give a response.
        while True:
            # Loop forever! (i.e. until valid input is given)
            try:
                tmp = raw_input(prompt + " [" + value + "]: ")
            except KeyboardInterrupt:
                print("\nQuitting...\n\n")
                sys.exit(1)
            if tmp:
                if file:
                    # Must be a valid file.
                    if os.path.isfile(tmp):
                        # Return and exit.
                        return tmp
                    else:
                        print("No such file '" + tmp + "'.")
                elif dir:
                    # Must be a valid directory.
                    if os.path.isdir(tmp):
                        # Return and exit.
                        return tmp
                    else:
                        print("No such directory '" + tmp + "'.")
                else:
                    # Return and exit.
                    return tmp
            else:
                # User has to input something!
                print("Must provide valid input.")
    else:
        try:
            tmp = raw_input(prompt + " [" + value + "]: ")
        except KeyboardInterrupt:
            print("\nQuitting...\n\n")
            sys.exit(1)
        if tmp:
            if file:
                if os.path.isfile(tmp):
                    return tmp
                else:
                    print "Invalid file specified. Using default."
                    return value
            elif dir:
                if os.path.isdir(tmp):
                    return tmp
                else:
                    print "Invalid directory specified. Using default."
                    return value
            else:
                return tmp
        else:
            # If there's no input given, stick with the default value.
            return value

def with_config():
    '''The user specified a confi file. Get its values, but retain anything that
    the user may have given at command invocation (perhaps they wanted to
    override something in the file temporarily).
    '''
    logger.info("Using config file '" + os.path.abspath(options['config']) + "'")
    config = automagic_imaging.configurator.Configurator(options['config'])

    options['tmp_dir'] = config.globals['tmp_dir'] if not options['tmp_dir'] else options['tmp_dir']
    options['out_dir'] = config.globals['out_dir'] if not options['out_dir'] else options['out_dir']
    options['rserver'] = config.globals['rserver'] if not options['rserver'] else options['rserver']

    for image in config.images:
        options['cert']    = config.images[image]['cert']
        options['image']   = image
        options['volname'] = config.images[image]['volume']

        produce_image()

def produce_image():
    '''Makes a call to 'image_producer' using the values in 'options'. This
    saves time and typing, since all of the values are generally stored here
    anyway.
    '''
    if options['volname'].find('$VERSION') >= 0:
        options['attach_version'] = True
        options['original_volname'] = options['volname']
        options['volname'] = options['volname'].replace('$VERSION', '')
        options['volname'] = options['volname'].replace('  ', ' ')

    image_producer(
        tmp_dir        = options['tmp_dir'],
        out_dir        = options['out_dir'],
        rserver        = options['rserver'],
        cert           = options['cert'],
        image          = options['image'],
        volname        = options['volname'],
        attach_version = options['attach_version']
    )

def image_producer(tmp_dir, out_dir, rserver, cert, image, volname, attach_version=False):
    '''Creates an image and fills its filesystem from radmind.'''
    # All options must be non-empty.
    if not tmp_dir:
        raise ValueError("No temporary directory given.")
    if not out_dir:
        raise ValueError("No output directory given.")
    if not rserver:
        raise ValueError("No radmind server given.")
    if not cert:
        raise ValueError("No certificate given.")
    if not image:
        raise ValueError("No image name given.")
    if not volname:
        raise ValueError("No bootable volume name given.")

    # Check valid paths and files before beginning.
    if not os.path.isdir(tmp_dir):
        raise ValueError("Invalid temporary directory specified: '" + tmp_dir + "'")
    else:
        tmp_dir = os.path.abspath(tmp_dir)
    if not os.path.isdir(out_dir):
        raise ValueError("Invalid output directory specified: '" + out_dir + "'")
    else:
        out_dir = os.path.abspath(out_dir)
    if not os.path.isfile(cert):
        raise ValueError("Invalid certificate specified: '" + cert + "'")
    else:
        cert = os.path.abspath(cert)

    if tmp_dir.endswith('/'):
        tmp_dir = tmp_dir[:-1]
    if out_dir.endswith('/'):
        out_dir = out_dir[:-1]

    # Start logging for this image.
    logger.info("--------------------------------------------------------------------------------")
    logger.info("Processing image '" + image + "'")
    # Change directory to the temporary location.
    try:
        with ChDir(tmp_dir):
            # Create the blank sparse image
            logger.info("Creating image named '" + image + "'...")
            try:
                i = automagic_imaging.images.Image(make=True, name=image, volume=volname)
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker()
            logger.info("Created image '" + i.path + "'")

            # Mount sparse image to write to
            logger.info("Mounting image...")
            try:
                i.mount()
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker()
            logger.info("Mounted image at '" + i.mount_point + "'")

            # Enable ownership
            logger.info("Enabling ownership of volume...")
            try:
                i.enable_ownership()
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker(i)
            logger.info("Volume ownership enabled.")

            # Clean volume
            logger.info("Emptying volume of all contents...")
            try:
                i.clean()
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker(i)
            logger.info("Volume cleaned.")

            try:
                with ChDir(i.mount_point):
                    # Radmind
                    logger.info("Beginning radmind cycle...")

                    # ktcheck
                    logger.info("Running ktcheck...")
                    try:
                        automagic_imaging.scripts.radmind.run_ktcheck(
                            cert=cert,
                            rserver=rserver,
                            logfile='./private/var/log/radmind/imaging_ktcheck.log'
                        )
                    except:
                        logger.error(sys.exc_info()[1].message)
                        raise WithBreaker(i)
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
                        raise WithBreaker(i)
                    logger.info("Completed fsdiff.")

                    # Move fsdiff output for lapply (for redundancy)
                    lapply_in = './private/var/log/radmind/lapply_input.T'
                    try:
                        subprocess.call(['cp', fsdiff_out, lapply_in])
                    except:
                        logger.error("Could not copy '" + fsdiff_out + "' to '" + lapply_in + "'")
                        raise WithBreaker(i)

                    # lapply
                    logger.info("Running lapply with input from '" + os.path.abspath(lapply_in) + "'...")
                    try:
                        automagic_imaging.scripts.radmind.run_lapply(
                            cert=cert,
                            rserver=rserver,
                            infile=lapply_in,
                            logfile='./private/var/log/radmind/imaging_lapply.log'
                        )
                    except:
                        logger.error(sys.exc_info()[1].message)
                        raise WithBreaker(i)
                    logger.info("Completed lapply.")

                    # Xhooks post-maintenance
                    logger.info("Beginning post-maintenance...")
                    try:
                        automagic_imaging.scripts.radmind.run_post_maintenance()
                    except:
                        logger.error(sys.exc_info()[1].message)
                        raise WithBreaker(i)
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
            except WithBreaker as e:
                raise WithBreaker(e.image)

            # Declare the disk label for blessing here; could be modified
            bless_label = volume
            if options['attach_version']:
                # Rename the volume to include the system version.
                bless_label = options['original_volname'].replace('$VERSION', version)
                logger.info("Renaming volume to '" + bless_label + "'...")
                try:
                    i.rename(bless_label)
                except:
                    logger.error(sys.exc_info()[1].message)
                    raise WithBreaker(i)
                logger.info("Volume renamed.")

            # Bless volume to make it mountable
            logger.info("Blessing volume...")
            try:
                time.sleep(10)
                i.bless(bless_label)
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker(i)
            logger.info("Volume blessed.")

            # Unmount volume for conversion
            logger.info("Unmounting volume...")
            try:
                i.unmount()
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker(i)
            logger.info("Volume unmounted.")


            # Convert from .sparseimage to read-only .dmg
            logger.info("Converting image to read-only at '" + convert_name + "'")
            try:
                # Craft new file name in the form:
                # {out_dir}/YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD.dmg
                date = datetime.datetime.now().strftime('%Y.%m.%d')
                convert_name = out_dir + '/' + date + '_' + image.upper() + '_' + version + '_' + build + '.dmg'
                i.convert(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker()
            logger.info("Image converted.")

            # Remove sparse image
            logger.info("Removing original sparse image...")
            try:
                os.remove('./' + image + '.sparseimage')
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker()
            logger.info("Image removed.")

            # Scan image for ASR use
            logger.info("Scanning image for asr use...")
            try:
                automagic_imaging.images.scan(convert_name)
            except:
                logger.error(sys.exc_info()[1].message)
                raise WithBreaker()
            logger.info("Image scanned.")

            # Done
            logger.info("Successfully finished '" + image + "'.")
    except WithBreaker as e:
        # Outside of the with, need to check if there's still an issue.
        # If there was a problem previously, unmount the previous image.
        # This is here because you can't unmount a volume while inside it...
        logger.error("Image '" + image + "' did not complete successfully.")
        failure_unmount(e.image)

def failure_unmount(image):
    '''Attempt to unmount a volume/disk multiple times after a failure.'''
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
    '''Set globally-accessible options.'''
    global options
    options = {}
    options['long_name'] = "Radmind Auto Image Creator"
    options['name'] = '_'.join(options['long_name'].lower().split())
    options['version'] = automagic_imaging.__version__

    # Initialize null keys
    options['tmp_dir']          = None
    options['out_dir']          = None
    options['rserver']          = None
    options['cert']             = None
    options['image']            = None
    options['volname']          = None
    options['attach_version']   = False
    options['original_volname'] = None


def setup_logger():
    '''Sets up the logger to be used throughout.'''
    global logger
    logger = automagic_imaging.scripts.logger.logger(options['log'],
                                                     options['log_dest'],
                                                     options['name'])

class ChDir:
    '''Changes directories to the new path and retains the old directory.

    Use this in a 'with' statement for the best effect:

    # If we start in oldPath:
    os.getcwd()
    # returns oldPath
    with ChDir(newPath):
        os.getcwd()
        # returns newPath
    os.getcwd()
    # returns oldPath
    '''

    def __init__(self, newPath):
        self.savedPath = os.getcwd()
        os.chdir(newPath)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.savedPath)

class WithBreaker(Exception):
    '''Used to break out of 'with' statements.'''

    def __init__(self, image=None):
        self.image = image
    def __str__(self):
        return "Needed to break out of a 'with' statement!"

if __name__ == "__main__":
    main()
