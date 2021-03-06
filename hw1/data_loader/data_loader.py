import torch
import numpy as np
from torchvision import datasets, transforms
from base.base_data_loader import BaseDataLoader
import random
random.seed(1)
import matplotlib.pyplot as plt

class MnistLoader(BaseDataLoader):
    def __init__(self, batch_size, rand_label=False, noise=False):
        super(MnistLoader, self).__init__(batch_size)
        self.data_loader = torch.utils.data.DataLoader(
            datasets.MNIST('../data', train=True, download=True,
                           transform=transforms.Compose([
                               transforms.ToTensor(),
                               transforms.Normalize((0.1307,), (0.3081,))
                           ])), batch_size=256, shuffle=False)
        self.x = []
        self.y = []
        for data, target in self.data_loader:
            self.x += [i for i in data.numpy()]
            self.y += [i for i in target.numpy()]
        self.x = np.array(self.x)
        self.y = np.array(self.y)
        if rand_label:
            np.random.shuffle(self.y)
        if noise:
            mean, deviation = 0.0, 0.2 
            noise = np.random.normal(mean,deviation,self.x.shape)
            self.x = self.x + noise

        self.n_batch = len(self.x) // self.batch_size
        self.batch_idx = 0

    def __iter__(self):
        self.n_batch = len(self.x) // self.batch_size
        self.batch_idx = 0
        assert self.n_batch > 0
        return self

    def __next__(self):
        if self.batch_idx < self.n_batch:
            x_batch = self.x[self.batch_idx * self.batch_size:(self.batch_idx + 1) * self.batch_size]
            y_batch = self.y[self.batch_idx * self.batch_size:(self.batch_idx + 1) * self.batch_size]
            self.batch_idx = self.batch_idx + 1
            return x_batch, y_batch
        else:
            raise StopIteration

    def __len__(self):
        self.n_batch = len(self.x) // self.batch_size
        return self.n_batch


class CifarLoader(BaseDataLoader):
    def __init__(self, batch_size, rand_label=False, noise=False):
        super(CifarLoader, self).__init__(batch_size)
        self.data_loader = torch.utils.data.DataLoader(
            datasets.CIFAR10('../data', train=True, download=True,
                             transform=transforms.Compose([
                                transforms.ToTensor(),
                                transforms.Normalize((0.4914, 0.4822, 0.4465),
                                                     (0.2470, 0.2430, 0.2610))
                             ])), batch_size=256, shuffle=False)
        self.x = []
        self.y = []
        for data, target in self.data_loader:
            self.x += [i for i in data.numpy()]
            self.y += [i for i in target.numpy()]
        self.x = np.array(self.x)
        self.y = np.array(self.y)
        if rand_label:
            np.random.shuffle(self.y)
        if noise:
            mean, deviation = 0.0, 0.2 
            noise = np.random.normal(mean,deviation,self.x.shape)
            self.x = self.x + noise
        self.n_batch = len(self.x) // self.batch_size
        self.batch_idx = 0

    def __iter__(self):
        self.n_batch = len(self.x) // self.batch_size
        self.batch_idx = 0
        assert self.n_batch > 0
        return self

    def __next__(self):
        if self.batch_idx < self.n_batch:
            x_batch = self.x[self.batch_idx * self.batch_size:(self.batch_idx + 1) * self.batch_size]
            y_batch = self.y[self.batch_idx * self.batch_size:(self.batch_idx + 1) * self.batch_size]
            self.batch_idx = self.batch_idx + 1
            return x_batch, y_batch
        else:
            raise StopIteration

    def __len__(self):
        self.n_batch = len(self.x) // self.batch_size
        return self.n_batch
