from io import BytesIO


async def create_bucket(session, endpoint_url, bucket_name, number_of_files):
    async with session.client("s3", endpoint_url=endpoint_url) as s3:
        resp = await s3.create_bucket(Bucket=bucket_name)
        for i in range(number_of_files):
            with BytesIO(b"A Text") as f:
                await s3.upload_fileobj(f, bucket_name, f"file_{i}")
