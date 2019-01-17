"""
This demo shows how to use the `experiment` package to log both to `Tensorboard` and `mlflow`.
"""
from experiment import MLflowExperiment
from experiment import TensorboardXExperiment
import logging
import mlflow
from traitlets import Enum, Float, Int, Unicode
import time

try:
    from tqdm import trange
except ImportError:
    trange = range


class Main(MLflowExperiment, TensorboardXExperiment):

    description = Unicode("Demonstration of using Tensorboard and MLflow logging.")

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

        loss = 100
        for i in trange(self.epochs):
            self.summary_writer.add_scalar(
                tag='training/loss',
                scalar_value=loss,
                global_step=i+1
            )
            mlflow.log_metric("loss", loss)

            loss = loss * self.lr
            time.sleep(.5)

        logging.info("Experiment finished")


if __name__ == "__main__":
    main = Main()
    main.initialize()
    main.start()
