import torch
import numpy as np
from torch.autograd import Variable
from base.base_trainer import BaseTrainer


class Trainer(BaseTrainer):
    def __init__(self, model, loss, metrics, data_loader, optimizer, epochs,
                 save_dir, save_freq, resume, with_cuda, verbosity, identifier='',
                 valid_data_loader=None, logger=None, save_grad=False):
        super(Trainer, self).__init__(model, loss, metrics, optimizer, epochs,
                                      save_dir, save_freq, resume, verbosity, identifier, logger)
        self.batch_size = data_loader.batch_size
        self.data_loader = data_loader
        self.valid_data_loader = valid_data_loader
        self.valid = True if self.valid_data_loader is not None else False
        self.with_cuda = with_cuda
        self.save_grad = save_grad

    def _train_epoch(self, epoch):
        self.model.train()
        if self.with_cuda:
            self.model.cuda()

        total_loss = 0
        total_metrics = np.zeros(len(self.metrics))
        for batch_idx, (data, target) in enumerate(self.data_loader):
            target_dtype = str(target.dtype)
            data = torch.FloatTensor(data)
            target = torch.FloatTensor(target) if target_dtype[0] == 'f' else torch.LongTensor(target)
            data, target = Variable(data), Variable(target)
            if self.with_cuda:
                data, target = data.cuda(), target.cuda()

            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.loss(output, target)
            loss.backward()
            self.optimizer.step()
            for i, metric in enumerate(self.metrics):
                y_output = output.data.cpu().numpy()
                y_output = np.argmax(y_output, axis=1)
                y_target = target.data.cpu().numpy()
                total_metrics[i] += metric(y_output, y_target)

            total_loss += loss.data[0]
            log_step = int(np.sqrt(self.batch_size))
            if self.verbosity >= 2 and batch_idx % log_step == 0:
                print('Train Epoch: {} [{}/{} ({:.0f}%)] Loss: {:.6f}'.format(
                    epoch, batch_idx * len(data), len(self.data_loader) * len(data),
                    100.0 * batch_idx / len(self.data_loader), loss.data[0]))

        avg_loss = total_loss / len(self.data_loader)
        avg_metrics = (total_metrics / len(self.data_loader)).tolist()
        log = {'loss': avg_loss, 'metrics': avg_metrics}

        if self.save_grad:
            grad_all = 0.0
            for p in self.model.parameters():
                grad = 0.0
                if p.grad is not None:
                    grad = (p.grad.cpu().data.numpy() ** 2).sum()
                grad_all += grad
            grad_norm = grad_all ** 0.5
            log = {**log, 'grad_norm': grad_norm}

        if self.valid:
            val_log = self._valid_epoch()
            log = {**log, **val_log}

        return log

    def _valid_epoch(self):
        self.model.eval()
        total_val_loss = 0
        total_val_metrics = np.zeros(len(self.metrics))
        for batch_idx, (data, target) in enumerate(self.valid_data_loader):
            target_dtype = str(target.dtype)
            data = torch.FloatTensor(data)
            target = torch.FloatTensor(target) if target_dtype[0] == 'f' else torch.LongTensor(target)
            data, target = Variable(data), Variable(target)
            if self.with_cuda:
                data, target = data.cuda(), target.cuda()

            output = self.model(data)
            loss = self.loss(output, target)
            total_val_loss += loss.data[0]

            for i, metric in enumerate(self.metrics):
                y_output = output.data.cpu().numpy()
                y_output = np.argmax(y_output, axis=1)
                y_target = target.data.cpu().numpy()
                total_val_metrics[i] += metric(y_output, y_target)

        avg_val_loss = total_val_loss / len(self.valid_data_loader)
        avg_val_metrics = (total_val_metrics / len(self.valid_data_loader)).tolist()
        return {'val_loss': avg_val_loss, 'val_metrics': avg_val_metrics}
