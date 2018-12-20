from experiment import Experiment
import logging
from traitlets import Enum, Float, Int


class Main(Experiment):
    #
    # Parameters of experiment
    #
    epochs = Int(10, config=True, help="Number of epochs")
    lr = Float(0.1, config=True, help="Learning rate of training")
    loss = Enum(("mse", "l1"), config=True, default_value="mse", help="Loss type.")

    def run(self):
        """Running the experiment"""

        logging.info("Starting experiment")
        logging.info("Using {} loss".format(self.loss))

        for i in range(self.epochs):
            logging.info("Epoch: [{}/{}]".format(i, self.epochs))

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = Main()
    main.initialize()
    main.start()
