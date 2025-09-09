AnimeGAN2 TF.js Model Placeholder

This folder is reserved for a TensorFlow.js GraphModel (model.json + weight shards) compatible with AnimeGAN2 or CartoonGAN.

How to add:
- Export a TF.js GraphModel and place files here: model.json and group1-shard*.bin
- The Dual Rig viewer references default path: /static/models/animegan2/model.json

During dev you can copy a model here and it will be served under /static/models/animegan2/ thanks to FastAPI StaticFiles.

Example sources:
- https://github.com/TencentARC/GFPGAN (for facial enhancement; not TF.js by default)
- Community TF.js ports of AnimeGAN2/CartoonGAN (verify license & format)

Note: For now, set the Model URL field in the UI to a known CDN if you don’t have local files.
