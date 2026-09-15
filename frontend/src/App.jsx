import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import PCBList from "./pages/PCBList";
import PCBCreate from "./pages/PCBCreate";
import PCBDetail from "./pages/PCBDetail";
import Dashboard from "./pages/Dashboard";

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
            <Route path="pcbs/:id" element={<PCBDetail />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
