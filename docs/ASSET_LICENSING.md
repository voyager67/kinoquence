# Asset provenance and licensing

Every imported or generated element needs a provenance record before a public/commercial release: images, illustrations, videos, fonts, music, sound effects, voice recordings, logos, datasets and third-party code.

`assets.csv` columns:

- `path`: repository-relative local path or canonical asset URL.
- `asset_type`: image, video, audio, font, model_output, code, etc.
- `creator`: creator or provider.
- `source_url`: source location or generation record.
- `license`: exact license or applicable service terms; do not write `free`.
- `attribution`: required credit text, if any.
- `commercial_use`: yes/no/conditional; include a note when conditional.
- `notes`: restrictions, model/version, consent, release, expiry or verification details.

Unknown is not a license. If rights are unknown, do not include the asset in a redistributed bundle. Do not assume a model-generated result is automatically free of third-party rights or safe to use commercially. Check the model/provider terms, voice rights, reference image rights, likeness permissions, trademarks and applicable law. Kinoquence's documentation license does not override the license of any exported asset.
