# Copyright © 2023 Pavel Tisnovsky, Red Hat, Inc.
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

"""Implementation of test steps that run Insights Results Aggregator Mock and check its output."""

import requests
import subprocess

from behave import when, then
from src.process_output import process_generated_output
from src.asserts import assert_sets_equality
from src.utils import get_array_from_json, construct_rh_token, retrieve_set_of_clusters_from_table


# default name of file generated by Insights Aggregator Mock during testing
test_output = "test"


@when("I run the Insights Results Aggregator Mock with the {flag} command line flag")
def run_insights_results_aggregator_mock_with_flag(context, flag):
    """Start the Insights Results Aggregator Mock with given command-line flag."""
    out = subprocess.Popen(
        ["insights-results-aggregator-mock", flag],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # check if subprocess has been started and its output caught
    assert out is not None
    context.add_cleanup(out.terminate)

    # it is expected that exit code will be 0 or 2
    process_generated_output(context, out, 2)


def check_help_from_mock(context):
    """Check if help is displayed by Insights Results Aggregator Mock."""
    expected_output = """
Service to provide content for OCP rules

Usage:

    insights-results-aggregator-mock [command]

The commands are:

    <EMPTY>                      starts content service
    start-service                starts content service
    help     print-help          prints help
    config   print-config        prints current configuration set by files & env variables
    version  print-version-info  prints version info
    authors  print-authors       prints authors"""

    assert context.stdout is not None
    stdout = context.stdout.decode("utf-8").replace("\t", "    ")

    # preliminary checks
    assert stdout is not None, "stdout object should exist"
    assert isinstance(stdout, str), "wrong type of stdout object"

    # check the output
    assert stdout.strip() == expected_output.strip(), f"{stdout} != {expected_output}"


def check_version_from_mock(context):
    """Check if version info is displayed by Insights Results Aggregator Mock."""
    # preliminary checks
    assert context.output is not None
    assert isinstance(context.output, list), "wrong type of output"

    # check the output
    assert "Version:\t0.1" in context.output, f"Caught output: {context.output}"


def check_authors_info_from_mock(context):
    """Check if information about authors is displayed by Insights Results Aggregator Mock."""
    # preliminary checks
    assert context.output is not None
    assert isinstance(context.output, list), "wrong type of output"

    # check the output
    assert (
        "Pavel Tisnovsky <ptisnovs@redhat.com>" in context.output
    ), f"Caught output: {context.output}"


@then("I should see actual configuration displayed by Insights Results Aggregator Mock on standard output")  # noqa E501
def check_actual_configuration(context):
    """Check if actual configuration is displayed by Insights Results Aggregator Mock."""
    # preliminary checks
    assert context.output is not None
    assert isinstance(context.output, list), "wrong type of output"

    # check the output
    assert "Server" in context.output[1], f"Caught output: {context.output}"
    assert "Address" in context.output[2], f"Caught output: {context.output}"
    assert "APIPrefix" in context.output[3], f"Caught output: {context.output}"
    assert "APISpecFile" in context.output[4], f"Caught output: {context.output}"
    assert "Content" in context.output[7], f"Caught output: {context.output}"


@when("I request list of organizations")
def request_list_of_organizations(context):
    """Call Insights Results Aggregator Mock service and retrieve list of organizations."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/organizations"
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@then("I should retrieve following list of organizations")
def check_list_of_organizations(context):
    """Check if Insights Results Aggregator Mock service returned expected list of organizations."""
    # construct set of expected organizations
    # from a table provided in feature file
    expected_organizations = set(int(item["Organization"]) for item in context.table)

    # construct set of actually found organizations
    # from JSON payload returned by the service
    found_organizations = set(get_array_from_json(context, "organizations"))

    # compare both sets and display diff (if diff is found)
    assert_sets_equality("organizations", expected_organizations, found_organizations)


@when("I request list of clusters for organization {organization:d}")
def request_list_of_clusters(context, organization):
    """Call Insights Results Aggregator Mock service and retrieve list of clusters for given org."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/organizations/{organization}/clusters"  # noqa E501
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK or 404 Not Found
    assert context.response.status_code in (200, 403)


@then("I should retrieve following list of clusters")
@then("I should retrieve following list of clusters stored in attribute {selector}")
def check_list_of_clusters(context, selector="clusters"):
    """Check if Insights Results Aggregator Mock service returned expected list of clusters."""
    # construct set of expected cluster names
    # from a table provided in feature file
    expected_clusters = retrieve_set_of_clusters_from_table(context)

    # construct set of actually found clusters
    # from JSON payload returned by the service
    found_clusters = set(get_array_from_json(context, selector))

    # compare both sets and display diff (if diff is found)
    assert_sets_equality("cluster list", expected_clusters, found_clusters)


@when("I request list of clusters hitting rule with name {rule_name} and error key {error_key}")
def request_clusters_hitting_rule(context, rule_name, error_key):
    """Check if Insights Results Aggregator Mock service returned expected list of clusters hitting rule."""  # noqa E501
    url = f"http://{context.hostname}:{context.port}{context.api_prefix}/rule/{rule_name}.report|{error_key}/clusters_detail/"  # noqa E501
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@when("I request list of groups")
def request_list_of_groups(context):
    """Call Insights Results Aggregator Mock service and retrieve list groups."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/groups"
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@then("I should retrieve following list of groups")
def check_list_of_groups(context):
    """Check list of groups returned from the service."""
    # construct set of expected group names
    # from a table provided in feature file
    expected_group_names = set(item["Title"] for item in context.table)

    # construct set of actually found group names
    # from JSON payload returned by the service
    found_group_names = set(get_array_from_json(context, "groups", "title"))

    # compare both sets and display diff (if diff is found)
    assert_sets_equality("list of groups", expected_group_names, found_group_names)

    # now we know that we retrieved the correct list of groups,
    # time to check the content
    for group in context.response.json()["groups"]:
        assert group is not None

        # retrieve attributes from JSON object
        title = group["title"]
        description = group["description"]
        tags = ",".join(group["tags"])

        # try to find the corresponding record in BDD table
        for item in context.table:
            if item["Title"] == title and \
                    item["Description"] == description and \
                    item["Tags"] == tags:
                # we found the record
                break
        else:
            # record was not found
            raise KeyError(f"Group {group} was not returned by the service")


@when("I request report for cluster {cluster:S}")
def request_report_for_cluster(context, cluster):
    """Call Insights Results Aggregator Mock service and retrieve report for given cluster."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/report/{cluster}"  # noqa E501
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@when("I request report for cluster {cluster:S} from organization {organization:d}")
def request_report_for_cluster_in_organization(context, cluster, organization):
    """Call Insights Results Aggregator Mock service and retrieve report for given cluster and organization."""  # noqa E501
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/report/{organization}/{cluster}"  # noqa E501
    context.response = requests.get(url)

    # check the response
    assert context.response is not None


@when("I request upgrade risk for cluster {cluster:S}")
def request_upgrade_for_cluster(context, cluster):
    """Call Insights Results Aggregator Mock service and retrieve upgrade risk for given cluster."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/cluster/{cluster}/upgrade-risks-prediction"  # noqa E501
    context.response = requests.get(url)

    # check the response
    assert context.response is not None


@then("The report should contain {expected_count:d} rule hits")
@then("The report should contain 1 rule hit")
@then("The report should contain one rule hit")
def check_number_of_rule_hits(context, expected_count=1):
    """Check number of rule hits in report returned from the service."""
    json = context.response.json()
    assert json is not None

    assert "report" in json, "Report attribute is missing"
    report = json["report"]

    assert "meta" in report, "Meta attribute is missing in report attribute"
    meta = report["meta"]

    assert "count" in meta, "Count attribute is missing in meta attribute"
    actual_count = meta["count"]

    # compare actual count with expected count
    assert actual_count == expected_count, \
        f"Expected rule hits count: {expected_count}, actual count: {actual_count}"


@then("The report should not contain any rule hit")
def check_no_rule_hits(context):
    """Check number of rule hits in report returned from the service."""
    check_number_of_rule_hits(context, 0)


@then("I should find following rule hit in cluster report")
@then("I should find following rule hits in cluster report")
def check_all_rule_hits(context):
    """Check the rule hits returned by service against expected rule hits defined in scenario."""
    json = context.response.json()
    assert json is not None

    assert "report" in json, "Report attribute is missing"
    report = json["report"]

    assert "data" in report, "Data attribute is missing in report attribute"
    data = report["data"]

    # check if all rule hits defined in scenario is found in returned structure
    for rule_hit in context.table:
        expected_type = rule_hit["Type"]
        expected_rule_id = rule_hit["Rule ID"]
        expected_error_key = rule_hit["Error key"]
        expected_total_risk = int(rule_hit["Total risk"])
        expected_risk_of_change = int(rule_hit["Risk of change"])

        # try to find the corresponding record in rule hits returned by service
        for record in data:
            actual_type = record["details"]["type"]
            actual_rule_id = record["rule_id"]
            actual_error_key = record["details"]["error_key"]
            actual_total_risk = record["total_risk"]
            actual_risk_of_change = record["risk_of_change"]

            # exact match
            if all((actual_type == expected_type,
                    actual_rule_id == expected_rule_id,
                    actual_error_key == expected_error_key,
                    actual_total_risk == expected_total_risk,
                    actual_risk_of_change == expected_risk_of_change)):
                break
        else:
            # record was not found
            raise KeyError(f"Rule hit {rule_hit} was not returned by the service")


@then("The metadata should contain following attributes")
def check_metadata(context):
    """Check metadata returned from the service."""
    json = context.response.json()
    assert json is not None

    # try to retrieve metadata attribute which should be object containing more attributes
    assert "meta" in json, "meta attribute is missing"
    meta = json["meta"]

    # check if all metadata defined in scenario is found in returned structure
    for expected_metadata in context.table:
        expected_name = expected_metadata["Attribute name"]
        expected_value = expected_metadata["Attribute value"]

        # does the attribute exist?
        assert expected_name in meta, f"Attribute with name {expected_name} is missing"

        # has the attribute expected value?
        assert str(meta[expected_name]) == expected_value, \
            f"Attribute with name {expected_name} has unexpected value {meta[expected_name]}"


@when("I request results for the following list of clusters")
@when("I request results for the following list of clusters using token for organization {organization:d} account number {account}, and user {user}")  # noqa: E501
def request_results_for_list_of_clusters(context, organization=None, account=None, user=None):
    """Send list of clusters in JSON body of request into the service."""
    cluster_list = [item["Cluster name"] for item in context.table]
    assert cluster_list is not None, "Test step definition problem"

    # construct object to be send to the service
    json_request_body = {"clusters": cluster_list}

    # use RH identity token if needed
    if organization is not None and account is not None and user is not None:
        # URL for Insights Results Aggregator
        url = f"http://{context.hostname}:{context.port}{context.api_prefix}/organizations/{organization}/clusters/reports"  # noqa: E501
        # construct RH identity token for provided user info
        token = construct_rh_token(organization, account, user)
        # perform POST request
        context.response = requests.post(
            url, headers={"x-rh-identity": token}, json=json_request_body
        )
    else:
        # URL for Smart Proxy and for Insights Results Aggregator Mock
        url = f"http://{context.hostname}:{context.port}{context.api_prefix}/clusters"
        # perform POST request
        context.response = requests.post(url, json=json_request_body)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@then("I should see empty list of reports")
def check_list_of_reports_is_empty(context):
    """Check that list of reports returned from the service is empty."""
    json = context.response.json()
    assert json is not None

    # try to retrieve report attribute which should be object containing more attributes
    assert "reports" in json, "reports attribute is missing"
    reports = json["reports"]

    assert len(reports) == 0, "List of reports should be empty"


@then("I should see report for following list of clusters")
def check_reports_for_list_of_clusters(context):
    """Check list of reports returned from the service."""
    json = context.response.json()
    assert json is not None

    # try to retrieve report attribute which should be object containing more attributes
    assert "reports" in json, "reports attribute is missing"
    reports = json["reports"]

    # retrieve expected set of clusters
    expected_clusters = retrieve_set_of_clusters_from_table(context)
    assert expected_clusters is not None, "Test step definition problem"

    # cluster reports found in response
    found_clusters = reports.keys()

    # compare both sets and display diff (if diff is found)
    assert_sets_equality("cluster list", expected_clusters, found_clusters)

    # now we need to check reports for basic structure
    for cluster_name, cluster_entry in reports.items():
        assert "status" in cluster_entry, cluster_entry
        status = cluster_entry["status"]
        assert status == "ok", f"Unexpected status {status}"

        assert "report" in cluster_entry, cluster_entry
        report = cluster_entry["report"]

        assert "data" in report, report
        data = report["data"]

        assert "meta" in report, report
        meta = report["meta"]

        # check number of reports
        meta_count = meta["count"]
        report_count = len(data)
        assert meta_count == report_count, \
            "Incorrect number of reports {meta_count} <> {report_count}"


@then("I should see following list of unknown clusters")
def check_list_of_unknown_clusters(context):
    """Check if list of unknown clusters returned by service contains expected items."""
    # construct set of expected list of clusters
    # from a table provided in feature file
    expected_clusters = retrieve_set_of_clusters_from_table(context)
    assert expected_clusters is not None, "Test step definition problem"

    # construct set of actually found list of clusters
    # W/O report (i.e. "error" clusters
    found_clusters = set(get_array_from_json(context, "errors"))

    # compare both sets and display diff (if diff is found)
    assert_sets_equality("list of error clusters", expected_clusters, found_clusters)


@when("I request content and groups")
def request_content_and_list_of_groups(context):
    """Call Insights Results Aggregator Mock service and retrieve content and list groups."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/content"
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@then("I should retrieve empty content")
def check_empty_content(context):
    """Check that the content attribute exists and is empty."""
    json = context.response.json()
    assert json is not None

    # try to retrieve content attribute
    assert "content" in json, "content attribute is missing"
    content = json["content"]

    assert len(content) == 0, "content attribute should be empty"


@when("I ask for list of all acked rules")
def request_list_of_all_acked_rules(context):
    """Send request to tested service to return list of all acked rules."""
    url = f"http://{context.hostname}:{context.port}/{context.api_prefix}/ack"
    context.response = requests.get(url)

    # basic check if service responded with HTTP code 200 OK
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@then("I should retrieve list of {length:n} acked rules")
def check_list_of_acked_rules_length(context, length):
    """Test how many items are returned in a list of acked rules."""
    # try to retrieve data to be checked from response payload
    json = context.response.json()
    assert json is not None

    # JSON attribute with list of acked rules
    assert "data" in json, "Data attribute is missing in report attribute"
    data = json["data"]

    # check length of the list
    assert len(data) == length, f"Unexpected list of acked rules size {len(data)}"


@then("I should retrieve following list of acked rules")
def check_list_of_acked_rules(context):
    """Test if returned acked rules are expected."""
    # try to retrieve data to be checked from response payload
    json = context.response.json()
    assert json is not None

    # JSON attribute with list of acked rules
    assert "data" in json, "Data attribute is missing in report attribute"
    data = json["data"]

    # check if all acked rules in scenario is found in returned structure
    for rule in context.table:
        expected_rule_id = rule["Rule ID"]
        expected_error_key = rule["Error key"]
        expected_justification = rule["Justification"]
        expected_created_by = rule["Created by"]

        # try to find the corresponding record in list returned by service
        for record in data:
            rule_fqdn = record["rule"]

            # split FQDN into rule ID and error key
            actual_rule_id, actual_error_key = rule_fqdn.split("|")

            # strip the ".report" suffix
            assert actual_rule_id.endswith(".report")
            actual_rule_id = actual_rule_id[: -len(".report")]

            actual_justification = record["justification"]
            actual_created_by = record["created_by"]

            # exact match is required
            if all((actual_rule_id == expected_rule_id,
                    actual_error_key == expected_error_key,
                    actual_justification == expected_justification,
                    actual_created_by == expected_created_by)):
                break
        else:
            # record was not found
            raise KeyError(f"Rule {rule} was not returned by the service")


@when('I ack rule with ID "{rule_id}" and error key "{error_key}" without justification')
def perform_rule_ack_without_justification(context, rule_id, error_key):
    """Ack the rule identified by rule ID and error key."""
    # construct full rule FQDN
    rule_fqdn = f"{rule_id}.report|{error_key}"

    url = f"http://{context.hostname}:{context.port}{context.api_prefix}/ack/{rule_fqdn}"

    # perform GET request
    context.response = requests.get(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK or 201 Created
    assert context.response.status_code in (200, 201)


@when('I ack rule with ID "{rule_id}" and error key "{error_key}" with justification "{justification}"')  # noqa E501
def perform_rule_ack_with_justification(context, rule_id, error_key, justification):
    """Ack the rule identified by rule ID and error key."""
    # construct full rule FQDN
    rule_fqdn = f"{rule_id}.report|{error_key}"

    # construct object to be send to the service
    json_request_body = {"rule_id": rule_fqdn,
                         "justification": justification}

    url = f"http://{context.hostname}:{context.port}{context.api_prefix}/ack"

    # perform POST request
    context.response = requests.post(url, json=json_request_body)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK or 201 Created
    assert context.response.status_code in (200, 201)


@when('I change justification text for rule with ID "{rule_id}" and error key "{error_key}" to "{justification}"')  # noqa E501
def change_justification_text(context, rule_id, error_key, justification):
    """Change justification for a rule via POST call."""
    # construct full rule FQDN
    rule_fqdn = f"{rule_id}.report|{error_key}"

    # construct object to be send to the service
    json_request_body = {"justification": justification}

    url = f"http://{context.hostname}:{context.port}{context.api_prefix}/ack/{rule_fqdn}"

    # perform PUT request
    context.response = requests.put(url, json=json_request_body)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK
    assert context.response.status_code == requests.codes.ok, context.response.status_code


@when('I delete ack for rule with ID "{rule_id}" and error key "{error_key}"')
def delete_rule_ack(context, rule_id, error_key):
    """Delete ack for selected rule via REST API call."""
    # construct full rule FQDN
    rule_fqdn = f"{rule_id}.report|{error_key}"

    url = f"http://{context.hostname}:{context.port}{context.api_prefix}/ack/{rule_fqdn}"

    # perform DELETE request
    context.response = requests.delete(url)

    # check the response
    assert context.response is not None

    # HTTP status code of response should be 200 OK, 204 No Content, or 404 Not Found
    assert context.response.status_code in (200, 204, 404), \
        f"Status code is {context.response.status_code}"
