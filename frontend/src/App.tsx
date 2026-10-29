import { lazy, Suspense } from 'react'
import { BrowserRouter, Outlet, Route, Routes } from 'react-router-dom'
import { Navbar } from '@/components/layout/Navbar'
import { Footer } from '@/components/layout/Footer'
import { PublisherSidebar } from '@/components/layout/PublisherSidebar'
import { AdminSidebar } from '@/components/layout/AdminSidebar'
import { AuthGuard } from '@/components/guards/AuthGuard'
import { RoleGuard } from '@/components/guards/RoleGuard'
import { KYCGuard } from '@/components/guards/KYCGuard'
import { Skeleton } from '@/components/ui/Skeleton'

// Public pages
const LandingPage = lazy(() => import('@/pages/LandingPage'))
const BookListingPage = lazy(() => import('@/pages/BookListingPage'))
const BookDetailPage = lazy(() => import('@/pages/BookDetailPage'))
const PublisherPage = lazy(() => import('@/pages/PublisherPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

// Auth pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))
const VerifyEmailPage = lazy(() => import('@/pages/auth/VerifyEmailPage'))
const ForgotPasswordPage = lazy(() => import('@/pages/auth/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/pages/auth/ResetPasswordPage'))

// Reader pages
const ReaderProfilePage = lazy(() => import('@/pages/reader/ProfilePage'))
const LibraryPage = lazy(() => import('@/pages/reader/LibraryPage'))
const NotificationsPage = lazy(() => import('@/pages/reader/NotificationsPage'))

// Publisher pages
const PublisherDashboardPage = lazy(() => import('@/pages/publisher/DashboardPage'))
const PublisherBooksPage = lazy(() => import('@/pages/publisher/BooksPage'))
const UploadBookPage = lazy(() => import('@/pages/publisher/UploadBookPage'))
const KYCPage = lazy(() => import('@/pages/publisher/KYCPage'))
const PublisherProfilePage = lazy(() => import('@/pages/publisher/PublisherProfilePage'))

// Admin pages
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'))
const AdminUsersPage = lazy(() => import('@/pages/admin/AdminUsersPage'))
const AdminKYCPage = lazy(() => import('@/pages/admin/AdminKYCPage'))
const AdminBooksPage = lazy(() => import('@/pages/admin/AdminBooksPage'))
const AdminReviewsPage = lazy(() => import('@/pages/admin/AdminReviewsPage'))
const AdminCategoriesPage = lazy(() => import('@/pages/admin/AdminCategoriesPage'))
const AdminTagsPage = lazy(() => import('@/pages/admin/AdminTagsPage'))
const AdminAuditPage = lazy(() => import('@/pages/admin/AdminAuditPage'))
const AdminNotificationsPage = lazy(() => import('@/pages/admin/AdminNotificationsPage'))

function PageLoader() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <Skeleton className="mb-4 h-8 w-48" />
      <Skeleton className="mb-2 h-4 w-full" />
      <Skeleton className="h-4 w-2/3" />
    </div>
  )
}

function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

function PublisherLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-8 sm:px-6">
        <PublisherSidebar />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  )
}

function AdminLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <div className="mx-auto flex w-full max-w-7xl flex-1 gap-6 px-4 py-8 sm:px-6">
        <AdminSidebar />
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/books" element={<BookListingPage />} />
            <Route path="/books/:bookId" element={<BookDetailPage />} />
            <Route path="/publishers/:userId" element={<PublisherPage />} />

            {/* Auth */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Reader (authenticated) */}
            <Route element={<AuthGuard><Outlet /></AuthGuard>}>
              <Route path="/reader/profile" element={<ReaderProfilePage />} />
              <Route path="/reader/library" element={<LibraryPage />} />
              <Route path="/reader/notifications" element={<NotificationsPage />} />
            </Route>
          </Route>

          {/* Publisher */}
          <Route element={
            <AuthGuard>
              <RoleGuard roles={['publisher']}>
                <PublisherLayout />
              </RoleGuard>
            </AuthGuard>
          }>
            <Route path="/publisher" element={<PublisherDashboardPage />} />
            <Route path="/publisher/profile" element={<PublisherProfilePage />} />
            <Route path="/publisher/kyc" element={<KYCPage />} />
            <Route path="/publisher/books" element={<PublisherBooksPage />} />
            <Route path="/publisher/books/upload" element={
              <KYCGuard><UploadBookPage /></KYCGuard>
            } />
          </Route>

          {/* Admin / Staff */}
          <Route element={
            <AuthGuard>
              <RoleGuard roles={['admin', 'superadmin', 'staff']}>
                <AdminLayout />
              </RoleGuard>
            </AuthGuard>
          }>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/kyc" element={<AdminKYCPage />} />
            <Route path="/admin/books" element={<AdminBooksPage />} />
            <Route path="/admin/reviews" element={<AdminReviewsPage />} />
            <Route path="/admin/categories" element={<AdminCategoriesPage />} />
            <Route path="/admin/tags" element={<AdminTagsPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
            <Route path="/admin/notifications" element={<AdminNotificationsPage />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<PublicLayout />}>
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
