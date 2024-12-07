from pydantic import BaseModel
import pandas as pd

CUSTOM_DATASET_FILE = 'custom_dataset.json'

class CustomDataset(BaseModel):
    id: str
    file_name: str
    file_location: str
    uuid4: str
    image: str
    page_number: int



def create_custom_dataset():
   # Get the field names from CustomDataset class
    fields = list(CustomDataset.__annotations__.keys())

    # Create an empty DataFrame with specified columns
    df = pd.DataFrame(columns=fields)

    # Set 'id' as the index
    df.set_index('id', inplace=True)

    df.to_json(CUSTOM_DATASET_FILE)
    return df



def get_custom_dataset():
    # Read the JSON file
    try:
        custom_dataset_df = pd.read_json(CUSTOM_DATASET_FILE)
    except FileNotFoundError:
        # If the file does not exist, create and return an empty DataFrame
        custom_dataset_df = create_custom_dataset()

    return custom_dataset_df