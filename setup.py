from distutils.core import setup

setup(
    name='Automagic Imaging',
    version='0.3',
    url='https://github.com/univ-of-utah-marriott-library-apple/automated_osx_imaging',
    author='Pierce Darragh, Marriott Library IT Services',
    author_email='mlib-its-mac-github@lists.utah.edu',
    description=('A group of scripts to set up automated OS X imaging with Radmind.'),
    license='MIT',
    packages=['automagic_imaging',
              'automagic_imaging.scripts'],
    package_dir={'automagic_imaging': 'src/automagic_imaging',
                 'automagic_imaging.scripts': 'src/automagic_imaging/scripts'},
    scripts=['scripts/radmind_auto_image_creator.py'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
)
