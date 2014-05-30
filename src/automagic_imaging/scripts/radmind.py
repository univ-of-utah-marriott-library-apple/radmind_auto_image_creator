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
    result = subprocess.call(ktcheck,
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result > 1:
        raise RuntimeError("ktcheck did not complete successfully!")

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
    fsdiff.append('.')
    result = subprocess.call(fsdiff,
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("fsdiff did not complete successfully!")

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
    result = subprocess.call(lapply,
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("lapply did not complete successfully!")

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
    result = subprocess.call(['./Library/Xhooks/Modules/xhooks/bin/radmind_xhooks_conf.pl'],
                             stderr=subprocess.STDOUT,
                             stdout=open(os.devnull, 'w'))
    if result != 0:
        raise RuntimeError("./Library/Xhooks/Modules/xhooks/bin/radmind_xhooks_conf.pl was unsuccesful.")
    touch('./Library/Xhooks/Preferences/triggerfiles/logout_hook_finished')
    touch('./System/Library/Extensions')
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
