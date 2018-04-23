import numpy as np
from preprocess.embedding import OneHotEmbedder


def beam_search(out_seq, n):
    """
        out_seq:
            type:  Variable
            shape: batch size x max sequence length in batch x emb size
    """

    max_prob_idx = np.argsort(-out_seq[0], axis=1)[::, :n]
    possible_prob = out_seq[0][0][max_prob_idx[0]]
    possible_idx = [(idx,) for idx in max_prob_idx[0]]

    for k, word_prob_idx in enumerate(max_prob_idx):
        if k == 0:
            continue
        word_prob = (out_seq[0][k][word_prob_idx])
        possible_prob = [i * w for i in possible_prob for w in word_prob]
        possible_idx = [i+(j,) for i in possible_idx for j in max_prob_idx[k]]
        sorted_idx = sorted(range(len(possible_prob)), key=lambda l: possible_prob[l], reverse=True)
        possible_prob = [possible_prob[idx] for idx in sorted_idx[:n]]
        possible_idx = [possible_idx[idx] for idx in sorted_idx[:n]]

    """
        possible_idx:
            type: tuple in list [(seq),(seq)]
    """
    return possible_idx