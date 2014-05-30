import collections
import ConfigParser
import datetime

class Configurator:
    '''Parses the config file for imaging information.
    '''

    def __init__(self, path):
        parser = ConfigParser.SafeConfigParser()
        parser.read(path)

        if not len(parser.sections()) >= 2:
            raise ValueError("Invalid config file: must have at least a 'Global' section and one Image section.")

        if not parser.has_section('Global'):
            raise ValueError("Invalid config file: must have a 'Global' section.")

        self.globals = {}
        required_globals = [
            'tmp_dir',    # Where the .sparseimage files are stored temporarily.
            'out_dir',    # Where to output the .dmg files.
            'rserver'     # The local radmind server.
        ]
        for required in required_globals:
            if not parser.has_option'Global', required):
                raise ValueError("Invalid config file: 'Global' section must have 'tmp_dir' and 'out_dir' options.")
        for option in parser.options('Global'):
            self.globals[option] = parser.get('Global', option)

        self.images = collections.OrderedDict()
        for images in parser.sections():
            if images == 'Global':
                continue
            image_options = {}
            for option in parser.options(images):
                image_options[option] = parser.get(images, option)
            self.images[images] = image_options

    def __repr__(self):
        result = ''
        result += self.print_globals()
        result += '\n'
        result += self.print_images()
        return result

    def print_globals(self):
        result = 'Globals:\n'
        for setting in self.globals:
            result += '  ' + setting + ': ' + self.globals[setting] + '\n'
        return result

    def print_images(self):
        result = 'Images:\n'
        for image in self.images.keys():
            result += '  ' + image + '\n'
            for item in self.images[image]:
                result += '    ' + item + ': ' + self.images[image][item] + '\n'
        return result
