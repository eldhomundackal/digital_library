"""Integration test stubs for Books API flow.

These tests verify the Books HTTP layer (router → service).
Full integration tests require a running PostgreSQL + Redis + storage instance.
Mark with pytest.mark.integration to skip in unit-only CI runs.
"""

import pytest


@pytest.mark.integration
class TestPublicBooksAPI:
    """Public book browsing endpoints."""

    def test_list_books_returns_200(self) -> None:
        """GET /books returns paginated list of APPROVED books."""
        pytest.skip("Requires running DB")

    def test_get_book_detail_returns_200(self) -> None:
        """GET /books/{id} returns full book detail for APPROVED book."""
        pytest.skip("Requires running DB")

    def test_get_nonexistent_book_returns_404(self) -> None:
        """GET /books/{id} returns 404 for unknown UUID."""
        pytest.skip("Requires running DB")

    def test_list_books_search_by_title(self) -> None:
        """GET /books?search=... returns matching books using full-text search."""
        pytest.skip("Requires running DB with GIN index populated")

    def test_list_books_filter_by_category(self) -> None:
        """GET /books?category_id=... returns only books in that category."""
        pytest.skip("Requires running DB")

    def test_list_categories_returns_200(self) -> None:
        """GET /categories returns active categories with total_books count."""
        pytest.skip("Requires running DB")

    def test_list_tags_returns_only_approved(self) -> None:
        """GET /tags returns only APPROVED tags."""
        pytest.skip("Requires running DB")

    def test_list_authors_returns_200(self) -> None:
        """GET /authors returns paginated author list."""
        pytest.skip("Requires running DB")

    def test_get_author_detail_returns_200(self) -> None:
        """GET /authors/{id} returns author with book list."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestPublisherBooksAPI:
    """Publisher book management endpoints."""

    def test_publisher_can_create_book(self) -> None:
        """POST /publisher/books creates a DRAFT book."""
        pytest.skip("Requires running DB + approved publisher token + storage")

    def test_unapproved_publisher_cannot_create_book(self) -> None:
        """POST /publisher/books returns 403 if KYC not APPROVED."""
        pytest.skip("Requires running DB")

    def test_publisher_can_list_own_books(self) -> None:
        """GET /publisher/books returns only the authenticated publisher's books."""
        pytest.skip("Requires running DB + publisher token")

    def test_publisher_can_submit_draft_book(self) -> None:
        """POST /publisher/books/{id}/submit moves DRAFT -> PENDING."""
        pytest.skip("Requires running DB")

    def test_publisher_cannot_submit_already_pending_book(self) -> None:
        """POST /publisher/books/{id}/submit returns 400 if already PENDING."""
        pytest.skip("Requires running DB")

    def test_publisher_can_archive_book(self) -> None:
        """DELETE /publisher/books/{id} moves book to ARCHIVED status."""
        pytest.skip("Requires running DB")

    def test_publisher_can_unarchive_book(self) -> None:
        """POST /publisher/books/{id}/unarchive moves ARCHIVED -> DRAFT."""
        pytest.skip("Requires running DB")

    def test_publisher_can_update_draft_book(self) -> None:
        """PATCH /publisher/books/{id} updates fields for DRAFT book."""
        pytest.skip("Requires running DB")

    def test_publisher_cannot_update_approved_book(self) -> None:
        """PATCH /publisher/books/{id} returns 400 for APPROVED book."""
        pytest.skip("Requires running DB")

    def test_publisher_cannot_see_other_publishers_books(self) -> None:
        """GET /publisher/books/{id} returns 403 for another publisher's book."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminBooksAPI:
    """Admin book moderation endpoints."""

    def test_admin_can_list_all_books(self) -> None:
        """GET /admin/books lists all statuses."""
        pytest.skip("Requires running DB + admin token")

    def test_admin_can_approve_pending_book(self) -> None:
        """POST /admin/books/{id}/approve moves PENDING -> APPROVED."""
        pytest.skip("Requires running DB")

    def test_admin_can_reject_pending_book(self) -> None:
        """POST /admin/books/{id}/reject moves PENDING -> REJECTED with reason."""
        pytest.skip("Requires running DB")

    def test_staff_cannot_approve_without_permission(self) -> None:
        """POST /admin/books/{id}/approve returns 403 for staff without manage_books."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminTagsAndCategoriesAPI:
    """Admin tag and category management."""

    def test_admin_can_approve_pending_tag(self) -> None:
        """POST /admin/tags/{id}/approve sets tag status=APPROVED."""
        pytest.skip("Requires running DB + admin token")

    def test_admin_can_reject_pending_tag(self) -> None:
        """POST /admin/tags/{id}/reject sets tag status=REJECTED."""
        pytest.skip("Requires running DB")

    def test_admin_can_create_category(self) -> None:
        """POST /admin/categories creates a new active category."""
        pytest.skip("Requires running DB")

    def test_admin_can_soft_delete_category(self) -> None:
        """DELETE /admin/categories/{id} sets is_active=False."""
        pytest.skip("Requires running DB")


@pytest.mark.integration
class TestAdminAuthorsAPI:
    """Admin author management endpoints."""

    def test_admin_can_update_author(self) -> None:
        """PATCH /admin/authors/{id} updates author details."""
        pytest.skip("Requires running DB + admin token")

    def test_admin_can_deactivate_author(self) -> None:
        """DELETE /admin/authors/{id} soft-deletes the author."""
        pytest.skip("Requires running DB")

    def test_admin_can_merge_authors(self) -> None:
        """POST /admin/authors/merge reassigns books and soft-deletes duplicates."""
        pytest.skip("Requires running DB")

    def test_merge_with_unknown_primary_returns_404(self) -> None:
        """POST /admin/authors/merge returns 404 if primary UUID not found."""
        pytest.skip("Requires running DB")
