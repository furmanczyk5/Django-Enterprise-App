import os
import re

from boto.s3.key import Key
from boto.s3.connection import S3Connection
from storages.backends.s3boto import S3BotoStorage

from django.conf import settings
from django.core.files.storage import get_storage_class


StaticS3BotoStorage = lambda: S3BotoStorage(
    bucket=settings.AWS_STATIC_STORAGE_BUCKET_NAME)
MediaS3BotoStorage = lambda: S3BotoStorage(
    bucket=settings.AWS_STORAGE_BUCKET_NAME)


class DupeS3BotoStorage(S3BotoStorage):
    """
    S3 storage backend that saves the files locally, too (without compress)
    """
    def __init__(self, *args, **kwargs):
        super(DupeS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "django.contrib.staticfiles.storage.StaticFilesStorage")()
        self.bucket_name = settings.AWS_STATIC_STORAGE_BUCKET_NAME

    def save(self, name, content):
        name = super(DupeS3BotoStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name


class CachedS3BotoStorage(S3BotoStorage):
    """
    S3 storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()
        self.bucket_name = settings.AWS_STATIC_STORAGE_BUCKET_NAME

    def save(self, name, content):
        name = super(CachedS3BotoStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name


def copy_file_to_s3(local_filepath, remote_filepath, bucket_name=settings.AWS_STATIC_STORAGE_BUCKET_NAME):
    access_key = settings.AWS_S3_ACCESS_KEY_ID
    secret_key = settings.AWS_S3_SECRET_ACCESS_KEY

    connection = S3Connection(access_key, secret_key)
    bucket = connection.get_bucket(bucket_name)
    key = Key(bucket)
    key.key = remote_filepath
    return key.set_contents_from_filename(local_filepath)


def write_string_to_s3_file(content, remote_filepath, bucket_name=settings.AWS_STATIC_STORAGE_BUCKET_NAME):
    access_key = settings.AWS_S3_ACCESS_KEY_ID
    secret_key = settings.AWS_S3_SECRET_ACCESS_KEY

    connection = S3Connection(access_key, secret_key)
    bucket = connection.get_bucket(bucket_name)
    key = Key(bucket)
    key.key = remote_filepath
    return key.set_contents_from_string(content)


def read_string_from_s3_file(remote_filepath, bucket_name=settings.AWS_STATIC_STORAGE_BUCKET_NAME):
    access_key = settings.AWS_S3_ACCESS_KEY_ID
    secret_key = settings.AWS_S3_SECRET_ACCESS_KEY

    # remove root domain from url path
    root_path = os.path.join("https://s3.amazonaws.com/", settings.AWS_STATIC_STORAGE_BUCKET_NAME)
    escaped_root_path = re.escape(root_path)
    regex_res = re.match("(?:{0})*/{{0,1}}(.*)".format(escaped_root_path), remote_filepath)
    if regex_res:
        remote_filepath = regex_res.groups()[0]

    connection = S3Connection(access_key, secret_key)
    bucket = connection.get_bucket(bucket_name)
    key = bucket.get_key(remote_filepath)
    return key.get_contents_as_string()

