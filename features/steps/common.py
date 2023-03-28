# Copyright © 2021, 2022, 2023 Pavel Tisnovsky, Red Hat, Inc.
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

"""Implementation of common test steps."""

from shutil import which
from datetime import datetime
from time import sleep


from behave import given, then, when


@given("the system is in default state")
def system_in_default_state(context):
    """Check the default system state."""
    pass


@when("I look for executable file {filename}")
def look_for_executable_file(context, filename):
    """Try to find given executable file on PATH."""
    context.filename = filename
    context.found = which(filename)


@then("I should find that file on PATH")
def file_was_found(context):
    """Check if the file was found on PATH."""
    assert context.found is not None, \
        "executable filaname '{}' is not on PATH".format(context.filename)


@then("The process should finish with exit code {exit_code:d}")
def check_process_exit_code(context, exit_code):
    """Check exit code of process."""
    assert context.return_code == exit_code, \
        "Unexpected exit code {}. Output:\n{}".format(context.return_code, context.output)


@then('I should see following message in service output: "{message}"')
def check_message_in_output(context, message):
    """Check if output generated by tested service contains given message."""
    # preliminary checks
    assert context.output is not None
    assert type(context.output) is list, "wrong type of output"

    # check the output, line by line
    for line in context.output:
        if message in line:
            break
    else:
        raise Exception("Expected message not found in {}".format(context.output))


@then('BuildTime is a proper datetime stamp')
def check_build_datetime_stamp(context):
    """Check build timestamp taken from service output."""
    buildTime = context.response.json()["info"]["BuildTime"]

    # an output example: 'Mon Mar 20 13:20:48 CET 2023'
    timestampFormat = "%a %b %d %H:%M:%S %Z %Y"

    # just try to parse datetime, if it fails, it fails
    datetime.strptime(buildTime, timestampFormat)


@then('DBVersion is in the proper format')
def check_db_version(context):
    """Check database version taken from service output."""
    dbVersion = context.response.json()["info"]["DB_version"]

    # just try to parse the version, that's all
    version = int(dbVersion)

    assert version >= 1, "Improper DB version {}".format(version)


@when('I wait {number:n} seconds')
def wait_n_seconds(context, number):
    """Wait for n seconds between test steps."""
    sleep(number)
