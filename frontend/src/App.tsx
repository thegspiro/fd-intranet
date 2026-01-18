import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import MemberListPage from './pages/MemberListPage'
import SettingsPage from './pages/SettingsPage'
import MembersAdminPage from './pages/MembersAdminPage'
import RoleManagementPage from './pages/RoleManagementPage'

function Navigation() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
      ? 'border-blue-500 text-gray-900'
      : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
  }

  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">The Logbook</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                to="/"
                className={`${isActive('/')} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                Members
              </Link>
              <Link
                to="/admin/members"
                className={`${isActive('/admin/members')} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                Members Admin
              </Link>
              <Link
                to="/admin/roles"
                className={`${isActive('/admin/roles')} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                Role Management
              </Link>
              <Link
                to="/settings"
                className={`${isActive('/settings')} inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
              >
                Settings
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <Routes>
          <Route path="/" element={<MemberListPage />} />
          <Route path="/admin/members" element={<MembersAdminPage />} />
          <Route path="/admin/roles" element={<RoleManagementPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
