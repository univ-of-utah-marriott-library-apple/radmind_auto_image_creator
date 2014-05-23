import os
import re
import subprocess

class Image:
    '''Helps to deal with images more easily. Can mount, unmount, and get all
    relevant information.
    '''

    def __init__(self, path):
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

    def unmount(self):
        self.detach()

    def attach(self):
        if not self.mounted:
            self.disk_id = attach(self.path)
            self.mount_point = find_mount(self.disk_id)
            self.mounted = True

    def detach(self):
        if self.mounted:
            detach(self.disk_id)
            self.__revert()

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

    subprocess.call(['hdiutil', 'create', '-size', str(size), '-type', 'SPARSE',
                    '-ov', '-fs', 'HFS+', '-volname', str(vol), str(image)])

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
            raise RuntimeError("The disk did not mount properly.")
        else:
            return disk
        # # Mount the image, and retain the outputted information.
        # hdiutil = subprocess.check_output(['hdiutil', 'attach', '-plist', str(image)])
        #
        # # Get the mount point from the output:
        # mount = re.findall('mount-point.*\n[^>]*>([^<]*)<', hdiutil, re.MULTILINE)[0]
        # return mount
    else:
        raise ValueError("Invalid image file specified.")

def detach(disk):
    '''Unmounts the image.

    disk - the disk identifier to be unmounted; must be /dev/diskN format
    '''

    if re.match('/dev/', str(disk)):
        result = subprocess.call(['hdiutil', 'detach', str(disk)],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Disk did not unmount successfully.")
    elif re.match('/Volumes/', str(disk)):
        result = subprocess.call(['diskutil', 'unmountDisk', str(disk)],
                                 stderr=subprocess.STDOUT,
                                 stdout=open(os.devnull, 'w'))
        if result != 0:
            raise RuntimeError("Disk did not unmount successfully.")
    else:
        raise ValueError("Invalid disk specified.")

def find_mount(disk):
    '''Takes in a disk identifier in /dev/diskN format and finds its mountpoint.

    disk - the disk identifier
    '''

    if not re.match('/dev/', str(disk)):
        raise ValueError("Invalid disk specified; must be in /dev/diskN format.")
    else:
        mount = subprocess.check_output(['mount']).split('\n')
        result = ''
        for line in mount:
            if re.match(disk, line):
                result = re.search('on ([^(]*)', line).group()[3:-1]
        if not result:
            raise RuntimeError("The mount point could not be found for " + disk)
        else:
            return result