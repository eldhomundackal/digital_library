"""Integration test stubs for Reviews and Downloads API flow.

These tests verify the HTTP layer (router → service).
Full integration tests require a running PostgreSQL + Redis instance.
Mark with pytest.mark.integration to skip in unit-only CI runs.
"""

import pytest


@pytest.mark.integration
class TestBookReviewsAPI:
    """Book rating and review endpoints."""

    def test_reader_can_submit_rating(self) -> None:
        """POST /books/{id}/reviews creates a Rating row and returns ReviewResponse."""
        pytest.skip("Requires running DB + reader token")

    def test_publisher_cannot_rate_own_book(self) -> None:
        """POST /books/{id}/reviews returns 403 if publisher owns the book."""
        pytest.skip("Requires running DB")

    def test_duplicate_rating_returns_400(self) -> None:
        """POST /books/{id}/reviews returns 400 if user already rated this book."""
        pytest.skip("Requires running DB")

    def test_reader_can_update_review(self) -> None:
        """PATCH /books/{id}/reviews updates rating and sets is_edited=True."""
        pytest.skip("Requires running DB")

    def test_reader_can_delete_review(self) -> None:
        """DELETE /books/{id}/reviews soft-deletes review and removes rating."""
        pytest.skip("Requires running DB")

    def test_get_book_reviews_returns_rating_summary(self) -> None:
        """GET /books/{id}/reviews includes average rating and breakdown."""
        pytest.skip("Requires running DB")

    def test_get_book_reviews_sorted_by_rating(self) -> None:
        """GET /books/{id}/reviews?sort_by=highest returns reviews in order."""
        pytest.skip("Requires running DB")

    def test_get_my_review_returns_null_if_no_review(self) -> None:
        """GET /books/{id}/reviews/me returns null when no review exists."""
        pytest.skip("Requires running DB + auth token")


@pytest.mark.integration
class TestReviewRepliesAPI:
    """Review reply endpoints."""

    def test_reader_can_reply_to_review(self) -> None:
        """POST /reviews/{id}/replies creates a reply."""
        pytest.skip("Requires running DB + reader token")

    def test_publisher_reply_sets_is_publisher_response(self) -> None:
        """POST /reviews/{id}/replies auto-sets is_publisher_response for book owner."""
        pytest.skip("Requires running DB")

    def test_owner_can_update_reply(self) -> None:
        """PATCH /reviews/{id}/replies/{id} updates the reply."""
        pytest.skip("Requires running DB")

    def test_non_owner_cannot_update_reply(self) -> None:
        """PATCH /reviews/{id}/replies/{id} returns 403 for non-owner."""
        pytest.skip("Requires running DB")

    def test_owner_can_delete_reply(self) -> None:
        """DELETE /reviews/{id}/replies/{id} removes the reply."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestReviewReportsAPI:
    """Review reporting endpoints."""

    def test_reader_can_report_review(self) -> None:
        """POST /reviews/{id}/report creates a ReviewReport with PENDING status."""
        pytest.skip("Requires running DB + reader token")

    def test_duplicate_report_returns_400(self) -> None:
        """POST /reviews/{id}/report returns 400 if user already reported."""
        pytest.skip("Requires running DB")

    def test_reader_can_report_reply(self) -> None:
        """POST /reviews/{id}/replies/{id}/report creates a report."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminReviewsAPI:
    """Admin review moderation endpoints."""

    def test_admin_can_list_all_reviews(self) -> None:
        """GET /admin/reviews returns all active reviews."""
        pytest.skip("Requires running DB + admin token")

    def test_admin_can_list_reported_reviews(self) -> None:
        """GET /admin/reviews/reported returns reviews with reports."""
        pytest.skip("Requires running DB")

    def test_admin_can_remove_review(self) -> None:
        """DELETE /admin/reviews/{id} soft-deletes review and all replies."""
        pytest.skip("Requires running DB")

    def test_admin_can_dismiss_report(self) -> None:
        """POST /admin/reviews/{id}/dismiss-report sets report status=DISMISSED."""
        pytest.skip("Requires running DB")
