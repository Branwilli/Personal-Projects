import torch
import torch.nn as nn

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class PredictionModel(nn.Module):

    def __init__(self, input_size):
        super().__init__()
        self.lstm = nn.LSTM(input_size, 128, num_layers=2, batch_first=True, dropout=0.3)
        self.opportunity_head = nn.Linear(128, 1)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.direction_head = nn.Linear(128, 1)
        #self.sigmod = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.relu(out)
        out = self.dropout(out)
        opp = self.opportunity_head(out)
        direction = self.direction_head(out)
        return opp, direction
