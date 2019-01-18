"""General utilities.
"""
import json
import logging
import os
from pathlib import Path
import subprocess as sbp
import sys
import time
from typing  import Tuple
import warnings


def setupLogging(
    log_path=None,
    file_name="script_log",
    log_level=logging.INFO,
    logging_format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    custom_handlers=()):
    """Initialize the logger. Single process version.
    Logs both to file and stderr."""

    #
    # Get the log level
    #
    if type(log_level) == str:
        log_level = getattr(logging, log_level.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % log_level)

    #
    # config console handler.
    #
    logging.basicConfig(level=log_level, format=logging_format)

    if log_path is None:
        return

    #
    # Create a unique name for the log file.
    #
    if not os.path.isdir(log_path):
        os.makedirs(log_path)

    log_file = os.path.join(log_path, file_name)

    logging.info("Logging to: {}".format(log_file))

    #
    # Log to file.
    #
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logFormatter = logging.Formatter(logging_format)

    handler = logging.FileHandler(log_file, "w", encoding=None, delay="true")
    handler.setFormatter(logFormatter)
    logger.addHandler(handler)

    #
    # Add any custom loggers.
    #
    for handler in custom_handlers:
        handler.setFormatter(logFormatter)
        logger.addHandler(handler)


def safe_mkdirs(path):
    """Safely create path, warn in case of race.

    Args:
        path (string): Path to create.

    Note:
        Race condition can happen when several instantiations of the same code
        run in parallel, e.g. mpi.
    """

    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            import errno
            if e.errno == errno.EEXIST:
                warnings.warn("Failed creating path: {path}, probably a race"
                              " condition".format(path=path))


def getGitInfo(strict: bool=False) -> Tuple[str, str]:
    """Get version and diff information.

    Args:
        strict (bool, optional): If True (default) will raise an exception when
        there are modified or un-tracked python files in the repository.
    """

    from pkg_resources import resource_filename

    #
    # Change path to the repository
    #
    #cwd = os.getcwd()
    #os.chdir(os.path.abspath(resource_filename(__name__, '..')))
    ver_cmd = ['git', 'rev-list', '--full-history', '--all', '--abbrev-commit']
    p = sbp.Popen(ver_cmd, stdout=sbp.PIPE, stderr=sbp.PIPE)#, encoding="utf-8")
    ver, err = p.communicate()

    #
    # Create a diff file.
    #
    if strict:
        #
        # Raise an exception if there are modified or un-tracked files in the folder.
        #
        strict_cmd = "git status -u | egrep -v 'ipynb|notebooks\/' | egrep '\.py$'"
        o, e = sbp.Popen(strict_cmd, stdout=sbp.PIPE, stderr=sbp.PIPE, shell=True)\
            .communicate()
        o = o.decode("utf-8")
        if o != '':
            uncommited_files = "\n".join(o.split())
            err_msg = "The working directory contains uncommited files:\n{}\n"\
                .format(uncommited_files)
            err_msg += "Please commit or run `getGitInfo` in unstrict mode"
            raise Exception(err_msg)

        diff = None
    else:
        diff_cmd = 'git diff -- "*.py"'
        p = sbp.Popen(diff_cmd, stdout=sbp.PIPE, stderr=sbp.PIPE,
                      shell=True)#, encoding="utf-8")
        diff, err = p.communicate()

    #os.chdir(cwd)

    ver = ver.strip().split()
    version = "%04d_%s" % (len(ver), ver[0].decode("utf-8"))

    return version, diff


def getJOBID():
    """Get the lsf job id."""

    #
    # Get the jobid.
    #
    if 'LSB_JOBID' in os.environ:
        jobid = os.environ['LSB_JOBID']
    else:
        jobid = "noJobID"

    return jobid


def createResultFolder(
    results_path_format: str,
    base_path: str="/tmp/results",
    params: list=None,
    strict_git: bool=False,
    time_struct: time.struct_time=None
):
    """Create Results Folder

    This function creates a *unique* hierarchical results folder name. It is
    made of the git version and time stamp. It can also dump a diff log between
    the git version and the working copy at the time of run.

    Args:
        results_path_format (str): Format of results folder.
            Possible vars: base_path, script_name, git, date, time
            For example: "{base_path}/{script_name}/{git}/{jobid}/{date}_{time}"
        base_path (optional[str]): Root name of the results folder.
        params (optional[list]): List of parameters of the run. Will be saved
            as txt file.
        strict_git (optional[bool]): Assert that all code changes are committed.
        time_struct (optional[time.struct_time]): Use a specific time for timestamp.

    Returns:
        Full path of results folder.

    """

    try:
        git_version, diff = getGitInfo(strict=strict_git)
    except:
        git_version, diff = "no_gitinfo", b""

    if time_struct is None:
        time_struct = time.localtime()

    results_folder_parts = {
        "base_path": base_path,
        "script_name": Path(sys.argv[0]).stem,
        "git": git_version,
        "jobid": getJOBID(),
        "date": time.strftime('%y%m%d', time_struct),
        "time": time.strftime('%H%M%S', time_struct),
    }
    results_folder = results_path_format.format(**results_folder_parts)

    safe_mkdirs(results_folder)

    try:
        #
        # Create a symlink to the results folder so it can be browsed through
        # a browser. To serve this pages do:
        # > cd ~/JB_RESULTS
        # > python -m SimpleHTTPServer
        #
        html_folder = os.path.join(
            os.path.expanduser('~/JB_RESULTS/'), os.environ['LSB_JOBID']
        )
        os.symlink(results_folder, html_folder)
    except Exception:
        pass

    #
    # Create a diff file.
    #
    if diff is not None:
        with open(os.path.join(results_folder, 'git_diff.txt'), 'wb') as f:
            f.write(diff)

    #
    # Dump parameters into a file.
    #
    if params is not None:
        if type(params) is not dict:
            try:
                params = params.__dict__
            except:
                pass
        with open(os.path.join(results_folder, 'params.txt'), 'w') as f:
            json.dump(params, f)

    #
    # Log the command line.
    #
    command_line = "python "

    command_line += " ".join(sys.argv)
    command_line += "\n"

    with open(os.path.join(results_folder, 'cmdline.txt'), 'w') as f:
        f.write(command_line)

    results_folder =  os.path.abspath(results_folder)
    logging.info("Results folder: {}".format(results_folder))

    return results_folder
