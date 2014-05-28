try:
    from management_tools import loggers
except ImportError as e:
    print "You need the 'Management Tools' module to be installed first."
    print "https://github.com/univ-of-utah-marriott-library-apple/management_tools"
    sys.exit(3)

def logger (log, log_dest='', name=''):
    '''Creates and returns the logger to be used throughout.

    If it was not specified not to create a log, the log will be created in either
    the default location (as per management_tools) or a specified location.

    Otherwise, the logger will just be console output.
    '''

    if not name:
        name = 'unnamed'

    if log:
        # A logger!
        if not log_dest:
            return loggers.file_logger(name)
        else:
            return loggers.file_logger(name, path=log_dest)
    else:
        # A dummy logger.  It won't record anything to file.
        return loggers.stream_logger(1)
