import os
import subprocess

# Defaults
defaults = []
defaults['path'] = './private/var/radmind/'
defaults['comm'] = defaults['path'] + 'client/command.K'
defaults['port'] = '6223' # For certs
defaults['auth'] = '2'    # For certs
defaults['fsdo'] = '/tmp/fsdiff_out.T'

def full(cert, rserver, path=defaults['path'], port=defaults['port'],
         auth=defaults['auth'], command=defaults['comm'],
         fsdiff_out=defaults['fsdo']):
    run_ktcheck(cert, path, port, auth, command, rserver)
    run_fsdiff(command, fsdiff_out)
    run_lapply(cert, fsdiff_out, path, port, auth, command, rserver)
    run_post_maintenance()

def run_ktcheck(cert, rserver, path=defaults['path'], port=defaults['port'],
            auth=defaults['auth'], command=defaults['comm']):
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
    return subprocess.check_output(ktcheck)

def run_fsdiff(command=defaults['comm'], outfile=None):
    fsdiff = [
        '/usr/local/bin/fsdiff',
        '-A',
        '-c', 'sha1',
        '-K', command,
        '-I',
        '-%'
    ]
    if outfile:
        fsdiff.append('-o')
        fsdiff.append(outfile)
    return subprocess.check_output(fsdiff)

def run_lapply(cert, rserver, infile, path=defaults['path'], port=defaults['port'],
               auth=defaults['auth'], command=defaults['comm']):
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
    return subprocess.check_output(lapply)

def run_post_maintenance():
    # We use a system called Xhooks to manage our post-maintenance routines.
    # If you don't have Xhooks... you don't need post-maintenance.
    if not os.path.exists('./Library/Xhooks'):
        return

    # Remove these files in case radmind had an error and didn't delete them:
    remove_these = [
        './Library/Xhooks/Preferences/triggerfiles/run_maintenance',
        './Library/Xhooks/Preferences/triggerfiles/run_maintenance_balanced',
        './Library/Xhooks/Preferences/triggerfiles/use_radmind_shadow'
    ]
    for file in remove_these:
        if os.path.exists(file):
            os.remove(file)
    subprocess.check_output(['./Library/Xhooks/Modules/xhooks/bin/radmind_xhooks_conf.pl'],
                            stderr=subprocess.STDOUT)
    touch('./Library/Xhooks/Preferences/triggerfiles/logout_hook_finished')
    touch('./System/Library/Extensions')
    subprocess.check_output(['./usr/bin/update_dyld_shared_cache', '-root', '.',
                             '-force', '-universal_boot'],
                            stderr=subprocess.STDOUT)

def touch(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'a'):
        os.utime(path, None)
