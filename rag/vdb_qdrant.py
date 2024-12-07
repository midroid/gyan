import os

import numpy as np
# from IPython.display import display
from PIL import Image

import torch

from qdrant_client import QdrantClient
from qdrant_client.http import models
from tqdm import tqdm
from rich import print as r_print

from rag.model import colpali_model, colpali_processor

from rag.data_set import get_dataset, sample_image


qdrant_client = QdrantClient(
    # ":memory:"
    "http://localhost:6333"
)  # Use ":memory:" for in-memory database or "path/to/db" for persistent storage



sample_embedding = None
with torch.no_grad():
    sample_batch = colpali_processor.process_images([sample_image]).to(
        colpali_model.device
    )
    sample_embedding = colpali_model(**sample_batch)

print(sample_embedding)
print(sample_embedding.shape)

collection_name = "ufo"

vector_size = sample_embedding.shape[-1]

# scalar_quant = models.ScalarQuantizationConfig(
#     type=models.ScalarType.INT8,
#     quantile=0.99,
#     always_ram=False,
# )

# vector_params = models.VectorParams(
#     size=vector_size,
#     distance=models.Distance.COSINE,
#     multivector_config=models.MultiVectorConfig(
#         comparator=models.MultiVectorComparator.MAX_SIM
#     ),
#     quantization_config=scalar_quant
# )

# print(vector_params)

def recreate_qdrant_collection():
    qdrant_client.recreate_collection(
        collection_name=collection_name,  # the name of the collection
        on_disk_payload=True,  # store the payload on disk
        optimizers_config=models.OptimizersConfigDiff(
            indexing_threshold=10
        ),  # it can be useful to swith this off when doing a bulk upload and then manually trigger the indexing once the upload is done
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
            multivector_config=models.MultiVectorConfig(
                comparator=models.MultiVectorComparator.MAX_SIM
            ),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True,
                ),
            ),
        ),
    )

    print("Collection created")
    print(qdrant_client)
    return qdrant_client

# import stamina

# @stamina.retry(on=Exception, attempts=1)
def upsert_to_qdrant(points):
    print(f"Upserting {len(points)} points")
    print(points[0])
    try:
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points,
            wait=False,
        )
    except Exception as e:
        print(f"Error during upsert: {e}")
        return False
    return True


batch_size = 4  # Adjust based on your GPU memory constraints


def index_data_batch(dataset, batch_size: int):

    # Use tqdm to create a progress bar
    with tqdm(total=len(dataset), desc="Indexing Progress") as pbar:
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]

            # The images are already PIL Image objects, so we can use them directly
            images = batch["image"]

            # Process and encode images
            with torch.no_grad():
                batch_images = colpali_processor.process_images(images).to(
                    colpali_model.device
                )
                image_embeddings = colpali_model(**batch_images)

            # Prepare points for Qdrant
            points = []
            for j, embedding in enumerate(image_embeddings):
                # Convert the embedding to a list of vectors
                multivector = embedding.cpu().float().numpy().tolist()
                points.append(
                    models.PointStruct(
                        id=i + j,  # we just use the index as the ID
                        vector=multivector,  # This is now a list of vectors
                        payload={
                            "source": "internet archive"
                        },  # can also add other metadata/data
                    )
                )
            # Upload points to Qdrant
            try:
                print(f"Upserting {len(points)} points")
                print(points[0])
                upsert_to_qdrant(points)
            except Exception as e:
                print(f"Error during upsert: {e}")
                continue

            # Update the progress bar
            pbar.update(batch_size)

    print("Indexing complete!")


def create_test_collection():
    recreate_qdrant_collection()
    # index_data_batch(dataset, batch_size)

def upload_index_test_data():
    # dataset subset with 1/{n}th of the data
    dataset = get_dataset(50)
    index_data_batch(dataset, batch_size)
    return True

def get_qdrant_collection():
    collection = qdrant_client.get_collection(collection_name)
    r_print(collection)
    return collection


def get_collection_items(limit=10):
    return qdrant_client.scroll(collection_name=collection_name, limit=limit)


