import json
from datetime import datetime
from pathlib import Path

import numpy as np
from scrapy import Request

from ..backend import models, utils, database

DB = database.EmbeddingDB(Path("vector.index"), Path("metadata.json"))


class ImagePipeline:
    def process_item(self, item, spider):
        image_data = item.get("image_bytes")
        if image_data is None:
            return item
        img = utils.load_image(image_data)
        emb = models.extract_facenet_embedding(img)
        emb_hash = models.embedding_hash(emb)
        metadata = {
            "source_url": item.get("source_url"),
            "timestamp": datetime.utcnow().isoformat(),
            "embedding_hash": emb_hash,
            "type": "osint",
            "user_id": item.get("user_id", "unknown"),
        }
        DB.add(metadata["user_id"], emb, metadata)
        return item
