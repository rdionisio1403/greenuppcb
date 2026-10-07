import { useEffect, useState } from "react";
import { createCustomer, getCustomers } from "../api/customers";

const inputStyle = {
  width: "100%",
  padding: "10px 12px",
  border: "1px solid #475569",
  borderRadius: "6px",
  background: "#0f172a",
  color: "#e2e8f0",
  boxSizing: "border-box",
};

export default function CustomerManagement() {
  const [customers, setCustomers] = useState([]);
  const [formData, setFormData] = useState({
    name: "",
    contact_info: "",
    reference: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadCustomers = async () => {
    try {
      setError("");
      const data = await getCustomers();
      setCustomers(data);
    } catch (err) {
      setError(err.message || "Failed to load customers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!formData.name.trim()) {
      setError("Customer name is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      await createCustomer({
        name: formData.name.trim(),
        contact_info: formData.contact_info.trim() || null,
        reference: formData.reference.trim() || null,
      });

      setFormData({
        name: "",
        contact_info: "",
        reference: "",
      });

      setSuccess("Customer created successfully.");
      await loadCustomers();
    } catch (err) {
      setError(err.message || "Failed to create customer.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div style={{ textAlign: "left" }}>
        <h1
          style={{
            color: "#e2e8f0",
            margin: "0 0 8px 0",
            fontSize: "1.6rem",
            fontWeight: "700",
            textAlign: "left",
          }}
        >
          Customer Management
        </h1>

        <p
          style={{
            color: "#94a3b8",
            margin: 0,
            marginBottom: "24px",
            fontSize: "0.9rem",
            textAlign: "left",
          }}
        >
          Create and view customers used by PCB records.
        </p>
      </div>

      <section
        style={{
          background: "#1e293b",
          padding: "24px",
          borderRadius: "10px",
          marginBottom: "30px",
        }}
      >
        <h2 style={{ color: "#e2e8f0", marginTop: 0 }}>
          Add Customer
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label
              htmlFor="customer-name"
              style={{
                display: "block",
                color: "#cbd5e1",
                marginBottom: "6px",
                fontWeight: "600",
              }}
            >
              Customer Name *
            </label>
            <input
              id="customer-name"
              type="text"
              required
              maxLength={200}
              value={formData.name}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  name: event.target.value,
                })
              }
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label
              htmlFor="customer-contact"
              style={{
                display: "block",
                color: "#cbd5e1",
                marginBottom: "6px",
                fontWeight: "600",
              }}
            >
              Contact Information
            </label>
            <input
              id="customer-contact"
              type="text"
              maxLength={200}
              value={formData.contact_info}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  contact_info: event.target.value,
                })
              }
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label
              htmlFor="customer-reference"
              style={{
                display: "block",
                color: "#cbd5e1",
                marginBottom: "6px",
                fontWeight: "600",
              }}
            >
              Reference
            </label>
            <input
              id="customer-reference"
              type="text"
              maxLength={100}
              value={formData.reference}
              onChange={(event) =>
                setFormData({
                  ...formData,
                  reference: event.target.value,
                })
              }
              style={inputStyle}
            />
          </div>

          {error && (
            <p style={{ color: "#f87171", marginBottom: "12px" }}>
              {error}
            </p>
          )}

          {success && (
            <p style={{ color: "#4ade80", marginBottom: "12px" }}>
              {success}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: "10px 18px",
              background: saving ? "#475569" : "#16a34a",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontWeight: "600",
              cursor: saving ? "not-allowed" : "pointer",
            }}
          >
            {saving ? "Creating..." : "Create Customer"}
          </button>
        </form>
      </section>

      <section
        style={{
          background: "#1e293b",
          padding: "24px",
          borderRadius: "10px",
        }}
      >
        <h2 style={{ color: "#e2e8f0", marginTop: 0 }}>
          Customers
        </h2>

        {loading ? (
          <p style={{ color: "#94a3b8" }}>Loading customers...</p>
        ) : customers.length === 0 ? (
          <p style={{ color: "#94a3b8" }}>No customers found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                color: "#e2e8f0",
              }}
            >
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid #475569" }}>
                    ID
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid #475569" }}>
                    Name
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid #475569" }}>
                    Contact Information
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid #475569" }}>
                    Reference
                  </th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr key={customer.id}>
                    <td style={{ padding: "10px", borderBottom: "1px solid #334155" }}>
                      {customer.id}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid #334155" }}>
                      {customer.name}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid #334155" }}>
                      {customer.contact_info || "—"}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid #334155" }}>
                      {customer.reference || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
