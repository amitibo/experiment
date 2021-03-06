# -*- coding: utf-8 -*-

"""
Configuration environment for experiments.

This module introduces a framework for configuring experiments. It is based on the jupyter configuration
framework (traitlets and application).

.. code-block:: python

    from experiment import Experiment
    from traitlets import Float


    class Main(Experiment):

        lr = Float(0.1, config=True, help="Learning rate of training")

        def run(self):
            <Run the experiment>

    if __name__ == "__main__":
        main = Main()
        main.initialize()
        main.start()

For more examples see the `examples` folder.
"""

from copy import deepcopy
import errno
import logging
import os
from pathlib import Path
import sys
import time

from ipython_genutils.text import wrap_paragraphs
from traitlets.config.application import Application, catch_config_error, Configurable
from traitlets.config.loader import ConfigFileNotFound
from traitlets import Bool, Dict, Enum, Instance, List, Unicode

from .utils import createResultFolder, getJOBID, setupLogging


def ensure_dir_exists(path, mode=0o777):
    """ensure that a directory exists

    If it doesn't exist, try to create it, protecting against a race condition
    if another process is doing the same.

    The default permissions are determined by the current umask.
    """
    try:
        os.makedirs(path, mode=mode)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    if not os.path.isdir(path):
        raise IOError("%r exists but is not a directory" % path)


class Experiment(Application):
    """An experiment with CLI configuration support."""

    description = Unicode(u"An experiment with CLI configuration support.")

    name = Unicode(Path(sys.argv[0]).stem)

    log_level = Enum((0, 10, 20, 30, 40, 50, 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
                     config=True,
                     default_value=logging.INFO,
                     help="Set the log level by value or name.")

    strict_git = Bool(False, config=True,
                      help="Force (by fail running) that all code changes are committed before execution.")

    results_path_format = Unicode(help="Format of the results path. Default:"
                                       " '{base_path}/{script_name}/{git}/{jobid}/{date}_{time}'")

    def _results_path_format_default(self):

        return os.environ.get(
            "RESULTS_PATH_FORMAT",
            "{base_path}/{script_name}/{git}/{jobid}/{date}_{time}"
        )

    #
    # Note:
    # The results_path is not a `config` member as it will be saved in the config file and later
    # when loaded will oeverwrite the new results_path.
    #
    results_path = Unicode(help="Base path for experiment results.")

    def _results_path_default(self):

        results_base_path = os.environ.get("RESULTS_BASE", "/tmp/results")
        results_path = createResultFolder(
            results_path_format=self.results_path_format,
            base_path=results_base_path,
            strict_git=self.strict_git,
            time_struct=self.exp_time
        )
        return results_path

    custom_log_handlers = List(help="List of custom logging handlers.")

    exp_time = Instance(time.struct_time, help="Start time of the experiment.")

    def _exp_time_default(self):
        return time.localtime()

    #
    # Configuration loading and saving.
    #
    generate_config = Bool(True, config=True, help="Generate config file.")

    config_file_name = Unicode("config.py", config=True, help="Specify a config file to save.")

    config_file = Unicode(config=True, help="Full path of a config file to load.")

    #
    # Logic
    #
    cache = Dict(help="Container for storing results across different parts of the experiment.")

    def class_config_section(self, cls, classes=None):
        """Get the config section for this class.
        Parameters
        ----------
        classes: list, optional
            The list of other classes in the config file.
            Used to reduce redundant information.

        Note:
            I overwrite this function in order to have the configuration in "config.py"
            show the actual configuration used and have it non commented.
        """

        def c(s):
            """return a commented, wrapped block."""
            s = '\n\n'.join(wrap_paragraphs(s, 78))

            return '## ' + s.replace('\n', '\n#  ')

        # section header
        breaker = '#' + '-' * 78
        parent_classes = ', '.join(
            p.__name__ for p in cls.__bases__
            if issubclass(p, Configurable)
        )

        s = "# %s(%s) configuration" % (cls.__name__, parent_classes)
        lines = [breaker, s, breaker]
        # get the description trait
        desc = cls.class_traits().get('description')
        if desc:
            desc = desc.default_value
        if not desc:
            # no description from trait, use __doc__
            desc = getattr(cls, '__doc__', '')
        if desc:
            lines.append(c(desc))
            lines.append('')

        for name, trait in sorted(cls.class_own_traits(config=True).items()):
            default_repr = trait.default_value_repr()

            if classes:
                defining_class = cls._defining_class(trait, classes)
            else:
                defining_class = cls
            if defining_class is cls:
                # cls owns the trait, show full help
                if trait.help:
                    lines.append(c(trait.help))
                if 'Enum' in type(trait).__name__:
                    # include Enum choices
                    lines.append('#  Choices: %s' % trait.info())
                lines.append('###  (default: %s)' % default_repr)
            else:
                # Trait appears multiple times and isn't defined here.
                # Truncate help to first line + "See also Original.trait"
                if trait.help:
                    lines.append(c(trait.help.split('\n', 1)[0]))
                lines.append('###  See also: %s.%s' % (defining_class.__name__, name))

            lines.append('c.%s.%s = %s' % (cls.__name__, name, repr(trait.get(self))))
            lines.append('')
        return '\n'.join(lines)

    def generate_config_file(self, classes=None):
        """generate default config file from Configurables"""
        lines = ["# Configuration file for %s." % self.name]
        lines.append('')
        classes = self.classes if classes is None else classes
        config_classes = list(self._classes_with_config_traits(classes))
        for cls in config_classes:
            lines.append(self.class_config_section(cls, config_classes))
        return '\n'.join(lines)

    def write_config(self):
        """Write our config to a .py config file"""

        config_file = os.path.join(
            self.results_path,
            Path(self.config_file_name).stem + '.py'
        )

        config_text = self.generate_config_file()
        if isinstance(config_text, bytes):
            config_text = config_text.decode('utf8')

        print("Writing default config to: %s" % config_file)
        ensure_dir_exists(os.path.abspath(os.path.dirname(config_file)), 0o700)
        with open(config_file, mode='w') as f:
            f.write(config_text)

    def create_aliases(self):
        """Flatten all class traits using aliasses."""

        self.aliases["strict_git"] = "Experiment.strict_git"

        self.aliases["config_file"] = "Experiment.config_file"

        cls = self.__class__
        for k, trait in sorted(cls.class_traits(config=True).items()):
            self.aliases[trait.name] = ("%s.%s" % (cls.__name__, trait.name))

    @catch_config_error
    def initialize(self, argv=None):

        self.create_aliases()

        self.parse_command_line(argv)

        if self.config_file:
            path, config_file_name = os.path.split(self.config_file)
            self.load_config_file(
                config_file_name,
                path=path
            )

    def _setup_logging(self):
        """Setup logging of experiment."""

        setupLogging(
            self.results_path,
            log_level=self.log_level,
            custom_handlers=self.custom_log_handlers
        )

        logging.info("Created results path: {}".format(self.results_path))

    def start(self):
        """Start the whole thing"""

        self._setup_logging()

        if self.generate_config:
            self.write_config()

        self.run()

    def run(self):
        """The logic of the experiment.

        Should be implemented by the subclass.
        """

        raise NotImplementedError("The `run` method should be implemented by the subclass.")


class MLflowExperiment(Experiment):
    """A singleton experiment with support for `mlflow` logging.

    Note:
        This object will setup a connection with the `mlflow` server.
        To successfully do so it is recommended to setup the following
        environment variable:

        * MLFLOW_SERVER - URL:PORT of mlflow server.
    """

    description = Unicode(u"An experiment with MLflow configuration support.")

    mlflow_server = Unicode(config=True, help="default mlflow server.")

    def _mlflow_server_default(self):

        return os.environ.get("MLFLOW_SERVER", 'http://localhost:5000')

    def start(self):
        """Start the whole thing"""

        self._setup_logging()

        if self.generate_config:
            self.write_config()

        #
        # Setup mlflow
        #
        import mlflow
        mlflow.set_tracking_uri(self.mlflow_server)
        experiment_id = mlflow.set_experiment(self.name)

        #
        # Run the script under mlflow
        #
        with mlflow.start_run(experiment_id=experiment_id):
            #
            # Log the run parametres to mlflow.
            #
            mlflow.log_param("results_path", self.results_path)

            cls = self.__class__
            for k, trait in sorted(cls.class_own_traits(config=True).items()):
                mlflow.log_param(trait.name, repr(trait.get(self)))

            self.run()


class VisdomExperiment(Experiment):
    """A singleton experiment with support of `Visdom` logging.

    Note:
        This object will setup a connection with the `visdom` server.
        To successfully do so it is recommended to setup the following
        environment variables:

        * VISDOM_SERVER_URL - URL of visdom server.
        * VISDOM_USERNAME - User name to use for logging to the visdom server (optional).
        * VISDOM_PASSWORD - Password to use for loffing to the visdom server (optional).
    """

    description = Unicode(u"An experiment with Visdom configuration support.")

    visdom_server = Unicode(config=True, help="default visdom server.")

    vis = Instance(name="vis", klass=object, help="Visdom client object.")

    def _vis_default(self):

        from .visdom import setup_visdom

        results_path = Path(self.results_path)

        #
        # Setup visdom callbacks
        #
        vis = setup_visdom(
            server=self.visdom_server,
            log_to_filename=results_path / "visdom.log",
        )

        return vis

    visdom_env = Unicode(help="Name of Visdom environment where the experiment is logged.")

    visdom_params_win = Instance(
        name="visdom_params_win", klass=object,
        help="Visdom window logging experiment parameters.")

    def _visdom_env_default(self):

        visdom_env = "{}_{}-{}".format(
            self.name.replace("_", "-"),
            getJOBID(),
            time.strftime('%y%m%d-%H%M%S', self.exp_time)
        )

        return visdom_env

    def _setup_logging(self):
        """Setup logging of experiment."""

        from .visdom import monitor_gpu
        from .visdom import write_conf
        from .visdom import VisdomLogHandler
        from .visdom import create_parameters_windows
        #
        # The following is just for initiating the connection with the visdom server.
        #
        vis = self.vis

        #
        # Monitor GPU.
        #
        monitor_gpu(self.visdom_env)

        #
        # Create a properties window for paramters.
        #
        if len(self.class_own_traits(parameter=True)) > 0:
            _, self.visdom_params_win = create_parameters_windows(
                params_object=self,
                env=self.visdom_env,
            )

        #
        # Setup logging.
        #
        config_text = self.generate_config_file(classes=[self.__class__])
        write_conf(self.visdom_env, text=config_text)
        self.custom_log_handlers.append(VisdomLogHandler(self.visdom_env, title="Logging"))

        super(VisdomExperiment, self)._setup_logging()


class TensorboardXExperiment(Experiment):
    """A singleton experiment with support of `TensorBoard` logging.

    Note:
        This object requires `tensorBoardX` to produce log summaries.
        The log summaries are stored in the path set by `self.tb_log_dir`.
        By default a unique folder will be created by script_name/jobid_date/
        To successfully do so it is recommended to setup the following
        environment variable:

        * TENSORBOARD_BASE_DIR - Base path for storing log summaries (optional).
          Defaults to `/tmp/tensorboard`.
    """

    description = Unicode(u"An experiment with TensorboardX configuration support.")

    tb_log_dir = Unicode(help="Path where to store the tensorboard logs.")

    def _tb_log_dir_default(self):
        tb_base_dir = os.environ.get("TENSORBOARD_BASE_DIR", '/tmp/tensorboard')

        jobid = getJOBID()
        timestamp = time.strftime('%y%m%d_%H%M%S', self.exp_time)

        tb_log_dir = os.path.join(
            tb_base_dir,
            self.name,
            "{}_{}".format(jobid, timestamp)
        )

        return tb_log_dir

    summary_writer = Instance(name="summary_writer", klass=object,
                          help="TensorboardX SummaryWriter object.")

    def _summary_writer_default(self):

        from tensorboardX import SummaryWriter

        summary_writer = SummaryWriter(log_dir=self.tb_log_dir)

        return summary_writer

    log_to_text = Bool(False, config=True, help="Whether to record logs as text summary.")

    def _setup_logging(self):
        """Setup logging of experiment."""

        from .tensorboard_x import monitor_gpu
        from .tensorboard_x import write_conf
        from .tensorboard_x import TensorBoardXLogHandler

        #
        # Monitor GPU.
        #
        monitor_gpu(self.summary_writer)

        #
        # Setup logging.
        #
        config_text = self.generate_config_file(classes=[self.__class__])
        write_conf(self.summary_writer, text=config_text)

        if self.log_to_text:
            self.custom_log_handlers.append(TensorBoardXLogHandler(self.summary_writer, title="Logging"))

        super(TensorboardXExperiment, self)._setup_logging()
