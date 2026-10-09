export default function Footer() {
  return (
    <footer className="contacts-footer">
      <div className="contacts-footer-content">
        <h2 className="contacts-footer-title">Contacts</h2>

        <div className="contacts-footer-grid">
          <section className="contacts-footer-item">
            <h3>Address</h3>
            <address>
              Av. Pedro Álvares Cabral, nº 12
              <br />
              6000-084 Castelo Branco
            </address>
          </section>

          <section className="contacts-footer-item">
            <h3>Phone</h3>
            <p>
              <a href="tel:+351272339600">(+351) 272 339 600</a>
            </p>
            <p className="contacts-footer-note">
              Call to the national landline network
            </p>
            <p className="contacts-footer-mobile">
              <a href="tel:+351965956971">(+351) 965 956 971</a>
            </p>
            <p className="contacts-footer-note">
              Call to the national mobile network
            </p>
          </section>

          <section className="contacts-footer-item">
            <h3>Email</h3>
            <a
              href="mailto:ipcb@ipcb.pt"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Compose an email to ipcb@ipcb.pt"
            >
              ipcb@ipcb.pt
            </a>
          </section>
          <section className="contacts-footer-item">
            <h3>Connect with us</h3>
            <a
              href="https://www.linkedin.com/company/e-novation-lab-greenuppcb/posts/?feedView=all"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Visit E-Novation Lab GreenUpPCB on LinkedIn"
            >
              <svg
                className="linkedin-icon"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                role="img"
                aria-label="LinkedIn"
              >
                <path
                  fill="currentColor"
                  d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.35V9h3.414v1.561h.049c.476-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.124 2.062 2.062 0 0 1 0 4.124zM7.119 20.452H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"
                />
              </svg>
            </a>
          </section>
        </div>

        <div className="contacts-footer-bottom">
          IPCB · Instituto Politécnico de Castelo Branco
        </div>
      </div>
    </footer>
  );
}
