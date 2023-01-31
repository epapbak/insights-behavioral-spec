# Copyright © 2022 Pavel Tisnovsky, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of test steps that check or access S3/S3 service."""

from src.minio import minio_client, bucket_check, read_object_into_buffer
import csv
from src.csv_checks import check_table_content


@given(u"S3 endpoint is set")
def set_S3_endpoint(context):
    """Set S3 endpoint value."""
    assert context.S3_endpoint is not None, "S3 endpoint not found in context"


@given(u"S3 endpoint is set to {endpoint}")
def set_S3_endpoint(context, endpoint):
    """Set S3 endpoint value."""
    assert endpoint is not None, "Endpoint needs to be specified"
    context.S3_endpoint = endpoint


@given(u"S3 port is set")
def set_S3_port(context):
    """Set S3 port value."""
    assert context.S3_port is not None, "S3 port not found in context"


@given(u"S3 port is set to {port:d}")
def set_S3_port(context, port):
    """Set S3 port value."""
    context.S3_port = port


@given(u"S3 access key is set")
def set_S3_access_key(context):
    """Set S3 access key."""
    assert context.S3_access_key is not None, "S3 Access key not found in context"


@given(u"S3 access key is set to {value}")
def set_S3_access_key(context, value):
    """Set S3 access key."""
    assert value is not None, "Access key needs to be specified"
    context.S3_access_key = value


@given(u"S3 secret access key is set")
def set_S3_secret_access_key(context):
    """Set S3 secret access key."""
    assert context.S3_secret_access_key is not None, "S3 Secret access key not found in context"


@given(u"S3 secret access key is set to {value}")
def set_S3_secret_access_key(context, value):
    """Set S3 secret access key."""
    assert value is not None, "Secret access key needs to be specified"
    context.S3_secret_access_key = value


@given(u"S3 bucket name is set to {value}")
def set_S3_bucket_name(context, value):
    """Set S3 bucket name."""
    assert value is not None, "Bucket name needs to be specified"
    context.S3_bucket_name = value


@given(u"S3 connection is established")
def establish_S3_connection(context):
    """Establish connection to S3."""
    minio_client(context)


@then(u"I should see following objects generated in S3")
def check_objects_in_s3(context):
    """Check that all specified objects was generated."""
    # check if bucket used by exporter exists
    bucket_check(context)

    # retrieve all objects stored in bucket
    objects = context.minio_client.list_objects(context.S3_bucket_name, recursive=True)
    # retrieve object names only
    names = [o.object_name for o in objects]
    print("S3 objects: ", names)

    # iterate over all items in feature table
    for row in context.table:
        object_name = f"{context.S3_bucket_name}/{row['File name']}"
        assert object_name in names, \
            "Can not find object {} in bucket {}".format(object_name, context.S3_bucket_name)


@then(u"I should see following number of records stored in CSV objects in S3")
def check_csv_content_in_s3(context):
    """Check content of objects stored in S3."""
    # check if bucket used by exporter exists
    bucket_check(context)

    # iterate over all items in feature table
    for row in context.table:
        object_name = f"{context.S3_bucket_name}/{row['File name']}"
        expected_records = int(row["Records"])

        # read object content
        buff = read_object_into_buffer(context, object_name)

        # read CVS from buffer
        csvFile = csv.reader(buff)

        # skip the first row of the CSV file.
        next(csvFile)

        stored_records = 0
        for lines in csvFile:
            stored_records += 1

        # now check numbers
        assert (
            expected_records == stored_records
        ), "Expected number records in object {} is {} but {} was read".format(
            object_name, expected_records, stored_records
        )


@then(u"I should see following records in exported object {object_name} placed in column {column:d}")  # noqa: E501
@then(u"I should see following records in exported object {object_name} placed in columns {column:d} and {column2:d}")   # noqa: E501
def check_records_in_csv_object(context, object_name, column, column2=None):
    """Check if all records are really stored in given CSV file/object in S3/S3."""
    # read object content
    object_name = f"{context.S3_bucket_name}/{object_name}"
    buff = read_object_into_buffer(context, object_name)

    check_table_content(context, buff, object_name, column, column2)
