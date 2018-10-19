#  File for playing with pytorch and fastai libraries

import torch

from torch import nn

from fastai.core import T, F, V

n_factors = 4

class EmbeddingDot(nn.Module):
    def __init__(self, n_users, n_movies, p1=0.5, p2=0.5, nh=10):
        super().__init__()
        self.u = nn.Embedding(n_users, n_factors)
        self.m = nn.Embedding(n_movies, n_factors)
        self.ub = nn.Embedding(n_users, 1)
        self.mb = nn.Embedding(n_movies, 1)
        self.u.weight.data.uniform_(0, 0.05)
        self.m.weight.data.uniform_(0, 0.05)
        self.ub.weight.data.uniform_(0, 0.05)
        self.mb.weight.data.uniform_(0, 0.05)
        self.lin1 = nn.Linear(n_factors * 2, nh)
        self.lin2 = nn.Linear(nh, 1)
        self.dropout1 = nn.Dropout(p1)
        self.dropout2 = nn.Dropout(p2)


    def forward(self, cats, conts):
        users, movies = cats[:, 0], cats[:, 1]
        u, m = self.u(users), self.m(movies)
        x = self.dropout1(torch.cat([u, m], dim=1))
        x = self.dropout2(F.relu(self.lin1(x)))
        return F.sigmoid(self.lin2(x)) * 4 + 1


class MyRnn(nn.Module):
    def __init__(self, es, hl, n_classes):
        super().__init__()
        self.hl = hl
        self.embeddings = nn.Embedding(n_classes, es)
        self.rnn = nn.RNN(es, hl)
        self.linear = nn.Linear(hl, n_classes)

    def forward(self, *input):
        bs = input[0].size(0)
        hiddens = V(torch.zeros(1, bs, self.hl))
        x = self.embeddings(V(torch.stack(input)))
        outputs, hiddens = self.rnn(x, hiddens)
        return F.softmax(self.linear(outputs), -1)


if __name__ == '__main__':
    b = T([[1, 1],
           [0, 0]])

    dot = EmbeddingDot(2, 3)
    print(dot.forward(b, []))

    # print(dot.model)
    # print([a for a in dot.parameters()])
    #
    # print(dot.forward(b, []))
    # print([a for a in dot.parameters()])

    rnn = MyRnn(3, 10, 4)
    rnn.forward(T([1, 2]), T([0, 0]))
