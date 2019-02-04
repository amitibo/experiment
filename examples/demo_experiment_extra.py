"""
Loading a config file with extra arguments raises a warning but continues the run::

    > python demo_experiment_extra.py
    > python demo_experiment.py --config_file <PATH TO CONFIG FILE>
    [Main] WARNING | Config option `extra_type` not recognized by `Main`.
    ...
"""
from experiment import Experiment
import logging
import time
from traitlets import Enum, Float, Int, Unicode

try:
    from tqdm import trange
except ImportError:
    trange = range


class Main(Experiment):
    #
    # Description of the experiment. Used in the help message.
    #
    description = Unicode("Basic experiment.")

    #
    # Overwrite results path format. Supported vars: base_path, script_name, git, date, time
    #
    results_path_format = Unicode("{base_path}/{script_name}/{date}_{time}")

    #
    # Parameters of experiment
    #
    epochs = Int(100, config=True, help="Number of epochs")
    lr = Float(0.1, config=True, help="Learning rate of training")
    loss_type = Enum(("mse", "l1"), config=True, default_value="mse", help="Loss type.")
    extra_type = Int(1, config=True, help="Extra type to test configration loading.")

    def run(self):
        """Running the experiment"""

        logging.info("Starting experiment")
        logging.info("Using {} loss".format(self.loss_type))

        loss = 100
        for i in trange(self.epochs):
            loss = loss * self.lr
            time.sleep(.5)

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = Main()
    main.initialize()
    main.start()
