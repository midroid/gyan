from datasets import load_dataset

dataset = load_dataset("davanstrien/ufo-ColPali", split="train")


print(dataset)
print(len(dataset))
dataset_length = len(dataset)
n = 50
# dataset subset with 1/{n}th of the data
dataset = dataset.select(range(0, dataset_length, n))

sample_image = dataset[0]["image"]

def get_result_ds(row_ids):
    return dataset.select(row_ids)


def get_dataset(n):
    dataset = load_dataset("davanstrien/ufo-ColPali", split="train")
    dataset_length = len(dataset)
    dataset = dataset.select(range(0, dataset_length, n))
    return dataset