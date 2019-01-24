from fastai.text import *

logger = logging.getLogger(__name__)


class EarlyStopping(Callback):
    def __init__(self, learner: RNN_Learner, save_path: str,
                 best_loss_path: str, best_acc_path: str,
                 best_epoch_path: str,
                 enc_path: str = None, patience: int = 5):
        super().__init__()
        self.learner = learner
        self.save_path = save_path
        self.best_loss_path = best_loss_path
        self.best_acc_path = best_acc_path
        self.best_epoch_path = best_epoch_path
        self.enc_path = enc_path
        self.patience = patience

    def on_train_begin(self):
        self.best_val_loss = float("inf")
        self.num_epochs_no_improvement = 0
        self.epoch_finished = -1

    def on_epoch_end(self, metrics):
        self.epoch_finished += 1
        val_loss = metrics[0]
        acc = metrics[1]  # TODO be careful here, normally it's accuracy but not necessary,
        # if not there will be some other metric written to acc.best file
        if val_loss < self.best_val_loss:
            self.best_val_loss = val_loss
            self.num_epochs_no_improvement = 0
            self.learner.save(self.save_path)
            if self.enc_path is not None:
                self.learner.save_encoder(self.enc_path)
            with open(os.path.join(self.learner.models_path, self.best_loss_path), 'w') as f:
                f.write(f'{val_loss[0]:.4f}')
            with open(os.path.join(self.learner.models_path, self.best_acc_path), 'w') as f:
                f.write(f'{acc:.4f}')
            with open(os.path.join(self.learner.models_path, self.best_epoch_path), 'w') as f:
                f.write(f'{self.epoch_finished}')
        else:
            self.num_epochs_no_improvement += 1
        if self.num_epochs_no_improvement > self.patience:
            logger.warning(f'Stopping - no improvement after {self.patience+1} epochs')
            return True

    def on_train_end(self):
        logger.info(f'Loading best model from {self.save_path}, loss: {self.best_val_loss[0]:.4f}')
        self.learner.load(self.save_path)
