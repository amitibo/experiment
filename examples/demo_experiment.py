from experiment import Experiment
import logging
from traitlets import Float, Int


class Main(Experiment):
    #
    # Parameters of experiment
    #
    epochs = Int(10, config=True, help="Number of epochs")

    lr = Float(0.1, config=True, help="Learning rate of training")

    def run(self):
        """Running the experiment"""

        logging.info("Starting experiment")

        for i in range(self.epochs):
            logging.info("Epoch: [{}/{}]".format(i, self.epochs))

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = Main()
    main.initialize()
    main.start()
