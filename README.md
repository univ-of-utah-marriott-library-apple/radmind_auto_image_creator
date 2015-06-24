Automated OS X Imaging
======================

Automagically create images for OS X computers using Radmind.

## Contents

* [Requirements](#requirements)
* [Contact](#contact)
* [Purpose](#purpose)
* [Usage](#usage)
  * [Options](#options)
* [Technical](#technical)
  * [Sparse Images](#sparse-images)
* [Config](#config)
  * [Global](#global)
  * [Image](#image)
* [Update History](#update-history)

## Download

[Download the latest installer here!](../../releases/)

## Requirements

* Python 2.7.x (which you can download [here](https://www.python.org/download/))

Note: This project has not seen any significant updates in some time, and so does not use our common [Management Tools](https://github.com/univ-of-utah-marriott-library-apple/management_tools) package. There are currently no plans to integrate Management Tools into the Radmind Automatic Image Creator.

## Contact

If you have any comments, questions, or other input, either [file an issue](../../issues) or [send us an email](mailto:mlib-its-mac-github@lists.utah.edu). Thanks!

## Uninstall

To remove the Ramind Automatic Image Creator from your system, download the .dmg and run the "Uninstall Automagic Imaging [x.x.x]" package to uninstall it. (Note that the version indicated does not actually matter, as any of the uninstall packages will remove any installed version of the Radmind Automatic Image Creator).

## Purpose

In an effort to streamline our imaging efforts, we created an automatic imaging system to interface with radmind. This system relies on you having radmind certificates set up and plenty of free disk space available.

## Usage

To use the Radmind Automatic Image Creator, you must have your radmind server set up to use certificates for specific command files. For a guide on this process, see [this guide](http://blog.magnusviri.com/radmind-tls-part-1.html).

```
$ radmind_auto_image_creator.py [-hvni] [-l log] [-c config] [-t tmp_dir] [-o out_dir] [-r rserver] [-C cert] [-I image] [-V volume] [-s sparse] [--persist-on-fail] [--persist-all]
```

### Options

| Option                                | Purpose                                                                                   |
|---------------------------------------|-------------------------------------------------------------------------------------------|
| `-h` `--help`                         | Prints help message and quits.                                                            |
| `-v` `--version`                      | Prints only the version information and quits.                                            |
| `-n` `--no-log`                       | Redirects logging to the console (stdio).                                                 |
| `-l log` `--log log`                  | Outputs log files to `log` instead of the default. (This is overridden by `--no-log`.)    |
| `-i` `--interactive`                  | Runs the script in interactive mode.                                                      |
| `-c config` `--config config`         | Use `config` as the input configuration file.                                             |
| `-t tmp_dir` `--tmp_dir tmp_dir`      | Use `tmp_dir` as the temporary directory for sparse images.                               |
| `-o out-dir` `--out_dir out_dir`      | Use `out_dir` as the output directory for final, read-only images.                        |
| `-r rserver` `--rserver rserver`      | Specify the radmind server address as `rserver`.                                          |
| `-C cert` `--cert cert`               | Use certificate `cert` to run radmind.                                                    |
| `-I image` `--image-name image`       | Name the finished image `image`.                                                          |
| `-V volume` `--volume-name volume`    | Name the mounted volume for the finished image `volume`.                                  |
| `-s sparse` `--sparse sparse`         | Try to use `sparse` as a starting point for radmind.                                      |
| `--persist-all`                       | Prevent the script from deleting any sparse images.                                       |
| `--persist-on-fail`                   | Prevent the script from deleting sparse images when radmind fails.                        |

#### Image Names

Image names are generally given as something like "Staff" or "Student_Lab". These names would result in sparse images named `Staff.sparseimage` and `Student_Lab.sparseimage` respectively. The converted read-only disk images have a naming scheme of: `YYYY.mm.dd_IMAGENAME_OSVERSION_OSBUILD.dmg`, where:

 * `YYYY` is the year
 * `mm` is the two-digit month
 * `dd` is the two-digit day
 * `IMAGENAME` is the name of the image given via `--image-name image`
 * `OSVERSION` is the version of the operating system (e.g. 10.9, 10.10)
 * `OSBUILD` is the current build number

#### Volume Names

The volume name, given with `--volume-name volume`, will appear whenever the disk image is mounted. This can be useful if you name your volumes in a particular way (for example, all of our regular volumes are named "Mac OS X"). Additionally, if you like to keep bootable minimal disk images, you can add `$VERSION` and `$BUILD` to offer more information. We maintain a bootable disk image with a volume name given as `Firewire $VERSION`, and this (currently) shows up as "Firewire 10.10" when we see it in Finder.

## Technical

We recommend setting up this imaging system on a computer with plenty of hard disk space. To create the images, the script creates an empty sparse disk image. Radmind is run relative to the root of this disk image, so the entire contents of the command file will be located locally. After radmind completes successfully, the disk image will be converted to a read-only format and compressed.

### Sparse Images

The Automated Radmind Image Creator uses sparse images to produce images. A sparse image is a type of disk image that is expandable, meaning that you can mount it and then add files to it and it won't stop you (although you can specify a maximum size).

In our environment, we use `--persist-all` to keep all sparse images that are created. This is useful because we can then use `--sparse` to use those sparse images in the future. This allows the imaging process to take less time than if it ran from scratch every time (and is probably better on your storage media due to fewer rewrites).

## Config

The configuration file serves as an easy way to run multiple images consecutively with minimal user interaction. There are two types of sections for the config file: Global and Image.

### Global

```
[Global]
tmp_dir: /tmp
out_dir: /path/to/images
rserver: radmind.example.com
```

The Global section has three keys that are all required:

* `tmp_dir`: the directory to store sparse images in
* `out_dir`: the directory to put the finished read-only disk images
* `rserver`: the address of the radmind server being used

### Image

```
[My Image]
cert: /path/to/certificate.pem
volume: OS X $VERSION-$BUILD
```

You can have any number of image sections, provided you have enough certificates to accommodate them all. The name of the image section should actually be whatever your image will be called, and it should have both a certificate path and a name for the volume. The shortcuts for version and build numbers can be used in the volume designator.

## Update History

This is a short, reverse-chronological summary of the updates to this project.

| Date       | Version | Update Description                                                                     |
|------------|:-------:|----------------------------------------------------------------------------------------|
| 2014-06-26 | 1.4.4   | More try/except blocks.                                                                |
| 2014-06-16 | 1.4.3   | Fixed descriptor update.                                                               |
| 2014-06-16 | 1.4.2   | Set number of file descriptors; bug fixes.                                             |
| 2014-06-13 | 1.4.1   | Improved persist functionality.                                                        |
| 2014-06-13 | 1.4.0   | Can now resume radmind from a sparse image.                                            |
| 2014-06-11 | 1.3.0   | Now compresses final read-only disk image.                                             |
| 2014-06-11 | 1.2.5   | Logging includes last five lines of file for failed radmind process.                   |
| 2014-06-10 | 1.2.4   | Multiple unmount attempts; delete failed images; fixed image renaming.                 |
| 2014-06-09 | 1.2.3   | Logging now includes more information.                                                 |
| 2014-06-09 | 1.2.2   | Corrected typo.                                                                        |
| 2014-06-09 | 1.2.1   | Corrected typo.                                                                        |
| 2014-06-09 | 1.2.0   | Can now use `$VERSION` in the volume name to substitute OS version.                    |
| 2014-06-06 | 1.1.2   | Updated repository url in `setup.py`.                                                  |
| 2014-06-05 | 1.1.1   | Wrapped delicate code in try/except blocks.                                            |
| 2014-06-05 | 1.1.0   | Added manual and interactive modes of input.                                           |
| 2014-06-03 | 1.0.9   | Attempts to force detach disks when unmount fails.                                     |
| 2014-06-03 | 1.0.8   | Adjusted hardlinks.                                                                    |
| 2014-06-03 | 1.0.7   | Improved logging and unmounting.                                                       |
| 2014-06-03 | 1.0.6   | Attempts to unmount multiple times (to give time for disk unlock).                     |
| 2014-06-03 | 1.0.5   | Radmind logging.                                                                       |
| 2014-06-02 | 1.0.4   | Implements xhooks post-maintenance properly.                                           |
| 2014-05-30 | 1.0.3   | More string formatting.                                                                |
| 2014-05-30 | 1.0.2   | Improper string formatting fixed.                                                      |
| 2014-05-30 | 1.0.1   | Adds radmind trigger files for xhooks.                                                 |
| 2014-05-30 | 1.0     | Updated logging output.                                                                |
| 2014-05-30 | 0.9.10  | `fsdiff` outfile is now removed if it already exists.                                  |
| 2014-05-30 | 0.9.9   | Fixed the conversion methods so they work properly.                                    |
| 2014-05-30 | 0.9.8   | Forgot `.path` in a method call.                                                       |
| 2014-05-30 | 0.9.7   | Further typo fixes.                                                                    |
| 2014-05-30 | 0.9.6   | Fixed a formatting typo.                                                               |
| 2014-05-30 | 0.9.5   | Unmounts failed images before aborting.                                                |
| 2014-05-30 | 0.9.4   | Fixed bless issues.                                                                    |
| 2014-05-30 | 0.9.3   | More typos.                                                                            |
| 2014-05-30 | 0.9.2   | Typo adjustment.                                                                       |
| 2014-05-30 | 0.9.1   | Renamed temporary files.                                                               |
| 2014-05-30 | 0.9     | Improved logging verbosity.                                                            |
| 2014-05-30 | 0.7.3   | Many minor adjustments to improve stability.                                           |
| 2014-05-30 | 0.7     | Blessing, ownership, error-checking, versioning all improved. Radmind calls revised.   |
| 2014-05-28 | 0.2.2   | Fixed issue where nested imports and some calls weren't working.                       |
| 2014-05-28 | 0.2     | Started work on wrapper script.                                                        |
| 2014-05-27 | 0.2     | Bless capabilities added.                                                              |
| 2014-05-27 | 0.2     | Image conversion now supported.                                                        |
| 2014-05-23 | 0.1     | Added `setup.py`.                                                                      |
| 2014-05-23 | 0.1     | Project started with basic image handling.                                             |
