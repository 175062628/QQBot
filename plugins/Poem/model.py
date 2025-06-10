import torch
import torch.nn as nn
import numpy as np
import os
import yaml

class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super(LSTMModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, hidden=None):
        embedded = self.embedding(x)
        output, hidden = self.lstm(embedded, hidden)
        output = self.fc(output)
        return output, hidden

class PoemGenerator:
    def __init__(self, model_name):
        self.seq_length = None
        self.hidden_dim = None
        self.embedding_dim = None
        self.vocab_size = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        with open('./plugins/Poem/poetry.txt', 'r', encoding='utf-8') as f:
            self.global_text = f.read()
        self.model_name = model_name
        self.vocab, self.char_to_idx, self.idx_to_char = self.preprocess()

    def preprocess(self):
        text = self.global_text.replace(" ", "")
        vocab = sorted(set(text))
        char_to_idx = {char: idx for idx, char in enumerate(vocab)}
        idx_to_char = {idx: char for idx, char in enumerate(vocab)}
        return vocab, char_to_idx, idx_to_char

    def generate_acrostic(self, keywords):
        if self.model is None:
            self.upload_model()
        # 检查所有关键字是否都在词汇表中
        invalid_keywords = [kw for kw in keywords if kw not in self.char_to_idx]
        if invalid_keywords:
            return False, f"错误: 关键字 '{', '.join(invalid_keywords)}' 不在训练词汇表中"

        poem = ""
        hidden = None
        for i, keyword in enumerate(keywords):
            keyword_idx = self.char_to_idx[keyword]
            input_seq = [keyword_idx]
            if self.device == 'cuda':
                input_tensor = torch.tensor([input_seq], dtype=torch.long).to(self.device)
            else:
                input_tensor = torch.tensor([input_seq], dtype=torch.long)
            for _ in range(self.seq_length - 1):
                output, hidden = self.model(input_tensor, hidden)
                output = output[:, -1, :]
                probs = torch.softmax(output, dim=1).detach().cpu().numpy()[0]  # 仅在需要 numpy 操作时移回 CPU
                next_idx = np.random.choice(len(probs), p=probs)
                input_seq.append(next_idx)
                if self.device == 'cuda':
                    input_tensor = torch.tensor([[next_idx]], dtype=torch.long).to(self.device)  # 移到 GPU
                else:
                    input_tensor = torch.tensor([[next_idx]], dtype=torch.long)
            line = ''.join([self.idx_to_char[idx] for idx in input_seq])
            poem += line + '\n' if i-1 != len(keywords) else ''
        return True, poem

    def upload_model(self):
        with open(f'{self.model_name}/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        self.vocab_size = config['vocab_size']
        self.embedding_dim = config['embedding_dim']
        self.hidden_dim = config['hidden_dim']
        self.seq_length = config['seq_length']

        self.model = LSTMModel(self.vocab_size, self.embedding_dim, self.hidden_dim)
        if self.device == 'cuda':
            self.model = self.model.to(self.device)

        model_path = f'{self.model_name}/acrostic_model.pth'
        try:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
        except FileNotFoundError:
            print(f"未找到模型文件 {model_path}，请检查文件路径。")
        except Exception as e:
            print(f"加载模型时出现错误：{e}")