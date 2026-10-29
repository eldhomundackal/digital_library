import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div>
            <span className="font-heading text-lg font-bold text-primary">Libraflow</span>
            <p className="mt-2 text-xs text-gray-500">
              Discover and download quality digital books.
            </p>
          </div>
          <div>
            <h4 className="mb-3 text-sm font-semibold text-gray-800">Explore</h4>
            <ul className="space-y-2 text-sm text-gray-500">
              <li><Link to="/books" className="hover:text-primary">Browse Books</Link></li>
              <li><Link to="/books?sort=new" className="hover:text-primary">New Arrivals</Link></li>
              <li><Link to="/books?sort=popular" className="hover:text-primary">Popular</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="mb-3 text-sm font-semibold text-gray-800">Publish</h4>
            <ul className="space-y-2 text-sm text-gray-500">
              <li><Link to="/register?role=publisher" className="hover:text-primary">Become a Publisher</Link></li>
              <li><Link to="/publisher" className="hover:text-primary">Publisher Dashboard</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="mb-3 text-sm font-semibold text-gray-800">Account</h4>
            <ul className="space-y-2 text-sm text-gray-500">
              <li><Link to="/login" className="hover:text-primary">Sign In</Link></li>
              <li><Link to="/register" className="hover:text-primary">Register</Link></li>
              <li><Link to="/reader/library" className="hover:text-primary">My Library</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-8 border-t border-gray-100 pt-6 text-center text-xs text-gray-400">
          &copy; {new Date().getFullYear()} Libraflow. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
