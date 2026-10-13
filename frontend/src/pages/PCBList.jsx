import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPCBs } from "../api/pcbs";
import { apiFetch } from "../api/apiFetch";

export default function PCBList() {

  const [pcbs, setPcbs] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPcb, setSelectedPcb] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const itemsPerPage = 10;

  const loadData = (query = searchQuery, page = currentPage) => {
    setLoading(true);
    setError(null);

    getPCBs(query, page, itemsPerPage)
      .then((data) => {
        setPcbs(data.items || []);
        setTotal(data.total || 0);
        setTotalPages(data.total_pages || 1);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Registry fetch error:", err);
        setError(err.message || "Failed to load PCB registry");
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData(searchQuery, currentPage);
  }, [currentPage]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    setCurrentPage(1);
    loadData(val, 1);
  };

  const getStatusBadge = (status) => {
    const key = (status || "REGISTERED").toUpperCase();

    const map = {
      REGISTERED: {
        label: "Registered",
        bg: "rgba(56, 189, 248, 0.15)",
        text: "var(--app-info)",
        border: "rgba(56, 189, 248, 0.3)"
      },
      IN_DIAGNOSIS: {
        label: "In Diagnosis",
        bg: "rgba(56, 189, 248, 0.15)",
        text: "var(--app-info)",
        border: "rgba(56, 189, 248, 0.3)"
      },
      REPAIRED: {
        label: "Repaired",
        bg: "rgba(52, 211, 153, 0.15)",
        text: "var(--app-success)",
        border: "rgba(52, 211, 153, 0.3)"
      },
      TESTING: {
        label: "Testing",
        bg: "rgba(251, 191, 36, 0.15)",
        text: "var(--app-warning)",
        border: "rgba(251, 191, 36, 0.3)"
      },
      COMPLETED: {
        label: "Completed",
        bg: "rgba(74, 222, 128, 0.15)",
        text: "var(--app-success)",
        border: "rgba(74, 222, 128, 0.3)"
      },
      ARCHIVED: {
        label: "Archived",
        bg: "rgba(251, 146, 60, 0.15)",
        text: "#fb923c",
        border: "rgba(251, 146, 60, 0.3)"
      }
    };

    const style = map[key] || {
      label: key.replace(/_/g, " "),
      bg: "#1e293b",
      text: "var(--app-text-muted)",
      border: "#334155"
    };

    return (
      <span
        style={{
          display: "inline-block",
          padding: "3px 8px",
          borderRadius: "12px",
          fontSize: "0.72rem",
          fontWeight: "600",
          backgroundColor: style.bg,
          color: style.text,
          border: `1px solid ${style.border}`,
          whiteSpace: "nowrap",
          letterSpacing: "0.2px"
        }}
      >
        {style.label}
      </span>
    );
  };

  const startIndex =
    total === 0 ? 0 : (currentPage - 1) * itemsPerPage + 1;

  const endIndex = Math.min(currentPage * itemsPerPage, total);

  return (
    <div
      style={{
        padding: "24px",
        maxWidth: "1400px",
        margin: "0 auto",
        color: "var(--app-text)",
        fontFamily: "Segoe UI, -apple-system, sans-serif"
      }}
    >
      {/* Page Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-end",
          marginBottom: "20px",
          flexWrap: "wrap",
          gap: "16px"
        }}
      >
        <div style={{ textAlign: "left" }}>
          <h1
            style={{
              fontSize: "1.6rem",
              fontWeight: "700",
              margin: "0 0 6px 0",
              color: "var(--app-text)"
            }}
          >
            Registered PCB Units
          </h1>

          <p
            style={{
              margin: 0,
              color: "var(--app-text-muted)",
              fontSize: "0.9rem"
            }}
          >
            Total {total} {total === 1 ? "board" : "boards"} registered in
            laboratory database
          </p>
        </div>

        <div>
          <input
            type="text"
            placeholder="Search reference, serial, status, date, equipment..."
            value={searchQuery}
            onChange={handleSearchChange}
            style={{
              padding: "10px 16px",
              backgroundColor: "var(--app-bg)",
              border: "1px solid var(--app-border)",
              borderRadius: "6px",
              color: "var(--app-text)",
              width: "360px",
              fontSize: "0.9rem",
              outline: "none"
            }}
          />
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "var(--app-error-bg)",
            color: "var(--app-error-text)",
            padding: "14px",
            borderRadius: "8px",
            marginBottom: "16px"
          }}
        >
          Failed to load PCB registry: {error}
        </div>
      )}

      {/* PCB Registry Table */}
      <div
        style={{
          backgroundColor: "var(--app-surface)",
          borderRadius: "8px",
          border: "1px solid var(--app-border)",
          overflowX: "auto",
          boxShadow: "0 4px 12px rgba(0,0,0,0.25)"
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left"
          }}
        >
          <thead>
            <tr
              style={{
                backgroundColor: "var(--app-surface-muted)",
                borderBottom: "1px solid var(--app-border)"
              }}
            >
              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                ID
              </th>

              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                Reference / Serial
              </th>

              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                Customer
              </th>

              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                Equipment
              </th>

              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                Status
              </th>

              <th style={{ padding: "12px 16px", color: "var(--app-text-muted)", fontSize: "0.82rem", textTransform: "uppercase" }}>
                Received Date
              </th>

              <th
                style={{
                  padding: "12px 16px",
                  color: "var(--app-text-muted)",
                  fontSize: "0.82rem",
                  textTransform: "uppercase",
                  textAlign: "center"
                }}
              >
                Actions
              </th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan="7"
                  style={{
                    padding: "36px",
                    textAlign: "center",
                    color: "var(--app-text-muted)"
                  }}
                >
                  Searching PCB records...
                </td>
              </tr>
            ) : pcbs.length === 0 ? (
              <tr>
                <td
                  colSpan="7"
                  style={{
                    padding: "36px",
                    textAlign: "center",
                    color: "var(--app-text-muted)"
                  }}
                >
                  {searchQuery
                    ? `No records matching "${searchQuery}"`
                    : "No PCB records found."}
                </td>
              </tr>
            ) : (
              pcbs.map((pcb) => (
                <tr
                  key={pcb.id}
                  style={{
                    borderBottom: "1px solid var(--app-surface-muted)",
                    transition: "background-color 0.15s ease"
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.backgroundColor = "var(--app-surface-muted)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.backgroundColor = "transparent")
                  }
                >
                  <td
                    style={{
                      padding: "12px 16px",
                      color: "var(--app-text-muted)",
                      fontSize: "0.88rem"
                    }}
                  >
                    #{pcb.id}
                  </td>

                  <td style={{ padding: "12px 16px" }}>
                    <div
                      style={{
                        fontWeight: "600",
                        color: "var(--app-text)",
                        fontSize: "0.9rem"
                      }}
                    >
                      {pcb.internal_reference}
                    </div>

                    {pcb.serial_number && (
                      <div
                        style={{
                          fontSize: "0.76rem",
                          color: "var(--app-info)",
                          marginTop: "2px"
                        }}
                      >
                        SN: {pcb.serial_number}
                      </div>
                    )}
                  </td>

                  <td
                    style={{
                      padding: "12px 16px",
                      color: "var(--app-text)",
                      fontSize: "0.88rem"
                    }}
                  >
                    {pcb.customer_name || (
                      <span style={{ color: "var(--app-text-muted)" }}>-</span>
                    )}
                  </td>

                  <td
                    style={{
                      padding: "12px 16px",
                      color: "var(--app-text)",
                      fontSize: "0.88rem"
                    }}
                  >
                    {pcb.equipment || (
                      <span style={{ color: "var(--app-text-muted)" }}>-</span>
                    )}
                  </td>

                  <td style={{ padding: "12px 16px" }}>
                    <div
                      style={{
                        display: "inline-flex",
                        flexDirection: "column",
                        gap: "4px",
                        alignItems: "flex-start"
                      }}
                    >
                      {getStatusBadge(pcb.status)}

                      {pcb.is_archived && (
                        <span
                          style={{
                            display: "inline-block",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            fontSize: "0.68rem",
                            fontWeight: "700",
                            backgroundColor: "rgba(234, 88, 12, 0.15)",
                            color: "var(--app-warning)",
                            border:
                              "1px solid rgba(234, 88, 12, 0.4)",
                            whiteSpace: "nowrap"
                          }}
                        >
                          ARCHIVED
                        </span>
                      )}
                    </div>
                  </td>

                  <td
                    style={{
                      padding: "12px 16px",
                      color: "var(--app-text-muted)",
                      fontSize: "0.85rem",
                      whiteSpace: "nowrap"
                    }}
                  >
                    {pcb.date_received || "-"}
                  </td>

                  {/* Actions */}
                  <td
                    style={{
                      padding: "12px 16px",
                      textAlign: "center"
                    }}
                  >
                    <Link
                      to={`/pcb/${pcb.id}`}
                      style={{
                        padding: "5px 12px",
                        backgroundColor: "var(--app-button-success)",
                        color: "#ffffff",
                        textDecoration: "none",
                        borderRadius: "5px",
                        fontSize: "0.82rem",
                        fontWeight: "600",
                        display: "inline-block",
                        whiteSpace: "nowrap"
                      }}
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "14px 20px",
              borderTop: "1px solid var(--app-border)",
              backgroundColor: "var(--app-surface)",
              fontSize: "0.86rem",
              color: "var(--app-text-muted)",
              flexWrap: "wrap",
              gap: "12px"
            }}
          >
            <div>
              Showing{" "}
              <strong style={{ color: "var(--app-text)" }}>{startIndex}</strong> to{" "}
              <strong style={{ color: "var(--app-text)" }}>{endIndex}</strong> of{" "}
              <strong style={{ color: "var(--app-text)" }}>{total}</strong> units
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px"
              }}
            >
              <button
                onClick={() =>
                  setCurrentPage((p) => Math.max(1, p - 1))
                }
                disabled={currentPage === 1}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  border: "1px solid var(--app-border)",
                  backgroundColor:
                    currentPage === 1 ? "var(--app-bg)" : "var(--app-surface-muted)",
                  color:
                    currentPage === 1 ? "#484f58" : "var(--app-text)",
                  cursor:
                    currentPage === 1 ? "not-allowed" : "pointer",
                  fontWeight: "600",
                  fontSize: "0.82rem"
                }}
              >
                Previous
              </button>

              <span
                style={{
                  margin: "0 6px",
                  color: "var(--app-text)"
                }}
              >
                Page <strong>{currentPage}</strong> of{" "}
                <strong>{totalPages}</strong>
              </span>

              <button
                onClick={() =>
                  setCurrentPage((p) =>
                    Math.min(totalPages, p + 1)
                  )
                }
                disabled={currentPage >= totalPages}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  border: "1px solid var(--app-border)",
                  backgroundColor:
                    currentPage >= totalPages
                      ? "var(--app-bg)"
                      : "var(--app-surface-muted)",
                  color:
                    currentPage >= totalPages
                      ? "#484f58"
                      : "var(--app-text)",
                  cursor:
                    currentPage >= totalPages
                      ? "not-allowed"
                      : "pointer",
                  fontWeight: "600",
                  fontSize: "0.82rem"
                }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
