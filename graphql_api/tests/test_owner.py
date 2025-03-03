import asyncio
from datetime import timedelta
from unittest.mock import patch

from django.test import TransactionTestCase
from django.utils import timezone
from freezegun import freeze_time

from codecov_auth.models import OwnerProfile
from codecov_auth.tests.factories import (
    GetAdminProviderAdapter,
    OwnerFactory,
    UserFactory,
)
from core.tests.factories import CommitFactory, OwnerFactory, RepositoryFactory
from plan.constants import PlanName
from reports.tests.factories import CommitReportFactory, UploadFactory

from .helper import GraphQLTestHelper, paginate_connection

query_repositories = """{
    owner(username: "%s") {
        orgUploadToken
        ownerid
        isCurrentUserPartOfOrg
        yaml
        repositories%s {
            totalCount
            edges {
                node {
                    name
                }
            }
            pageInfo {
                hasNextPage
                %s
            }
        }
    }
}
"""


class TestOwnerType(GraphQLTestHelper, TransactionTestCase):
    def setUp(self):
        self.owner = OwnerFactory(username="codecov-user", service="github")
        random_user = OwnerFactory(username="random-user", service="github")
        RepositoryFactory(
            author=self.owner, active=True, activated=True, private=True, name="a"
        )
        RepositoryFactory(
            author=self.owner, active=False, private=False, activated=False, name="b"
        )
        RepositoryFactory(
            author=random_user, active=True, activated=False, private=True, name="not"
        )
        RepositoryFactory(
            author=random_user,
            active=True,
            private=False,
            activated=True,
            name="still-not",
        )

    def test_fetching_repositories(self):
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data == {
            "owner": {
                "orgUploadToken": None,
                "ownerid": self.owner.ownerid,
                "isCurrentUserPartOfOrg": True,
                "yaml": None,
                "repositories": {
                    "totalCount": 2,
                    "edges": [{"node": {"name": "a"}}, {"node": {"name": "b"}}],
                    "pageInfo": {"hasNextPage": False},
                },
            }
        }

    def test_fetching_repositories_with_pagination(self):
        query = query_repositories % (self.owner.username, "(first: 1)", "endCursor")
        # Check on the first page if we have the repository b
        data_page_one = self.gql_request(query, owner=self.owner)
        connection = data_page_one["owner"]["repositories"]
        assert connection["edges"][0]["node"] == {"name": "a"}
        pageInfo = connection["pageInfo"]
        assert pageInfo["hasNextPage"] == True
        next_cursor = pageInfo["endCursor"]
        # Check on the second page if we have the other repository, by using the cursor
        query = query_repositories % (
            self.owner.username,
            f'(first: 1, after: "{next_cursor}")',
            "endCursor",
        )
        data_page_two = self.gql_request(query, owner=self.owner)
        connection = data_page_two["owner"]["repositories"]
        assert connection["edges"][0]["node"] == {"name": "b"}
        pageInfo = connection["pageInfo"]
        assert pageInfo["hasNextPage"] == False

    def test_fetching_active_repositories(self):
        query = query_repositories % (
            self.owner.username,
            "(filters: { active: true })",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "a"}]

    def test_fetching_repositories_by_name(self):
        query = query_repositories % (
            self.owner.username,
            '(filters: { term: "a" })',
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "a"}]

    def test_fetching_public_repository_when_unauthenticated(self):
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "b"}]

    def test_fetching_repositories_with_ordering(self):
        query = query_repositories % (
            self.owner.username,
            "(ordering: NAME, orderingDirection: DESC)",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "b"}, {"name": "a"}]

    def test_fetching_repositories_inactive_repositories(self):
        query = query_repositories % (
            self.owner.username,
            "(filters: { active: false })",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "b"}]

    def test_fetching_repositories_active_repositories(self):
        query = query_repositories % (
            self.owner.username,
            "(filters: { active: true })",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "a"}]

    def test_fetching_repositories_activated_repositories(self):
        query = query_repositories % (
            self.owner.username,
            "(filters: { activated: true })",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "a"}]

    def test_fetching_repositories_deactivated_repositories(self):
        query = query_repositories % (
            self.owner.username,
            "(filters: { activated: false })",
            "",
        )
        data = self.gql_request(query, owner=self.owner)
        repos = paginate_connection(data["owner"]["repositories"])
        assert repos == [{"name": "b"}]

    def test_is_part_of_org_when_unauthenticated(self):
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query)
        assert data["owner"]["isCurrentUserPartOfOrg"] is False

    def test_is_part_of_org_when_authenticated_but_not_part(self):
        org = OwnerFactory(username="random_org_test", service="github")
        user = OwnerFactory(username="random_org_user", service="github")
        query = query_repositories % (org.username, "", "")
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isCurrentUserPartOfOrg"] is False

    def test_is_part_of_org_when_user_asking_for_themself(self):
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["isCurrentUserPartOfOrg"] is True

    def test_is_part_of_org_when_user_path_of_it(self):
        org = OwnerFactory(username="random_org_test", service="github")
        user = OwnerFactory(
            username="random_org_user", service="github", organizations=[org.ownerid]
        )
        query = query_repositories % (org.username, "", "")
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isCurrentUserPartOfOrg"] is True

    def test_yaml_when_owner_not_have_yaml(self):
        org = OwnerFactory(username="no_yaml", yaml=None, service="github")
        self.owner.organizations = [org.ownerid]
        self.owner.save()
        query = query_repositories % (org.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["yaml"] is None

    def test_yaml_when_current_user_not_part_of_org(self):
        yaml = {"test": "test"}
        org = OwnerFactory(username="no_yaml", yaml=yaml, service="github")
        self.owner.organizations = []
        self.owner.save()
        query = query_repositories % (org.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["yaml"] is None

    def test_yaml_return_data(self):
        yaml = {"test": "test"}
        org = OwnerFactory(username="no_yaml", yaml=yaml, service="github")
        self.owner.organizations = [org.ownerid]
        self.owner.save()
        query = query_repositories % (org.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["yaml"] == "test: test\n"

    @patch("codecov_auth.commands.owner.owner.OwnerCommands.set_yaml_on_owner")
    def test_repository_dispatch_to_command(self, command_mock):
        asyncio.set_event_loop(asyncio.new_event_loop())
        repo = RepositoryFactory(author=self.owner, private=False)
        query_repositories = """{
            owner(username: "%s") {
                repository(name: "%s") {
                    ... on Repository {
                        name
                    }
                }
            }
        }
        """
        command_mock.return_value = repo
        query = query_repositories % (repo.author.username, repo.name)
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["repository"]["name"] == repo.name

    def test_resolve_number_of_uploads_per_user(self):
        query_uploads_number = """{
            owner(username: "%s") {
               numberOfUploads
            }
        }
        """
        repository = RepositoryFactory.create(
            author__plan=PlanName.BASIC_PLAN_NAME.value, author=self.owner
        )
        first_commit = CommitFactory.create(repository=repository)
        first_report = CommitReportFactory.create(commit=first_commit)
        for i in range(150):
            UploadFactory.create(report=first_report)
        query = query_uploads_number % (repository.author.username)
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["numberOfUploads"] == 150

    def test_is_current_user_not_an_admin(self):
        query_current_user_is_admin = """{
            owner(username: "%s") {
               isAdmin
            }
        }
        """
        user = OwnerFactory(username="random_org_user", service="github")
        owner = OwnerFactory(username="random_org_test", service="github")
        query = query_current_user_is_admin % (owner.username)
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isAdmin"] is False

    @patch(
        "codecov_auth.commands.owner.interactors.get_is_current_user_an_admin.get_provider"
    )
    def test_is_current_user_an_admin(self, mocked_get_adapter):
        query_current_user_is_admin = """{
            owner(username: "%s") {
               isAdmin
            }
        }
        """
        user = OwnerFactory(username="random_org_admin", service="github")
        owner = OwnerFactory(
            username="random_org_test", service="github", admins=[user.ownerid]
        )
        mocked_get_adapter.return_value = GetAdminProviderAdapter()
        query = query_current_user_is_admin % (owner.username)
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isAdmin"] is True

    def test_ownerid(self):
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["ownerid"] == self.owner.ownerid

    @patch("codecov_auth.commands.owner.owner.OwnerCommands.get_org_upload_token")
    def test_get_org_upload_token(self, mocker):
        mocker.return_value = "upload_token"
        query = query_repositories % (self.owner.username, "", "")
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["orgUploadToken"] == "upload_token"

    # Applies for old users that didn't get their owner profiles created w/ their owner
    def test_when_owner_profile_doesnt_exist(self):
        owner = OwnerFactory(username="no-profile-user")
        owner.profile.delete()
        query = """{
            owner(username: "%s") {
                defaultOrgUsername
                username
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=owner)
        assert data["owner"]["defaultOrgUsername"] == None

    def test_get_default_org_username_for_owner(self):
        organization = OwnerFactory(username="sample-org", service="github")
        owner = OwnerFactory(
            username="sample-owner",
            service="github",
            organizations=[organization.ownerid],
        )
        OwnerProfile.objects.filter(owner_id=owner.ownerid).update(
            default_org=organization
        )
        query = """{
            owner(username: "%s") {
                defaultOrgUsername
                username
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=owner)
        assert data["owner"]["defaultOrgUsername"] == organization.username

    def test_owner_without_default_org_returns_null(self):
        owner = OwnerFactory(username="sample-owner", service="github")
        query = """{
            owner(username: "%s") {
                defaultOrgUsername
                username
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=owner)
        assert data["owner"]["defaultOrgUsername"] == None

    def test_owner_without_owner_profile_returns_no_default_org(self):
        owner = OwnerFactory(username="sample-owner", service="github")
        query = """{
            owner(username: "%s") {
                defaultOrgUsername
                username
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=owner)
        assert data["owner"]["defaultOrgUsername"] == None

    def test_is_current_user_not_activated(self):
        owner = OwnerFactory(username="sample-owner", service="github")
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["isCurrentUserActivated"] == False

    def test_is_current_user_not_activated_no_current_owner(self):
        owner = OwnerFactory(username="sample-owner", service="github")
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        self.client.force_login(user=UserFactory())
        data = self.gql_request(query, owner=None)
        assert data["owner"]["isCurrentUserActivated"] == False

    def test_is_current_user_activated(self):
        user = OwnerFactory(username="sample-user")
        owner = OwnerFactory(
            username="sample-owner", plan_activated_users=[user.ownerid]
        )
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isCurrentUserActivated"] == True

    def test_is_current_user_activated_when_plan_activated_users_is_none(self):
        user = OwnerFactory(username="sample-user")
        owner = OwnerFactory(username="sample-owner", plan_activated_users=None)
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=user)
        assert data["owner"]["isCurrentUserActivated"] == False

    def test_is_current_user_activated_anonymous(self):
        owner = OwnerFactory(username="sample-owner")
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query)
        assert data["owner"]["isCurrentUserActivated"] == False

    def test_admin_is_current_user_activated(self):
        owner = OwnerFactory(username="sample-owner", admins=[self.owner.ownerid])
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            owner.username
        )
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["isCurrentUserActivated"] == True

    def test_owner_is_current_user_activated(self):
        query = """{
            owner(username: "%s") {
                isCurrentUserActivated
            }
        }
        """ % (
            self.owner.username
        )
        data = self.gql_request(query, owner=self.owner)
        assert data["owner"]["isCurrentUserActivated"] == True

    @freeze_time("2023-06-19")
    def test_owner_trial_is_expired(self):
        current_org = OwnerFactory(
            username="random-trial-user",
            service="github",
            trial_start_date=timezone.now(),
            trial_end_date=timezone.now() + timedelta(days=-3),
        )
        query = """{
            owner(username: "%s") {
                trialStatus
            }
        }
        """ % (
            current_org.username
        )
        data = self.gql_request(query, owner=current_org)
        assert data["owner"]["trialStatus"] == "EXPIRED"

    @freeze_time("2023-06-19")
    def test_owner_plan_status(self):
        current_org = OwnerFactory(
            username="random-plan-user",
            service="github",
            trial_start_date=timezone.now(),
            trial_end_date=timezone.now() + timedelta(days=14),
        )
        query = """{
            owner(username: "%s") {
                plan {
                    trialStatus
                }
            }
        }
        """ % (
            current_org.username
        )
        data = self.gql_request(query, owner=current_org)
        assert data["owner"]["plan"] == {
            "trialStatus": "ONGOING",
        }
