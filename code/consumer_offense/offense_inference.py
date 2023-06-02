import torch
import numpy as np
from transformers import BertForSequenceClassification as bfsc
from transformers import BertTokenizer


def load_model(model_path):
    model = bfsc.from_pretrained('bert-base-uncased', num_labels=2)         #, from_tf=True
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Load the checkpoint and set the model's state dictionary
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['state_dict'])

    return model


def predict(model, text):
    # Load tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

    # Tokenize input text
    inputs = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        return_attention_mask=True,
        return_token_type_ids=True,
        padding='max_length',
        max_length=64,
        truncation=True
    )

    # Convert inputs to PyTorch tensors
    input_ids = torch.tensor(inputs['input_ids']).unsqueeze(0)
    attention_mask = torch.tensor(inputs['attention_mask']).unsqueeze(0)
    token_type_ids = torch.tensor(inputs['token_type_ids']).unsqueeze(0)

    # Move tensors to device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)
    token_type_ids = token_type_ids.to(device)

    # Perform inference
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        logits = outputs[0]
        predictions = np.argmax(logits.detach().cpu().numpy(), axis=1)

    return predictions[0]