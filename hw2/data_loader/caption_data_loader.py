import os
import json
import random
from copy import copy
import numpy as np
from base.base_data_loader import BaseDataLoader
from utils.preprocess import OneHot

# TODO: (Optional) Word embedding by changing self.embedder
# FIXME: Train only by the first label?
# DONE: Output sequence padding
# DONE: One-hot encoding
# DONE: Tokens (<PAD>, <BOS>, <EOS>, <UNK>, ...)


class CaptionDataLoader(BaseDataLoader):
    """ Format:
        :returns: in_seq, out_seq, formatted

        in_seq:     batch size * 80 * 4096
        out_seq:    batch size * max length * embedder dict size
            padded per batch in __next__()
        formatted:
            [{'caption': ['...', '...'], 'id': '...'}, ...]
    """
    def __init__(self, data_dir, batch_size, shuffle=True):
        super(CaptionDataLoader, self).__init__(batch_size)
        self.__parse_dataset(os.path.join(data_dir, 'MLDS_hw2_1_data'))
        self.n_batch = len(self.in_seq) // self.batch_size
        self.batch_idx = 0
        self.shuffle = shuffle

    def __parse_dataset(self, base):
        self.video_ids = []
        self.corpus = []
        self.in_seq = []
        self.out_seq = []
        self.formatted = []
        features = load_features(os.path.join(base, 'training_data/feat'))
        labels = load_labels(os.path.join(base, 'training_label.json'))
        for video_id, feature in features.items():
            self.video_ids.append(video_id)
            self.in_seq.append(feature)
            # self.out_seq.append(labels[video_id][0])
            self.out_seq.append(labels[video_id])
            self.corpus.extend(labels[video_id])
            self.formatted.append({'caption': labels[video_id], 'id': video_id})
        self.embedder = OneHot(self.corpus)
        # self.out_seq = self.embedder.encode_lines(self.out_seq)
        self.out_seq = [self.embedder.encode_lines(seq) for seq in self.out_seq]

    def __iter__(self):
        self.n_batch = len(self.in_seq) // self.batch_size
        self.batch_idx = 0
        assert self.n_batch > 0
        if self.shuffle:
            self.__shuffle_data()
        return self

    def __next__(self):
        if self.batch_idx < self.n_batch:
            in_seq_batch = self.in_seq[self.batch_idx * self.batch_size:
                                       (self.batch_idx + 1) * self.batch_size]
            out_seq_batch = self.out_seq[self.batch_idx * self.batch_size:
                                         (self.batch_idx + 1) * self.batch_size]
            formatted_batch = self.formatted[self.batch_idx * self.batch_size:
                                             (self.batch_idx + 1) * self.batch_size]
            # out_seq_batch = [random.choice(seq) for seq in out_seq_batch]
            out_seq_batch = [seq[0] for seq in out_seq_batch]
            out_seq_batch = pad_batch(out_seq_batch,
                                      self.embedder.encode_word('<PAD>'),
                                      self.embedder.encode_word('<EOS>'))
            self.batch_idx = self.batch_idx + 1
            return np.array(in_seq_batch), np.array(out_seq_batch), formatted_batch
        else:
            raise StopIteration

    def __len__(self):
        """
        :return: Total batch number
        """
        self.n_batch = len(self.in_seq) // self.batch_size
        return self.n_batch

    def __shuffle_data(self):
        rand_idx = np.random.permutation(len(self.in_seq))
        self.in_seq = [self.in_seq[i] for i in rand_idx]
        self.out_seq = [self.out_seq[i] for i in rand_idx]
        self.formatted = [self.formatted[i] for i in rand_idx]

    # Pack/unpack for validation split
    def split_validation(self, validation_split, shuffle=True):
        valid_data_loader = copy(self)
        if shuffle:
            self.__shuffle_data()
        split = int(len(self.in_seq) * validation_split)
        valid_data_loader.in_seq = self.in_seq[:split]
        valid_data_loader.out_seq = self.out_seq[:split]
        valid_data_loader.formatted = self.formatted[:split]
        self.in_seq = self.in_seq[split:]
        self.out_seq = self.out_seq[split:]
        self.formatted = self.formatted[split:]
        return valid_data_loader


def load_features(path):
    features = {}
    filenames = os.listdir(path)
    for file in filenames:
        video_id, _ = os.path.splitext(file)
        feature = np.load(os.path.join(path, file))
        features[video_id] = feature
    return features


def load_labels(path):
    labels = {}
    raw_labels = json.load(open(path))
    for entry in raw_labels:
        labels[entry['id']] = entry['caption']
    return labels


def pad_batch(batch, pad_val, eos_val):
    maxlen = 0
    eos_val = eos_val.reshape((1, -1))
    for item in batch:
        maxlen = max(maxlen, len(item))
    for i, seq in enumerate(batch):
        seq = np.append(seq, eos_val, axis=0)
        if maxlen+1 != len(seq):
            batch[i] = np.append(seq, [pad_val for _ in range(maxlen-len(seq)+1)], axis=0)
        else:
            batch[i] = seq
    return batch


if __name__ == '__main__':
    # labels = load_labels('../datasets/MLDS_hw2_1_data/training_label.json')
    # for k, v in labels.items():
    #     print(k, v, end='\n\n')

    # features = load_features('../datasets/MLDS_hw2_1_data/training_data/feat')
    # for k, v in features.items():
    #     print(k, v, end='\n\n')

    data_loader = CaptionDataLoader('../datasets', 4)
    for isb, osb, fb in data_loader:
        print(isb.shape)
        print(osb.shape)
        print(fb)
        input()
