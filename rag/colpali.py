import torch
from PIL import Image

from colpali_engine.models import ColQwen2, ColQwen2Processor
from rag.data_set import get_result_ds
from rag.vdb_qdrant import sample_embedding

# model_name = "vidore/colqwen2-v1.0"

# # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# device = "mps"

# model = ColQwen2.from_pretrained(
#     model_name,
#     torch_dtype=torch.bfloat16,
#     device_map=device,
# ).eval()

# processor = ColQwen2Processor.from_pretrained(model_name)

# Your inputs
# images = [
#     Image.new("RGB", (32, 32), color="white"),
#     Image.new("RGB", (16, 16), color="black"),
# ]
# queries = [
#     "Is attention really all you need?",
#     "Are Benjamin, Antoine, Merve, and Jo best friends?",
# ]

# # Process the inputs
# batch_images = processor.process_images(images).to(model.device)
# batch_queries = processor.process_queries(queries).to(model.device)

# # Forward pass
# with torch.no_grad():
#     image_embeddings = model(**batch_images)
#     query_embeddings = model(**batch_queries)

# scores = processor.score_multi_vector(query_embeddings, image_embeddings)


# def search_rag(query: str) -> str:
#     print(scores)
#     print(scores.shape)
#     print(sample_embedding)
#     print(sample_embedding.shape)
#     return "Hello World"


from rag.model import colpali_model, colpali_processor
from rag.vdb_qdrant import qdrant_client, collection_name


# Perform a search
def search_images_by_text(query_text, top_k=5):
    # Process and encode the text query
    with torch.no_grad():
        batch_query = colpali_processor.process_queries([query_text]).to(
            colpali_model.device
        )
        query_embedding = colpali_model(**batch_query)

    # Convert the query embedding to a list of vectors
    multivector_query = query_embedding[0].cpu().float().numpy().tolist()
    print(f"Multivector Query: {multivector_query}")
    # Search in Qdrant
    search_result = qdrant_client.query_points(
        collection_name=collection_name, query=multivector_query, limit=top_k
    )
    print(f"Search Result: {search_result}")
    return search_result


# Example usage
# query_text = "declassified data"
# results = search_images_by_text(query_text)

# for result in results.points:
#     print(result)

# Search by text and return images
def search_by_text_and_return_images(query_text):
    top_k=5
    results = search_images_by_text(query_text, top_k)
    row_ids = [r.id for r in results.points]
    return row_ids

# Example usage
# row_ids = search_by_text_and_return_images("top secret")
# results_ds = get_result_ds(row_ids)


# def display(image):
#     # convert to pil image and show
#     pil_image = Image.fromarray(image)
#     pil_image.show()

# for row in results_ds:
#     # display image
#     display(row["image"])

# def process_single_file_upload(file_name, file_bytes):
#     # file_name = file.filename
#     print(f"file_name: {file_name}")
#     print(type(file_bytes))
#     file_id = uuid4()
#     conversion_result = convert_pdf_to_images(file_bytes, file_id)
#     print(f"Conversion Result: {conversion_result}")
#     return {
#         "filename": file_name,
#         "file_id": file_id,
#         "image_count": conversion_result["image_count"],
#     }
    # return {"result": True}