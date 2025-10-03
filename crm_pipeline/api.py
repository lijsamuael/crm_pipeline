import frappe
from frappe import _
from frappe.utils import now_datetime



@frappe.whitelist()
def create_pipeline_from_lead(lead_name):
    """Create a pipeline from a Lead, and log the initial status"""
    lead = frappe.get_doc("CRM Lead", lead_name)

    # Try to get or create organization
    organization_name = frappe.db.exists("CRM Organization", {"organization_name": lead.organization})
    if not organization_name:
        organization_doc = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": lead.organization,
            "website": lead.website,
        })
        organization_doc.insert(ignore_permissions=True)
        organization_name = organization_doc.name
    else:
        organization_doc = frappe.get_doc("CRM Organization", organization_name)

    if not organization_doc:
        frappe.throw(_("Organization could not be created or found."))
        
    # Create contact if not exists
    contact_name = frappe.db.exists("Contact", {"full_name": lead.lead_name})
    if not contact_name and lead.email:
        contact_doc = frappe.get_doc({
            "doctype": "Contact",
            "first_name": lead.first_name,
            "last_name": lead.last_name,
            "full_name": lead.lead_name,
            "email_id": lead.email,
        })
        contact_doc.insert(ignore_permissions=True)
        
    # Create a new pipeline
    pipeline = frappe.get_doc({
        "doctype": "CRM Pipeline",
        "status": "Open",
        "pipeline_name": lead.lead_name,
        "organization": organization_doc.name,   
        "organization_owner": frappe.session.user,
        "pipeline_owner": frappe.session.user,
        "lead": lead.name,
        "lead_name": lead.lead_name,
        "source": lead.source,
        "organization_name": organization_doc.organization_name,
        "website": organization_doc.website,
        "no_of_employees": organization_doc.no_of_employees,
        "territory": organization_doc.territory,
        "currency": organization_doc.currency,
        "exchange_rate": organization_doc.exchange_rate,
    })
    pipeline.insert(ignore_permissions=True)

    # Link pipeline back to lead
    lead.custom_pipeline = pipeline.name
    lead.save(ignore_permissions=True)

    # Add initial log entry
    log_entry = pipeline.append("logs", {})
    log_entry.from_status = "Open"
    log_entry.to_status = ""
    log_entry.from_date = now_datetime()
    log_entry.duration = 0
    pipeline.save(ignore_permissions=True)

    return pipeline.name


@frappe.whitelist()
def update_pipeline_status(pipeline_name, new_status):
    """Update pipeline logs and status without overwriting child table edits"""
    pipeline = frappe.get_doc("CRM Pipeline", pipeline_name)

    # Skip if status has not changed
    if pipeline.status == new_status:
        return pipeline.name

    # Close last log if still open
    if pipeline.logs:
        last_log = pipeline.logs[-1]
        if not last_log.to_status:
            last_log.to_status = new_status
            last_log.to_date = now_datetime()
            if last_log.from_date:
                duration_seconds = (last_log.to_date - last_log.from_date).total_seconds()
                last_log.duration = format_duration(duration_seconds)
            else:
                last_log.duration = "0s"

    # Add a new log entry for the new current status
    new_log = pipeline.append("logs", {})
    new_log.from_status = new_status
    new_log.to_status = ""
    new_log.from_date = now_datetime()
    new_log.duration = "0s"

    # Update status in memory, do NOT save
    pipeline.status = new_status
    pipeline.save(ignore_permissions=True)

    return pipeline.name


def format_duration(total_seconds):
    """Format duration in the format: 2h 3m 45s or 45s if only seconds"""
    total_seconds = int(total_seconds)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:  # Always show seconds if no hours/minutes
        parts.append(f"{seconds}s")
    
    return " ".join(parts)






@frappe.whitelist()
def create_deal_from_pipeline(pipeline_name):
    """Create a Deal from a Pipeline"""
    pipeline = frappe.get_doc("CRM Pipeline", pipeline_name)


    # Create a new Deal
    deal = frappe.get_doc({
        "doctype": "CRM Deal",
        "deal_name": pipeline.lead_name,
        "pipeline": pipeline.name,
        "organization": pipeline.organization_name,
        "organization_name": pipeline.organization_name,
        "custom_pipeline_name": pipeline.name,
        "website": pipeline.website,
        "lead_name": pipeline.lead_name,
        "organization_owner": pipeline.organization_owner,
        "deal_owner": frappe.session.user,
        "lead": pipeline.lead,
        "source": pipeline.source,
        "organization_name": pipeline.organization_name,
        "website": pipeline.website,
        "no_of_employees": pipeline.no_of_employees,
        "territory": pipeline.territory,
        "currency": pipeline.currency,
        "exchange_rate": pipeline.exchange_rate,
        "custom_est_quotation_sale": pipeline.est_pipeline_value,
    })
    deal.insert(ignore_permissions=True)

    # Link deal back to pipeline
    
    new_deal = pipeline.append("deals", {})
    new_deal.deal = deal.name
    new_deal.deal_owner = deal.deal_owner
    new_deal.deal_value = deal.deal_value
    new_deal.probability = deal.probability
    new_deal.est_qouotation_sales = deal.custom_est_quotation_sale
    new_deal.expected_deal_value = deal.expected_deal_value
    pipeline.save(ignore_permissions=True)

    return deal.name



# -----------------------------------------------------------
# CRM Pipeline Hooks
def set_status_from_type(doc, method):
    """
    Automatically set the 'status' field from the 'type' field when a new CRM Pipeline Status is created.
    """
    if doc.type:
        doc.status = doc.type