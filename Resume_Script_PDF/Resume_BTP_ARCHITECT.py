from fpdf import FPDF

# Function to replace Unicode characters with ASCII equivalents
def clean_text(text):
    return text.replace("–", "-").replace("—", "-") \
               .replace("’", "'").replace("“", '"').replace("”", '"')

class PDFResume(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, clean_text("Koti Davuluri"), ln=1, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, clean_text("kotesward2569@gmail.com | +1 (602) 617-6185"), ln=1, align="C")
        self.cell(0, 6, clean_text("Scottsdale, Arizona | Open to Relocate"), ln=1, align="C")
        self.ln(5)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 51, 102)
        self.cell(0, 6, clean_text(title), ln=1)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def add_paragraph(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, clean_text(text))
        self.ln(2)

    def add_table(self, data, col_widths=None):
        self.set_font("Helvetica", "", 10)
        line_height = 5
        for row in data:
            x_start = self.get_x()
            y_start = self.get_y()
            max_height = 0

            # Calculate max height of the row
            for i, cell in enumerate(row):
                n_lines = cell.count('\n') + 1
                max_height = max(max_height, n_lines * line_height)

            # Draw each cell
            for i, cell in enumerate(row):
                width = col_widths[i] if col_widths else 50
                self.multi_cell(width, line_height, clean_text(cell), border=1)
                x_new = x_start + sum(col_widths[:i+1]) if col_widths else x_start + width
                self.set_xy(x_new, y_start)

            # Move to next row
            self.set_xy(x_start, y_start + max_height)

# Create PDF
pdf = PDFResume()
pdf.add_page()

# Professional Summary
pdf.section_title("Professional Summary")
pdf.add_paragraph(
    "SAP Basis Architect and SAP Business Technology Platform (BTP) Administrator with over 19 years "
    "of comprehensive experience leading SAP Basis operations, architectural design, cloud integration, "
    "and hybrid SAP landscapes across multinational enterprises. Proven expertise in SAP S/4HANA migrations, "
    "SAP RISE brownfield transformation, and SAP BTP platform management to deliver enterprise cloud extensions "
    "and application modernization."
)

# Core Competencies
pdf.section_title("Core Competencies")
skills_data = [
    ["SAP Basis Architecture & Leadership", "SAP System Installation, Upgrades, Kernel Patches, RISE Migration Lead, Transport Strategy, HA/DR Planning, SAP Solution Manager Monitoring"],
    ["SAP BTP Platform Administration", "Subaccount & Entitlement Configuration, Cloud Connector Setup, Destination Management, User & Role Administration, Trust & Certificate Management, Transport Management"],
    ["Security & Integration", "Azure Entra ID & OKTA Integration, SAML & JWT Authentication, HTTPS Secure Communication, RBAC, Hybrid Cloud Security Frameworks"],
    ["Application Development & Extensions", "SAP CAP Model (Java/Node.js), SAP Fiori/UI5 Customizations, SAP Build Work Zone, OData APIs, CI/CD Pipelines, ABAP Environment Setup (basic)"],
    ["Databases & OS", "SAP HANA, DB2 (HADR, GeoCluster), Oracle 11g/11c, MSSQL; Linux (SUSE/Red Hat), Windows, AIX"],
    ["Tools & Utilities", "SUM, SWPM, SAP HANA Studio, PuTTY, WinSCP, Tivoli, LSMW, Automation & Scripting"]
]
pdf.add_table(skills_data, col_widths=[60, 130])

# Professional Experience
pdf.section_title("Professional Experience")
experience_texts = [
    ("Timken Company - Senior SAP Basis Architect & SAP BTP Administrator", 
     "Nov 2013 - Aug 2025 | CANTON, OHIO (Hybrid/Remote)",
     [
        "Led SAP Basis architecture and BTP platform services supporting SAP RISE transformation and hybrid cloud integration.",
        "Executed installations, upgrades, kernel patches, and brownfield migrations from ECC to S/4HANA with zero critical downtime.",
        "Managed BTP subaccounts, entitlements, destinations, Cloud Connector setup, and secure trust configurations.",
        "Integrated BTP authentication with Azure Entra ID and OKTA, enabling seamless SSO using SAML/JWT.",
        "Led transport strategy, dual-maintenance, and automated migration processes.",
        "Designed high availability and DR solutions for SAP HANA using Pacemaker clusters and replication.",
        "Authored operational playbooks, compliance audits, and mentored junior staff."
     ]),
    ("Hewlett Packard Global, Bangalore, India - SAP Basis Consultant",
     "Jan 2011 - Oct 2013",
     [
        "Managed OS/DB migrations on ECC, BW, SCM, Portal systems with Oracle 11g/11c on Linux.",
        "Implemented SAP Solution Manager 7.1 for monitoring and proactive issue resolution.",
        "Supported early SAP HANA deployments, backups, and security role maintenance.",
        "Automated administrative and migration tasks using scripting and LSMW."
     ]),
    ("Tech Mahindra - SAP Basis Administrator",
     "Feb 2006 - Dec 2011",
     [
        "Administered SAP ECC 4.7 on AIX with DB2 HADR and GeoCluster setups.",
        "Applied patches, kernel upgrades, and support packs for system stability.",
        "Developed automation scripts for monitoring and alerting.",
        "Executed ITIL-aligned incident and change management, and documented best practices."
     ])
]

for role, duration, bullets in experience_texts:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, clean_text(role), ln=1)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, clean_text(duration), ln=1)
    pdf.set_font("Helvetica", "", 10)
    for b in bullets:
        pdf.multi_cell(0, 5, f"- {clean_text(b)}")
    pdf.ln(2)

# Save PDF
pdf.output("Koti_Davuluri_Resume.pdf")
print("PDF generated successfully!")
