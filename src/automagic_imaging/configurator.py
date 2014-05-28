import ConfigParser

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
        for option in parser.options('Global'):
            self.globals[option] = parser.get('Global', option)

        self.images = {}
        for images in parser.sections():
            if images == 'Global':
                continue
            image_options = {}
            for option in parser.options(images):
                image_options[option] = parser.get(images, option)
            self.images[images] = image_options
