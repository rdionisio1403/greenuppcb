import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { createPCB } from "../api/pcbs";
import { getCustomers, createCustomer } from "../api/customers";

export default function PCBCreate() {
  const navigate = useNavigate();
  const location = useLocation();

  const reintakeData = location.state?.reintake || null;

  const [formData, setFormData] = useState({
    internal_reference: "",
    customer_id: "",
    equipment: "",
    manufacturer: "",
    pcb_model: "",
    serial_number: "",
    date_received: new Date().toISOString().split("T")[0],
    failure_description: "",
  });
  const [customers, setCustomers] = useState([]);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCustomerForm, setShowCustomerForm] = useState(false);
  const [customerSaving, setCustomerSaving] = useState(false);
  const [customerForm, setCustomerForm] = useState({
    name: "",
    contact_info: "",
    reference: "",
  });

  useEffect(() => {
    async function loadCustomers() {
      try {
        const data = await getCustomers();
        setCustomers(data);
      } catch (err) {
        setError(err.message || "Failed to load customers");
      }
    }

    loadCustomers();
  }, []);

  useEffect(() => {
    if (reintakeData) {
      const serial = reintakeData.serial_number || "";
      const randomSuffix = Math.floor(1000 + Math.random() * 9000);
      const generatedRef = serial ? `RE-${serial}-${randomSuffix}` : `RE-PCB-${randomSuffix}`;

      setFormData((prev) => ({
        ...prev,
        internal_reference: generatedRef,
        customer_id: reintakeData.customer_id || "",
        equipment: reintakeData.equipment || "",
        manufacturer: reintakeData.manufacturer || "",
        pcb_model: reintakeData.pcb_model || "",
        serial_number: serial,
        failure_description: "",
      }));
    }
  }, [reintakeData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await createPCB(formData);
      navigate("/");
    } catch (err) {
      setError(err.message || "Failed to register PCB");
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputStyle = {
    padding: "10px 12px",
    borderRadius: "6px",
    border: "1px solid #3f444e",
    backgroundColor: "#1e222b",
    color: "#f0f2f5",
    fontSize: "0.95rem"
  };

  return (
    <div style={{ maxWidth: "560px", margin: "0 auto", padding: "20px 0" }}>
      <h3 style={{ fontSize: "1.3rem", marginBottom: "18px", textAlign: "center", color: "#e2e8f0" }}>
        {reintakeData ? "🔁 Re-Intake PCB Entry (New Service Cycle)" : "Register New PCB Entry"}
      </h3>

      {reintakeData && (
        <div style={{ background: "rgba(234, 88, 12, 0.15)", border: "1px solid #ea580c", color: "#fdba74", padding: "10px 14px", borderRadius: "6px", marginBottom: "15px", fontSize: "0.85rem" }}>
          Re-intake initiated for serial <strong>{reintakeData.serial_number}</strong>. Reference format generated to prevent collision.
        </div>
      )}

      {error && (
        <div style={{ background: "#7f1d1d", color: "#fecaca", padding: "10px 14px", borderRadius: "6px", marginBottom: "15px", fontSize: "0.9rem" }}>
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        onKeyDown={(e) => {
          if (e.key !== "Enter") {
            return;
          }

          e.preventDefault();

          const form = e.currentTarget;
          const focusable = Array.from(
            form.querySelectorAll(
              'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
            )
          );

          const currentIndex = focusable.indexOf(e.target);

          if (currentIndex >= 0 && currentIndex < focusable.length - 1) {
            focusable[currentIndex + 1].focus();
          }
        }}
        style={{ display: "flex", flexDirection: "column", gap: "12px" }}
      >
        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Internal Reference *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Internal Reference (e.g. PCB-2026-001)"
            value={formData.internal_reference}
            onChange={(e) => setFormData({ ...formData, internal_reference: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Serial Number *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Serial Number (e.g. SN-987654)"
            value={formData.serial_number}
            onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>
            Customer *
          </label>

          <select
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            value={formData.customer_id}
            onChange={(e) =>
              setFormData({
                ...formData,
                customer_id: e.target.value ? Number(e.target.value) : "",
              })
            }
          >
            <option value="">Select Customer</option>
            {customers.map((customer) => (
              <option key={customer.id} value={customer.id}>
                {customer.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={() => {
              setShowCustomerForm((current) => !current);
              setError(null);
            }}
            style={{
              marginTop: "8px",
              padding: "7px 11px",
              background: "transparent",
              color: "#93c5fd",
              border: "1px solid #475569",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            {showCustomerForm ? "Cancel" : "+ Add New Customer"}
          </button>

          {showCustomerForm && (
            <div
              style={{
                marginTop: "12px",
                padding: "14px",
                border: "1px solid #334155",
                borderRadius: "8px",
                background: "#151a23",
              }}
            >
              <div
                style={{
                  color: "#e2e8f0",
                  fontSize: "0.9rem",
                  fontWeight: "600",
                  marginBottom: "12px",
                }}
              >
                Add New Customer
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <input
                  required
                  style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
                  placeholder="Customer Name *"
                  value={customerForm.name}
                  onChange={(e) =>
                    setCustomerForm({
                      ...customerForm,
                      name: e.target.value,
                    })
                  }
                />

                <input
                  style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
                  placeholder="Contact Info"
                  value={customerForm.contact_info}
                  onChange={(e) =>
                    setCustomerForm({
                      ...customerForm,
                      contact_info: e.target.value,
                    })
                  }
                />

                <input
                  style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
                  placeholder="Reference"
                  value={customerForm.reference}
                  onChange={(e) =>
                    setCustomerForm({
                      ...customerForm,
                      reference: e.target.value,
                    })
                  }
                />

                <button
                  type="button"
                  disabled={customerSaving || !customerForm.name.trim()}
                  onClick={async () => {
                    setCustomerSaving(true);
                    setError(null);

                    try {
                      const newCustomer = await createCustomer({
                        name: customerForm.name.trim(),
                        contact_info: customerForm.contact_info.trim() || null,
                        reference: customerForm.reference.trim() || null,
                      });

                      setCustomers((current) => [...current, newCustomer]);

                      setFormData((current) => ({
                        ...current,
                        customer_id: newCustomer.id,
                      }));

                      setCustomerForm({
                        name: "",
                        contact_info: "",
                        reference: "",
                      });

                      setShowCustomerForm(false);
                    } catch (err) {
                      setError(err.message || "Failed to create customer");
                    } finally {
                      setCustomerSaving(false);
                    }
                  }}
                  style={{
                    padding: "9px 12px",
                    background:
                      customerSaving || !customerForm.name.trim()
                        ? "#334155"
                        : "#2563eb",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    cursor:
                      customerSaving || !customerForm.name.trim()
                        ? "not-allowed"
                        : "pointer",
                    fontWeight: "600",
                  }}
                >
                  {customerSaving ? "Creating..." : "Create Customer"}
                </button>
              </div>
            </div>
          )}
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Equipment *</label>
          <input
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Equipment"
            value={formData.equipment}
            onChange={(e) => setFormData({ ...formData, equipment: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Manufacturer</label>
          <input
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="Manufacturer"
            value={formData.manufacturer}
            onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>PCB Model</label>
          <input
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            placeholder="PCB Model"
            value={formData.pcb_model}
            onChange={(e) => setFormData({ ...formData, pcb_model: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Received Date *</label>
          <input
            type="date"
            required
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box" }}
            value={formData.date_received}
            onChange={(e) => setFormData({ ...formData, date_received: e.target.value })}
          />
        </div>

        <div>
          <label style={{ fontSize: "0.8rem", color: "#8b949e", display: "block", marginBottom: "4px" }}>Failure Description</label>
          <textarea
            style={{ ...inputStyle, width: "100%", boxSizing: "border-box", minHeight: "80px", fontFamily: "inherit" }}
            placeholder="Reported Failure / Incoming Fault"
            value={formData.failure_description}
            onChange={(e) => setFormData({ ...formData, failure_description: e.target.value })}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          style={{
            padding: "10px",
            backgroundColor: isSubmitting ? "#166534" : "#22c55e",
            color: "#ffffff",
            border: "none",
            borderRadius: "6px",
            fontWeight: "700",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            marginTop: "10px"
          }}
        >
          {isSubmitting ? "Registering..." : reintakeData ? "Confirm Re-Intake Entry" : "Register PCB"}
        </button>
      </form>
    </div>
  );
}
