import datetime
import os
import subprocess

# Defaults
defaults = {}
defaults['path'] = './private/var/radmind/'
defaults['comm'] = defaults['path'] + 'client/command.K'
defaults['port'] = '6223' # For certs
defaults['auth'] = '2'    # For certs
defaults['fsdo'] = '/tmp/fsdiff_out.T'

def full(cert, rserver, path=defaults['path'], port=defaults['port'],
         auth=defaults['auth'], command=defaults['comm'],
         fsdiff_out=defaults['fsdo']):
    run_ktcheck(cert, rserver, path, port, auth, command)
    run_fsdiff(command, fsdiff_out)
    run_lapply(cert, rserver, fsdiff_out, path, port, auth, command)
    run_post_maintenance()

def run_ktcheck(cert, rserver, path=defaults['path'], port=defaults['port'],
            auth=defaults['auth'], command=defaults['comm'], logfile=None):
    if not os.path.exists(command):
        touch(command)
    ktcheck = [
        '/usr/local/bin/ktcheck',
        '-c', 'sha1',
        '-C',
        '-D', path,
        '-ex_ktcheck',
        '-h', rserver,
        '-i',
        '-I',
        '-K', command,
        '-p', port,
        '-w', auth,
        '-y', cert,
        '-z', cert
    ]
    STDOUT = None
    if logfile:
        if not os.path.isfile(logfile):
            touch(logfile)
        STDOUT = open(logfile, 'w')
    if not logfile:
        STDOUT = open(os.devnull, 'w')
    result = subprocess.call(ktcheck,
                             stderr=subprocess.STDOUT,
                             stdout=STDOUT)
    if result > 1:
        raise RuntimeError("ktcheck did not complete successfully!")

def run_fsdiff(command=defaults['comm'], outfile=None, logfile=None):
    if not outfile:
        outfile = './private/var/log/radmind/fsdiff_output.T'
    if not os.path.isdir(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))
    if os.path.exists(outfile):
        os.remove(outfile)
    fsdiff = [
        '/usr/local/bin/fsdiff',
        '-A',
        '-c', 'sha1',
        '-K', command,
        '-I',
        '-%',
        '-o', outfile,
        '.'
    ]
    STDOUT = None
    if logfile:
        if not os.path.isfile(logfile):
            touch(logfile)
        STDOUT = open(logfile, 'w')
    if not logfile:
        STDOUT = open(os.devnull, 'w')
    result = subprocess.call(fsdiff,
                             stderr=subprocess.STDOUT,
                             stdout=STDOUT)
    if result != 0:
        raise RuntimeError("fsdiff did not complete successfully!")

def run_lapply(cert, rserver, path=defaults['path'], port=defaults['port'],
               auth=defaults['auth'], command=defaults['comm'], infile=None,
               logfile=None):
    if not infile:
        infile = './private/var/log/radmind/lapply_input.T'
    if not os.path.isfile(infile):
        raise ValueError("Invalid input file: " + str(infile))
    lapply = [
        '/usr/local/bin/lapply',
        '-c', 'sha1',
        '-C',
        '-ex_lapply',
        '-F',
        '-i',
        '-I',
        '-h', rserver,
        '-p', port,
        '-w', auth,
        '-y', cert,
        '-z', cert,
        infile
    ]
    STDOUT = None
    if logfile:
        if not os.path.isfile(logfile):
            touch(logfile)
        STDOUT = open(logfile, 'w')
    if not logfile:
        STDOUT = open(os.devnull, 'w')
    result = subprocess.call(lapply,
                             stderr=subprocess.STDOUT,
                             stdout=STDOUT)
    if result != 0:
        raise RuntimeError("lapply did not complete successfully!")

def run_post_maintenance():
    # We use a system called Xhooks to manage our post-maintenance routines.
    # If you don't have Xhooks... you don't need post-maintenance.
    if not os.path.exists('./Library/Xhooks'):
        return

    # Common directories used:
    triggerfiles = './Library/Xhooks/Preferences/triggerfiles/'
    radmind_log = './private/var/log/radmind/'
    # Remove these files in case radmind had an error and didn't delete them:
    remove_these = [
        triggerfiles + 'run_maintenance',
        triggerfiles + 'run_maintenance_balanced',
        triggerfiles + 'use_radmind_shadow',
        radmind_log + 'wait_for_radmind'
    ]
    for file in remove_these:
        if os.path.exists(file):
            os.remove(file)

    # Touch these files/directories:
    touch_these = [
        triggerfiles + 'loginpanel_message',
        triggerfiles + 'logout_hook_finished',
        triggerfiles + 'radmind_finished',
        triggerfiles + 'radmind_xhooks_conf_finished',
        radmind_log + 'maintenance_lastrun',
        './System/Library/Extensions'
    ]
    for file in touch_these:
        try:
            touch(file)
        except:
            pass

    # Write special things to certain places:
    if os.path.isfile(triggerfiles + 'loginpanel_message'):
        # Defines what is shown on login, something like:
        # --6.3 0
        message = '--' + datetime.datetime.now().strftime('%-m.%-d') + ' 0'
        with open(triggerfiles + 'loginpanel_message', 'w') as f:
            f.write(message)
    if os.path.isfile(radmind_log + 'maintenance_lastrun'):
        # Put the date (formatted a particular way) in this file:
        date = subprocess.check_output(['date', '"+%H:%M:%S %D %Z"'])
        with open(radmind_log + 'maintenance_lastrun', 'w') as f:
            f.write(date)

    # Run some scripts:
    result = subprocess.call(['./Library/Xhooks/Modules/xhooks/bin/radmind_xhooks_conf.pl'],
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("./Library/Xhooks/Modules/xhooks/bin/radmind_xhooks_conf.pl was unsuccesful.")
    result = subprocess.call(['./usr/bin/update_dyld_shared_cache',
                              '-root', '.', '-force', '-universal_boot'],
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("./usr/bin/update_dyld_shared_cache was unsuccesful.")

def touch(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if os.path.isdir(path):
        try:
            os.utime(path, None)
        except:
            raise RuntimeError("Unable to touch directory '" + path + "'")
    else:
        try:
            with open(path, 'a'):
                os.utime(path, None)
        except:
            raise RuntimeError("Unable to touch file '" + path + "'")
