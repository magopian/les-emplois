import factory
import pytest
from django.utils.timezone import timedelta

import itou.companies.enums as companies_enums
import itou.employee_record.enums as er_enums
from itou.companies.models import Company
from itou.employee_record.constants import (
    EMPLOYEE_RECORD_EITI_AVAILABILITY_DATE,
    EMPLOYEE_RECORD_FEATURE_AVAILABILITY_DATE,
)
from itou.job_applications.models import JobApplication
from tests.companies.factories import CompanyFactory
from tests.employee_record.factories import EmployeeRecordWithProfileFactory
from tests.job_applications.factories import JobApplicationFactory, JobApplicationWithoutApprovalFactory
from tests.utils.test import TestCase


class EmployeeRecordEligibilityTest(TestCase):
    """
    Tests for `eligible_as_employee_record` queryset method.
    This method has been refactored to stick closely to clearly defined business and technical rules.
    Hence a new suite of tests.
    TODO: to be completed soon with upcoming changes to be made in the `move_company_data` process.
    """

    def test_target_company(self):
        # Hiring SIAE is the expected SIAE
        company_good = CompanyFactory()
        company_bad = CompanyFactory()
        eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company_good)
        non_eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company_bad)

        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company_good)
        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company_good)

    def test_existing_employee_record(self):
        # A job application must not have any employee record linked if newly created
        company = CompanyFactory()
        non_eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company)
        eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company)
        EmployeeRecordWithProfileFactory(job_application=non_eligible_job_application, status=er_enums.Status.READY)

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company)
        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company)

    def test_siae_kind(self):
        # Hiring SIAE must be of a specific kind to use employee record feature
        company_good = CompanyFactory()
        company_bad = CompanyFactory(kind=companies_enums.CompanyKind.EATT)
        # job application created with a fake approval
        # to avoid filtering criteria with empty approval
        non_eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company_bad)
        eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company_good)

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company_bad)
        assert eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company_bad)

    def test_admin_validation(self):
        # Employee record creation can be blocked via admin for a given job application
        company = CompanyFactory()
        non_eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, create_employee_record=False
        )
        eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, create_employee_record=True
        )

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company)
        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company)

    def test_hiring_start_date(self):
        # Hiring date must be after the employee record feature availability date
        bad_ts = EMPLOYEE_RECORD_FEATURE_AVAILABILITY_DATE - timedelta(days=1)
        good_ts = EMPLOYEE_RECORD_FEATURE_AVAILABILITY_DATE + timedelta(days=1)
        company = CompanyFactory(
            kind=factory.fuzzy.FuzzyChoice(set(Company.ASP_EMPLOYEE_RECORD_KINDS) - {companies_enums.CompanyKind.EITI})
        )
        non_eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, hiring_start_at=bad_ts
        )
        eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, hiring_start_at=good_ts
        )

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company)
        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company)

    def test_hiring_start_date_for_eiti(self):
        # Hiring date must be after the employee record feature availability date
        bad_ts = EMPLOYEE_RECORD_EITI_AVAILABILITY_DATE - timedelta(days=1)
        good_ts = EMPLOYEE_RECORD_EITI_AVAILABILITY_DATE + timedelta(days=1)
        company = CompanyFactory(kind=companies_enums.CompanyKind.EITI)
        non_eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, hiring_start_at=bad_ts
        )
        eligible_job_application = JobApplicationFactory(
            with_approval=True, to_company=company, hiring_start_at=good_ts
        )

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company)
        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company)

    def test_existing_approval(self):
        # Job application must be linked to an existing approval to be eligible
        company = CompanyFactory()

        non_eligible_job_application = JobApplicationWithoutApprovalFactory(to_company=company)
        eligible_job_application = JobApplicationFactory(with_approval=True, to_company=company)

        assert non_eligible_job_application not in JobApplication.objects.eligible_as_employee_record(company)
        assert eligible_job_application in JobApplication.objects.eligible_as_employee_record(company)


def test_existing_new_employee_records():
    company = CompanyFactory()
    expected_employee_record = EmployeeRecordWithProfileFactory(
        job_application__to_company=company, status=er_enums.Status.NEW
    )
    EmployeeRecordWithProfileFactory(job_application__to_company=company, status=er_enums.Status.READY)

    assert list(JobApplication.objects.eligible_as_employee_record(company)) == [
        expected_employee_record.job_application
    ]


@pytest.mark.parametrize("field", ["asp_measure", "siret", "approval_number"])
def test_existing_new_employee_records_are_eligible_with_a_different_value_for_field(field):
    employee_record = EmployeeRecordWithProfileFactory(status=er_enums.Status.NEW, **{field: ""})

    assert list(JobApplication.objects.eligible_as_employee_record(employee_record.job_application.to_company)) == [
        employee_record.job_application
    ]
