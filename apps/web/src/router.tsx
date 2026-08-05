import { Navigate, createBrowserRouter } from 'react-router-dom'
import App from './App'
import DiffPage from './pages/DiffPage'
import EvalRunsPage from './pages/EvalRunsPage'
import TestCasePage from './pages/TestCasePage'
import TraceDetailPage from './pages/TraceDetailPage'
import TracesPage from './pages/TracesPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/traces" replace /> },
      { path: 'traces', element: <TracesPage /> },
      { path: 'traces/:id', element: <TraceDetailPage /> },
      { path: 'test-cases', element: <TestCasePage /> },
      { path: 'eval-runs', element: <EvalRunsPage /> },
      { path: 'diff', element: <DiffPage /> },
    ],
  },
])
