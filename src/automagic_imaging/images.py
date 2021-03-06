import os
import re
import subprocess

class Image:
    '''Helps to deal with images more easily. Can mount, unmount, and get all
    relevant information.
    '''

    def __init__(self, path='', make=False, name=None, volume=None):
        if make:
            if not name or not volume:
                raise ValueError("Must specify 'name' and 'volume' to create image.")
            path = create(image=name, vol=volume)
        if not os.path.isfile(path):
            raise ValueError("Invalid path specified: '" + path + "'")
        self.path = os.path.abspath(str(path))
        self.name = os.path.splitext(os.path.basename(self.path))[0]
        if not os.access(self.path, os.R_OK):
            raise ValueError("Image " + self.name + " is not readable.")
        self.__revert()

    def __repr__(self):
        result = "Image: " + self.name
        if self.mounted:
            result += "\n       Full path:   " + self.path
            result += "\n       Disk:        " + self.disk_id
            result += "\n       Mount point: " + self.mount_point
        else:
            result += "\n       Not mounted."
        return result

    def mount(self):
        self.attach()

    def attach(self):
        if not self.mounted:
            self.disk_id = attach(self.path)
            self.mount_point = find_mount(self.disk_id)
            self.mounted = True

    def unmount(self, force=False):
        self.detach(force)

    def detach(self, force=False):
        if self.mounted:
            detach(self.disk_id, force)
            self.__revert()

    def enable_ownership(self):
        if self.mounted:
            enable_ownership(self.disk_id)

    def clean(self):
        if self.mounted:
            clean(self.mount_point)

    def convert(self, format='', outfile=''):
        if not self.mounted:
            self.path = convert(self.path, format=format, outfile=outfile)

    def scan(self):
        if not self.mounted:
            scan(self.path)

    def bless(self, label=None):
        if self.mounted:
            bless(self.mount_point, label)

    def rename(self, new_name):
        if self.mounted:
            rename(self.mount_point, new_name)
            self.mount_point = find_mount(self.disk_id)
            self.name = new_name

    def __revert(self):
        self.mount_point = ''
        self.disk_id = ''
        self.mounted = False

def create(image, vol='Mac OS X', size='200g'):
    '''Creates a blank sparse image.

    image - the name of the image
    vol   - the name of the volume once mounted
    size  - the maximum size of the sparse image
    '''

    result = subprocess.check_output(['hdiutil', 'create', '-size', str(size),
                                      '-type', 'SPARSE', '-ov', '-fs', 'HFS+J',
                                      '-volname', str(vol), str(image)])

    if not result.startswith('created: '):
        raise RuntimeError("The image '" + str(image) + "' was not created properly.")

    return result.strip('\n').split(': ')[1]

def convert(image, format='', outfile=''):
    '''Converts an image to another format. Default is read-only.

    image   - path of the image to be converted
    format  - the desired format
    outfile - the name of the output file (defaults to the input file basename)
    '''

    if not outfile:
        outfile = os.path.splitext(os.path.abspath(image))[0]
    if not format:
        format = 'UDRO'

    formats = ['UDRW', 'UDRO', 'UDCO', 'UDZO', 'UDBZ', 'UFBI', 'UDTO', 'UDxx',
               'UDSP', 'UDSB', 'Rdxx', 'DC42',
               'UDZO-1', 'UDZO-2', 'UDZO-3', 'UDZO-4', 'UDZO-5', 'UDZO-6',
               'UDZO-7', 'UDZO-8', 'UDZO-9']
    if format not in formats:
        raise ValueError("Invalid format specified: '" + format + "'")

    result = subprocess.call(['hdiutil', 'convert', str(image), '-format',
                              str(format), '-o', str(outfile)],
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))

    if result != 0:
        raise RuntimeError("The image '" + str(image) + "' was not successfully converted.")

    return outfile

def attach(image):
    '''Mounts an image and returns the disk identifier in /dev/diskNsX format.

    image - the path of the image to be mounted
    '''

    if os.path.isfile(image):
        # Mount the image, and retain the outputted information.
        hdiutil = subprocess.check_output(['hdiutil', 'attach', str(image)])

        # Get the disk identifier from the output:
        disk = ''
        for line in hdiutil.split('\n'):
            columns = line.split('\t')
            if len(columns) == 3 and columns[2]:
                disk = columns[0].rstrip()
        if not disk:
            raise RuntimeError("The disk '" + str(image) + "' did not mount properly.")
        else:
            return disk
    else:
        raise ValueError("Invalid image file specified: + '" + str(image) + "'")

def detach(disk, force=False):
    '''Unmounts the image.

    disk - the disk identifier to be unmounted; must be /dev/diskN format
    '''

    if re.match('/dev/', str(disk)):
        detach = [
            'hdiutil',
            'detach',
            str(disk)
        ]
        if force:
            detach.append('-force')
        result = subprocess.call(detach,
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Disk did not unmount successfully.")
    elif re.match('/Volumes/', str(disk)):
        unmountDisk = [
            'diskutil',
            'unmountDisk'
        ]
        if force:
            unmountDisk.append('force')
        unmountDisk.append(str(disk))
        result = subprocess.call(unmountDisk,
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Disk did not unmount successfully.")
    else:
        raise ValueError("Invalid disk specified: '" + str(disk) + "'")

def find_mount(disk):
    '''Takes in a disk identifier in /dev/diskN format and finds its mountpoint.

    disk - the disk identifier
    '''

    if not re.match('/dev/', str(disk)):
        raise ValueError("Invalid disk given; must be in /dev/diskN format.")
    else:
        mount = subprocess.check_output(['mount']).split('\n')
        result = ''
        for line in mount:
            if re.match(disk, line):
                result = re.search('on ([^(]*)', line).group()[3:-1]
        if not result:
            raise RuntimeError("The mount point could not be found for " + str(disk))
        else:
            return result

def enable_ownership(disk):
    '''Enables ownership on the specified disk.

    disk - the disk identifier in /dev/diskN format
    '''

    if re.match('/dev/', str(disk)) or re.match('/Volumes/', str(disk)):
        result = subprocess.call(['diskutil', 'enableOwnership', str(disk)],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Ownership could not be enabled properly.")
    else:
        raise ValueError("Invalid disk given: '" + str(disk) + "'; must be in /dev/diskN format.")

def clean(volume):
    '''Removes all contents on the specified volume. Does not check for
    permissions.

    volume - the volume to be cleaned
    '''

    if not re.match('/Volumes/', str(volume)):
        raise ValueError("Invalid volume specified: '" + str(volume) + "'; must be mounted in /Volumes/")
    else:
        if not volume.endswith('/'):
            volume += '/'
        result = subprocess.call(['rm', '-rf', str(volume) + '*'],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Contents of the volume '" + str(volume) + "' could not be removed.")
        result = subprocess.call(['rm', '-rf', str(volume) + '.*'],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Contents of the volume '" + str(volume) + "' could not be removed.")

def bless(volume, label=None):
    '''Blesses a volume for bootability.

    volume - the volume to be blessed in /Volumes/
    label  - the name to give the volume during boot (optional)
    '''

    if not volume.endswith('/'):
        volume += '/'

    bless = [
        '/usr/sbin/bless',
        '--folder', str(volume) + 'System/Library/CoreServices',
        '--file', str(volume) + 'System/Library/CoreServices/boot.efi'
    ]
    if label:
        bless.append('--label')
        bless.append(str(label))

    result = subprocess.call(bless,
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("Volume '" + str(volume) + "' could not be blessed.")

def scan(image):
    '''Performs an imagescan on the image.

    image - image to be scanned
    '''

    if os.path.isfile(image):
        result = subprocess.call(['asr', 'imagescan', '--source', str(image)],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Image could not be scanned properly.")
    else:
        raise ValueError("Invalid image file specified: '" + str(image) + "'")

def rename(volume, new_name):
    '''Renames a mounted volume. May not take effect until the volume is
    unmounted and then remounted. Only works on writable volumes (of course).

    volume   - the volume to be renamed in /Volumes/
    new_name - the new name for the mounted volume
    '''

    if not re.match('/Volumes/', str(volume)):
        raise ValueError("Invalid volume specified: '" + str(volume) + "'; must be mounted in /Volumes/")
    else:
        if not volume.endswith('/'):
            volume += '/'
        result = subprocess.call(['diskutil', 'rename', str(volume), str(new_name)],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("The volume '" + str(volume) + "' could not be renamed.")
