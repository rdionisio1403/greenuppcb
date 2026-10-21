import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import PCBList from "./pages/PCBList";
import PCBCreate from "./pages/PCBCreate";
import PCBDetail from "./pages/PCBDetail";
import Dashboard from "./pages/Dashboard";
import UserManagement from "./pages/UserManagement";
import AccountSettings from "./pages/AccountSettings";
import CustomerManagement from "./pages/CustomerManagement";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <div className="app-route-content">
          <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<PCBList />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="new" element={<PCBCreate />} />
            <Route path="pcb/:id" element={<PCBDetail />} />
            <Route path="user-management" element={<UserManagement />} />
            <Route path="customer-management" element={<CustomerManagement />} />
            <Route path="account-settings" element={<AccountSettings />} />
            <Route path="change-password" element={<AccountSettings />} />
          </Route>
        </Route>
          </Routes>
        </div>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
