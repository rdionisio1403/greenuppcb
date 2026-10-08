import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import PCBList from "./pages/PCBList";
import PCBCreate from "./pages/PCBCreate";
import PCBDetail from "./pages/PCBDetail";
import Dashboard from "./pages/Dashboard";
import UserManagement from "./pages/UserManagement";
import ChangePassword from "./pages/ChangePassword";
import CustomerManagement from "./pages/CustomerManagement";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<PCBList />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="new" element={<PCBCreate />} />
            <Route path="pcb/:id" element={<PCBDetail />} />
            <Route path="user-management" element={<UserManagement />} />
            <Route path="customer-management" element={<CustomerManagement />} />
            <Route path="change-password" element={<ChangePassword />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
