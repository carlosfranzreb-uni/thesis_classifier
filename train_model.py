""" Train the classifier neural network. """


from time import time
import logging

from torch.nn import BCELoss
from torch.optim import lr_scheduler

from descendant_mask import create_mask 

from cnn.init_training import init
from cnn.asymmetric_loss import ASL
from cnn.maxconstraint_loss import MCL
from cnn.convolutional_model import Classifier as ConvClassifier
from cnn.sum_model import Classifier as SumClassifier
from cnn.coherent_model import Classifier as CoherentClassifier


if __name__ == '__main__':
  """ Set the parameters for the training run.
  - Models: ConvClassifier, SumClassifier, CoherentClassifier.
  - Losses: BCELoss, ASL or MCL.
  - Scheduler can also be None.
  - Optimizer can be 'SGD' or 'Adam'. """
  subjects_file = 'data/openalex/subjects.json'
  mask = create_mask(subjects_file)
  params = {
    "run_id": int(time()),
    "model": CoherentClassifier,
    "subjects_file": subjects_file,
    "docs_folder": 'data/openalex/split_docs',
    "n_words": 250,
    "n_dims": 300,
    "dropout": .7,
    "loss": MCL(mask, 3, 1),
    "batch_size": 10,
    "n_epochs": 60,
    "lr": .4,
    "momentum": .5,
    "optimizer": 'Adam',
    "scheduler": lr_scheduler.OneCycleLR,
    "scheduler_steps": 12000,
    "scheduler_gamma": .9,
    "shuffle": True,
    "hidden_layer": 100,
    "input_linear": 6200,
    "model_state": None,
    "mask": mask
  }
  logging.basicConfig(
    level=logging.INFO,
    filename=f'logs/training_{params["run_id"]}.log'
  )
  init(params)
