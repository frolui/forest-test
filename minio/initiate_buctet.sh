# Configure MinIO Local client
mc alias set local http://localhost:9025 minioadmin minioadmin123 --api S3v4
mc mb local/mybucket    # Create a bucket named 'mybucket'
mc policy set public mybucket  # Set bucket policy to public
mc anonymous set download local/mybucket   # Allow anonymous download access to the bucket
# Enable versioning for the bucket
mc version enable local/mybucket