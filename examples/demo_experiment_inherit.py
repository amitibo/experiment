from experiment import Experiment
import logging
import time
from traitlets import Enum, Float, Int, Unicode

from demo_experiment import Main

try:
    from tqdm import trange
except ImportError:
    trange = range


class MainChild(Main):
    #
    # Description of the experiment. Used in the help message.
    #
    description = Unicode("Example of experiment inheritance.")

    #
    # Parameters of experiment
    # Note:
    # Overwriting the type, Enum fields or range of a parent class trait is
    # currently not supported.
    #
    loss_type_new = Enum(("CE", "BCE"), config=True, default_value="CE", help="Loss type.")

    def run(self):
        """Running the experiment"""

        logging.info("Starting experiment")
        logging.info("Using {} loss".format(self.loss_type_new))

        loss = 100
        for i in trange(self.epochs):
            loss = loss * self.lr
            time.sleep(.5)

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = MainChild()
    main.initialize()
    main.start()
