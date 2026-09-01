import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import PCBList from "./pages/PCBList";
import PCBCreate from "./pages/PCBCreate";
import PCBDetail from "./pages/PCBDetail";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PCBList />} />
          <Route path="new" element={<PCBCreate />} />
          <Route path="pcbs/:id" element={<PCBDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
