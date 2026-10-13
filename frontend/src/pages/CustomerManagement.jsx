import { useEffect, useState } from "react";
import { createCustomer, getCustomers, updateCustomer, deleteCustomer } from "../api/customers";

const inputStyle = {
  width: "100%",
  padding: "10px 12px",
  border: "1px solid var(--app-border)",
  borderRadius: "6px",
  background: "var(--app-input-bg)",
  color: "var(--app-text)",
  boxSizing: "border-box",
};

export default function CustomerManagement() {
  const [customers, setCustomers] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const [formData, setFormData] = useState({
    name: "",
    contact_info: "",
    reference: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editingCustomer, setEditingCustomer] = useState(null);
  const [customerToDelete, setCustomerToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadCustomers = async () => {
    try {
      setError("");
      const data = await getCustomers();
      setCustomers(data);
      setCurrentPage(1);
    } catch (err) {
      setError(err.message || "Failed to load customers.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const totalPages = Math.max(1, Math.ceil(customers.length / pageSize));
  const sortedCustomers = [...customers].sort((a, b) => a.id - b.id);
  const pageCustomers = sortedCustomers.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);


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

      const payload = {
        name: formData.name.trim(),
        contact_info: formData.contact_info.trim() || null,
        reference: formData.reference.trim() || null,
      };

      if (editingCustomer) {
        await updateCustomer(editingCustomer.id, payload);
      } else {
        await createCustomer(payload);
      }

      setFormData({
        name: "",
        contact_info: "",
        reference: "",
      });

      setSuccess(
        editingCustomer
          ? "Customer updated successfully."
          : "Customer created successfully."
      );
      setEditingCustomer(null);
      await loadCustomers();
    } catch (err) {
      setError(err.message || (editingCustomer
        ? "Failed to update customer."
        : "Failed to create customer."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div style={{ textAlign: "left" }}>
        <h1
          style={{
            color: "var(--app-text)",
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
            color: "var(--app-text-muted)",
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
          background: "var(--app-surface)",
          padding: "24px",
          borderRadius: "10px",
          marginBottom: "30px",
        }}
      >
        <h2 style={{ color: "var(--app-text)", marginTop: 0 }}>
          {editingCustomer ? "Edit Customer" : "Add Customer"}
        </h2>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "16px" }}>
            <label
              htmlFor="customer-name"
              style={{
                display: "block",
                color: "var(--app-text)",
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
                color: "var(--app-text)",
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
                color: "var(--app-text)",
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
            <p style={{ color: "var(--app-danger)", marginBottom: "12px" }}>
              {error}
            </p>
          )}

          {success && (
            <p style={{ color: "var(--app-success)", marginBottom: "12px" }}>
              {success}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            style={{
              padding: "10px 18px",
              background: saving ? "var(--app-border)" : "var(--app-button-success)",
              color: "#ffffff",
              border: "none",
              borderRadius: "6px",
              fontWeight: "600",
              cursor: saving ? "not-allowed" : "pointer",
            }}
          >
            {saving
              ? (editingCustomer ? "Saving..." : "Creating...")
              : (editingCustomer ? "Save Changes" : "Create Customer")}
          </button>
          {editingCustomer && (
            <button
              type="button"
              disabled={saving}
              onClick={() => {
                setEditingCustomer(null);
                setFormData({ name: "", contact_info: "", reference: "" });
                setError("");
                setSuccess("");
              }}
              style={{
                marginLeft: "10px",
                padding: "10px 18px",
                background: "transparent",
                color: "var(--app-text)",
                border: "1px solid var(--app-border)",
                borderRadius: "6px",
                fontWeight: "600",
                cursor: "pointer",
              }}
            >
              Cancel Edit
            </button>
          )}
        </form>
      </section>

      <section
        style={{
          background: "var(--app-surface)",
          padding: "24px",
          border: "1px solid var(--app-border)",
          borderRadius: "12px",
          marginBottom: "30px",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.05)",
        }}
      >
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "16px",
        }}>
          <h2 style={{ color: "var(--app-text)", margin: 0 }}>
            Customers
          </h2>
          <span style={{
            color: "var(--app-text-muted)",
            fontSize: "0.9rem",
          }}>
            {customers.length} total
          </span>
        </div>

        {loading ? (
          <p style={{ color: "var(--app-text-muted)" }}>Loading customers...</p>
        ) : customers.length === 0 ? (
          <p style={{ color: "var(--app-text-muted)" }}>No customers found.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                color: "var(--app-text)",
              }}
            >
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid var(--app-border)" }}>
                    ID
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid var(--app-border)" }}>
                    Name
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid var(--app-border)" }}>
                    Contact Information
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid var(--app-border)" }}>
                    Reference
                  </th>
                  <th style={{ textAlign: "left", padding: "10px", borderBottom: "1px solid var(--app-border)" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {pageCustomers.map((customer, index) => (
                  <tr key={customer.id}>
                    <td style={{ padding: "10px", borderBottom: "1px solid var(--app-surface-muted)" }}>
                      {(currentPage - 1) * pageSize + index + 1}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid var(--app-surface-muted)" }}>
                      {customer.name}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid var(--app-surface-muted)" }}>
                      {customer.contact_info || "—"}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid var(--app-surface-muted)" }}>
                      {customer.reference || "—"}
                    </td>
                    <td style={{ padding: "10px", borderBottom: "1px solid var(--app-surface-muted)", whiteSpace: "nowrap" }}>
                      <button
                        type="button"
                        onClick={() => {
                          setEditingCustomer(customer);
                          setFormData({
                            name: customer.name || "",
                            contact_info: customer.contact_info || "",
                            reference: customer.reference || "",
                          });
                          setError("");
                          setSuccess("");
                          window.scrollTo({ top: 0, behavior: "smooth" });
                        }}
                        style={{
                          padding: "7px 11px",
                          marginRight: "8px",
                          background: "#0284c7",
                          color: "#fff",
                          border: "none",
                          borderRadius: "5px",
                          cursor: "pointer",
                          fontWeight: "600",
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setError("");
                          setSuccess("");
                          setCustomerToDelete(customer);
                        }}
                        style={{
                          padding: "7px 11px",
                          background: "#dc2626",
                          color: "#fff",
                          border: "none",
                          borderRadius: "5px",
                          cursor: "pointer",
                          fontWeight: "600",
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && customers.length > 0 && (
          <div style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "12px",
            flexWrap: "wrap",
            marginTop: "20px",
            paddingTop: "16px",
            borderTop: "1px solid var(--app-border)",
          }}>
            <span style={{ color: "var(--app-text-muted)", fontSize: "0.9rem" }}>
              Showing {Math.min((currentPage - 1) * pageSize + 1, customers.length)}
              {"–"}
              {Math.min(currentPage * pageSize, customers.length)}
              {" of "}{customers.length}
            </span>

            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              flexWrap: "wrap",
            }}>
              <button
                type="button"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                style={{
                  padding: "8px 12px",
                  border: "1px solid var(--app-border)",
                  borderRadius: "6px",
                  background: "var(--app-surface)",
                  color: "var(--app-text)",
                  cursor: currentPage === 1 ? "not-allowed" : "pointer",
                  opacity: currentPage === 1 ? 0.5 : 1,
                }}
              >
                Previous
              </button>

              {Array.from({ length: totalPages }, (_, index) => index + 1).map((page) => (
                <button
                  key={page}
                  type="button"
                  aria-current={currentPage === page ? "page" : undefined}
                  onClick={() => setCurrentPage(page)}
                  style={{
                    minWidth: "36px",
                    padding: "8px 10px",
                    border: "1px solid var(--app-border)",
                    borderRadius: "6px",
                    background: currentPage === page ? "#0284c7" : "var(--app-surface)",
                    color: currentPage === page ? "#ffffff" : "var(--app-text)",
                    cursor: "pointer",
                    fontWeight: currentPage === page ? "700" : "500",
                  }}
                >
                  {page}
                </button>
              ))}

              <button
                type="button"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                style={{
                  padding: "8px 12px",
                  border: "1px solid var(--app-border)",
                  borderRadius: "6px",
                  background: "var(--app-surface)",
                  color: "var(--app-text)",
                  cursor: currentPage === totalPages ? "not-allowed" : "pointer",
                  opacity: currentPage === totalPages ? 0.5 : 1,
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </section>

      {customerToDelete && (
        <div
          role="presentation"
          onClick={(event) => {
            if (event.target === event.currentTarget && !deleting) {
              setCustomerToDelete(null);
            }
          }}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 2000,
            background: "rgba(15, 23, 42, 0.60)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="delete-customer-title"
            style={{
              width: "100%",
              maxWidth: "440px",
              background: "var(--app-surface)",
              color: "var(--app-text)",
              border: "1px solid var(--app-border)",
              borderRadius: "12px",
              padding: "24px",
              boxShadow: "0 20px 60px rgba(0,0,0,0.25)",
            }}
          >
            <h2 id="delete-customer-title" style={{ marginTop: 0 }}>
              Delete Customer
            </h2>
            <p>
              Are you sure you want to delete{" "}
              <strong>{customerToDelete.name}</strong>?
            </p>
            <p style={{ color: "var(--app-text-muted)", fontSize: "0.9rem" }}>
              Customers linked to PCB records cannot be deleted, so historical
              data remains protected.
            </p>
            {error && (
              <p style={{ color: "var(--app-danger)", marginBottom: "12px" }}>
                {error}
              </p>
            )}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                type="button"
                disabled={deleting}
                onClick={() => setCustomerToDelete(null)}
                style={{
                  padding: "10px 16px",
                  background: "transparent",
                  color: "var(--app-text)",
                  border: "1px solid var(--app-border)",
                  borderRadius: "6px",
                  cursor: deleting ? "not-allowed" : "pointer",
                  fontWeight: "600",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={async () => {
                  try {
                    setDeleting(true);
                    setError("");
                    await deleteCustomer(customerToDelete.id);
                    setCustomerToDelete(null);
                    setSuccess("Customer deleted successfully.");
                    await loadCustomers();
                  } catch (err) {
                    setError(err.message || "Failed to delete customer.");
                  } finally {
                    setDeleting(false);
                  }
                }}
                style={{
                  padding: "10px 16px",
                  background: "#dc2626",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  cursor: deleting ? "not-allowed" : "pointer",
                  fontWeight: "600",
                  opacity: deleting ? 0.7 : 1,
                }}
              >
                {deleting ? "Deleting..." : "Delete Customer"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
