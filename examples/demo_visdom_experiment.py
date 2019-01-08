"""
This demo shows how to use the `experiment` package to log both to `Visdom` and `mlflow`.
"""
from experiment import MLflowExperiment
from experiment import VisdomExperiment
from experiment.visdom import Line, Window
import logging
import mlflow
from traitlets import Enum, Float, Int
import time

try:
    from tqdm import trange
except ImportError:
    trange = range


class Main(MLflowExperiment, VisdomExperiment):
    #
    # Parameters of experiment
    #
    epochs = Int(100, config=True, help="Number of epochs")
    lr = Float(0.5, config=True, help="Learning rate of training")
    loss_type = Enum(("mse", "l1"), config=True, default_value="mse", help="Loss type.")

    def run(self):
        """Running the experiment"""

        logging.info("Starting experiment")
        logging.info("Using {} loss".format(self.loss_type))

        #
        # Create the Visdom window and loss plot. The same window can be used for multiple plots.
        #
        win = Window(env=self.visdom_env, xlabel="epoch", ylabel="Loss", title="Loss")
        loss_plot = Line("util", win)

        loss = 100
        for i in trange(self.epochs):
            loss_plot.append(x=i, y=loss)
            mlflow.log_metric("loss", loss)

            loss = loss * self.lr
            time.sleep(.5)

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = Main()
    main.initialize()
    main.start()
