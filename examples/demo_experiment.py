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

    results_path_format = Unicode("{base_path}/{script_name}/{date}_{time}")

    #
    # Parameters of experiment
    #
    epochs = Int(100, config=True, help="Number of epochs")
    lr = Float(0.1, config=True, help="Learning rate of training")
    loss_type = Enum(("mse", "l1"), config=True, default_value="mse", help="Loss type.")

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
