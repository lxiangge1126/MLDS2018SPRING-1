import numpy as np
from gensim.models.word2vec import Word2Vec
from gensim.models.keyedvectors import KeyedVectors


class BaseEmbedder:
    def __init__(self, corpus, config):
        self.config = config
        self.word_list = ['<PAD>', '<BOS>', '<EOS>', '<UNK>']
        self.dictionary = dict((word, i) for i, word in enumerate(self.word_list))
        self.frequency = dict()

    def encode_word(self, word):
        return NotImplementedError

    def encode_line(self, line):
        return NotImplementedError

    def encode_lines(self, lines):
        return NotImplementedError

    def decode_word(self, word):
        return NotImplementedError

    def decode_line(self, line):
        return NotImplementedError

    def decode_lines(self, lines):
        return NotImplementedError

    def dec_out2dec_in(self, dec_out):
        return NotImplementedError


class Word2VecEmbedder(BaseEmbedder):
    def __init__(self, corpus, config):
        super(Word2VecEmbedder, self).__init__(corpus, config)
        self.config = config

        self.emb_size = 300
        self.corpus = []
        for line in corpus:
            line = line.replace('.', '').split()
            line = [word.lower() for word in line]
            line = ['<BOS>'] + line
            self.corpus.append(line)
            for word in line:
                if word not in self.frequency:
                    self.frequency[word] = 1
                else:
                    self.frequency[word] += 1
        min_count = config['embedder']['min_count']
        max_len = 0
        for i, line in enumerate(self.corpus):
            max_len = max(len(line), max_len)
            for j, word in enumerate(line):
                if self.frequency[word] < min_count:
                    self.corpus[i][j] = '<UNK>'
        for i, line in enumerate(self.corpus):
            self.corpus[i].append('<EOS>')
            self.corpus[i].extend(['<PAD>'] * (max_len-len(self.corpus[i])))

        # self.word2vec = Word2Vec(self.corpus, size=self.emb_size, min_count=min_count, iter=30, workers=16)
        self.word2vec = KeyedVectors.load_word2vec_format('datasets/GoogleNews-vectors-negative300-SLIM.bin',
                                                          binary=True)
        # print(self.word2vec.wv.most_similar(positive=['UNK'], restrict_vocab=4096))

    def encode_word(self, word):
        if word in self.word2vec.wv:
            return self.word2vec.wv[word]
        elif word.title() in self.word2vec:
            return self.word2vec.wv[word.title()]
        else:
            return self.word2vec.wv['UNK']

    def encode_line(self, line):
        encoded = []
        for word in line:
            encoded.append(self.encode_word(word))
        return encoded

    def encode_lines(self, lines):
        encoded = []
        for line in lines:
            line = line.replace('.', '').split()
            line = [word.lower() for word in line]
            encoded.append(np.array(self.encode_line(line)))
        return encoded

    def decode_word(self, word):
        # return self.word2vec.wv.most_similar(positive=[word], topn=1)[0][0]
        sim = self.word2vec.wv.most_similar(positive=[word], topn=32, restrict_vocab=4096)
        for i in range(32):
            if sim[i][0] in self.frequency.keys() or sim[i][0].title() in self.frequency.keys():
                return sim[i][0]
        return '<UNK>'

    def decode_line(self, line):
        return [self.decode_word(vec) for vec in line]

    def decode_lines(self, lines):
        decoded = []
        for line in lines:
            line = self.decode_line(line)
            line = ' '.join(line)
            line = line.split('<EOS>', 1)[0]
            line = line.split('<PAD>', 1)[0]
            line = line.split()
            if len(line) == 0:
                line = ['a']
            line = ' '.join(line)
            decoded.append(line)
        return decoded

    def dec_out2dec_in(self, dec_out):
        dec_in = []
        dec_out_batch = dec_out.cpu().data.numpy()[0]
        for i, dec_out in enumerate(dec_out_batch):
            dec_in.append(self.encode_word(self.decode_word(dec_out)))
        return np.array([dec_in])


class OneHotEmbedder(BaseEmbedder):
    def __init__(self, corpus, config):
        super(OneHotEmbedder, self).__init__(corpus, config)
        self.config = config
        for line in corpus:
            line = line.replace('.', '').split()
            line = [word.lower() for word in line]
            for word in line:
                if word not in self.frequency:
                    self.frequency[word] = 1
                else:
                    self.frequency[word] += 1
        min_count = config['embedder']['min_count']
        for word, _ in self.frequency.items():
            if self.frequency[word] >= min_count:
                self.dictionary[word] = len(self.dictionary)
                self.word_list.append(word)
        self.emb_size = len(self.dictionary)

    def encode_word(self, word):
        return self.__onehot(self.emb_size, self.dictionary[word])

    def encode_line(self, line):
        line = [self.__onehot(self.emb_size,
                              self.dictionary.get(word, self.dictionary['<UNK>'])) for word in line]
        return line

    def encode_lines(self, lines):
        encoded = []
        for line in lines:
            line = line.replace('.', '').split()
            line = [word.lower() for word in line]
            line = self.encode_line(line)
            encoded.append(np.array(line))
        return encoded

    def decode_word(self, word):
        return self.word_list[int(np.argmax(word, 0))]

    def decode_line(self, line):
        return [self.decode_word(vec) for vec in line]

    def decode_lines(self, lines):
        decoded = []
        for line in lines:
            line = self.decode_line(line)
            line = list(filter(lambda x: x != '<EOS>' and x != '<PAD>', line))
            line = ' '.join(line)
            #line = line.split('<EOS>', 1)[0]
            #line = line.split('<PAD>', 1)[0]
            line = line.split()
            if len(line) == 0:
                line = ['a']
            line = ' '.join(line)
            decoded.append(line)
        return decoded

    def dec_out2dec_in(self, dec_out):
        dec_in = []
        dec_out_batch = dec_out.cpu().data.numpy()[0]
        dec_out_batch = np.argmax(dec_out_batch, 1)
        for dec_out in dec_out_batch:
            dec_in.append(self.__onehot(self.emb_size, dec_out))
        return np.array([dec_in])

    def __onehot(self, dim, label):
        v = np.zeros((dim,))
        v[label] = 1
        return v


class ChineseOneHotEmbedder(BaseEmbedder):
    def __init__(self, corpus, vocab_path, config):
        super(ChineseOneHotEmbedder, self).__init__(corpus, config)
        self.config = config
        self.word_list = dict()
        with open(vocab_path) as f:
            emb_size = 2048
            for i, line in enumerate(f):
                if i == emb_size:
                    break
                index, word = line.split()
                index = int(index)
                self.dictionary[word] = index
                self.word_list[index] = word
        self.emb_size = len(self.dictionary)
        config['model']['input_size'] = self.emb_size

    def encode_word(self, word):
        return self.__onehot(self.emb_size, self.dictionary[word])

    def encode_line(self, line):
        line = [self.__onehot(self.emb_size,
                              self.dictionary.get(word, self.dictionary['<UNK>'])) for word in line]
        return line

    def encode_lines(self, lines):
        lines = [[word for word in line] for line in lines]
        enc = []
        for line in lines:
            enc.append(np.array(self.encode_line(line)))
        return enc

    def decode_word(self, word):
        return self.word_list[int(np.argmax(word, 0))]

    def decode_line(self, line):
        return [self.decode_word(vec) for vec in line]

    def decode_lines(self, lines):
        decoded = []
        for line in lines:
            line = self.decode_line(line)
            line = ''.join(line)
            line = line.split('<EOS>', 1)[0]
            line = line.split('<PAD>', 1)[0]
            line = line.split()
            if len(line) == 0:
                line = ['。']
            line = ''.join(line)
            decoded.append(line)
        return decoded

    def dec_out2dec_in(self, dec_out):
        dec_in = []
        dec_out_batch = dec_out.cpu().data.numpy()[0]
        dec_out_batch = np.argmax(dec_out_batch, 1)
        for dec_out in dec_out_batch:
            dec_in.append(self.__onehot(self.emb_size, dec_out))
        return np.array([dec_in])

    def __onehot(self, dim, label):
        v = np.zeros((dim,))
        v[label] = 1
        return v
