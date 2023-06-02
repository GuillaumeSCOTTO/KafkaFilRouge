
from transformers import BertForSequenceClassification as bfsc
from transformers import BertTokenizer
import torch


# Build the Sentiment Classifier class 
class SentimentClassifier(torch.nn.Module):
    
    # Constructor class 
    def __init__(self, n_classes):
        super(SentimentClassifier, self).__init__()
        self.bert = BertModel.from_pretrained('bert-base-cased')
        self.drop = nn.Dropout(p=0.3)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)
    
    # Forward propagaion class
    def forward(self, input_ids, attention_mask, return_dict=False):
        _, pooled_output = self.bert(
          input_ids=input_ids,
          attention_mask=attention_mask, 
          return_dict = return_dict
        )
        #  Add a dropout layer 
        output = self.drop(pooled_output)
        return self.out(output)


def load_model(model_path, verbose=True):

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Load the checkpoint and set the model's state dictionary
    model = torch.load(model_path, map_location=device)
    model.to(device)

    if verbose:
        print("Ternary sentiment model has been loaded correctly")

    return model

def predict(model, text):
    # Prepare the input text
    tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    encoded_review = tokenizer.encode_plus(text, max_length=160, add_special_tokens=True, return_token_type_ids=False, pad_to_max_length=True, return_attention_mask=True, truncation=True, return_tensors='pt', )

    input_ids = encoded_review['input_ids'].to(device)
    attention_mask = encoded_review['attention_mask'].to(device)

    with torch.no_grad():
        output = model(input_ids, attention_mask)
        _, prediction = torch.max(output, dim=1)

    return prediction.item()
