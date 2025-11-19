import json
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


def _ensure_pipeline_organization(pipeline_doc, selected_org=None):
    """Return a valid CRM Organization docname and its display name, creating one when needed."""

    def _get_display_name(org_name):
        if not org_name:
            return None
        return frappe.db.get_value("CRM Organization", org_name, "organization_name")

    if selected_org:
        return selected_org, _get_display_name(selected_org)

    if pipeline_doc.get("organization") and frappe.db.exists("CRM Organization", pipeline_doc.organization):
        return pipeline_doc.organization, _get_display_name(pipeline_doc.organization) or pipeline_doc.get("organization_name")

    org_label = pipeline_doc.get("organization_name")
    if org_label:
        existing = frappe.db.get_value("CRM Organization", {"organization_name": org_label}, "name")
        if existing:
            return existing, org_label

    fallback_label = org_label or pipeline_doc.get("pipeline_name") or pipeline_doc.get("lead_name")
    if fallback_label:
        existing = frappe.db.get_value("CRM Organization", {"organization_name": fallback_label}, "name")
        if existing:
            return existing, fallback_label
        org_doc = frappe.get_doc({
            "doctype": "CRM Organization",
            "organization_name": fallback_label,
            "website": pipeline_doc.get("website"),
            "territory": pipeline_doc.get("territory"),
        })
        if pipeline_doc.get("email"):
            org_doc.email = pipeline_doc.get("email")
        if pipeline_doc.get("mobile_no"):
            org_doc.phone = pipeline_doc.get("mobile_no")
        org_doc.insert(ignore_permissions=True)
        return org_doc.name, org_doc.organization_name

    return None, None


def _ensure_pipeline_contact(pipeline_doc, selected_contact=None):
    """Return a valid Contact docname, creating one if required."""
    if selected_contact and frappe.db.exists("Contact", selected_contact):
        return selected_contact

    for link_field in ("contact_person", "contact"):
        link_value = pipeline_doc.get(link_field)
        if link_value and frappe.db.exists("Contact", link_value):
            return link_value

    if pipeline_doc.get("email"):
        existing_contact = frappe.db.get_value("Contact Email", {"email_id": pipeline_doc.email}, "parent")
        if existing_contact:
            return existing_contact
    if pipeline_doc.get("mobile_no"):
        existing_contact = frappe.db.get_value("Contact Phone", {"phone": pipeline_doc.mobile_no}, "parent")
        if existing_contact:
            return existing_contact

    lead_doc = None
    if pipeline_doc.get("lead"):
        try:
            lead_doc = frappe.get_doc("CRM Lead", pipeline_doc.lead)
        except Exception:
            lead_doc = None

    first_name = (
        getattr(lead_doc, "first_name", None)
        or pipeline_doc.get("lead_name")
        or pipeline_doc.get("pipeline_name")
        or _("Pipeline Contact")
    )
    last_name = getattr(lead_doc, "last_name", None) if lead_doc else None
    email = pipeline_doc.get("email") or (getattr(lead_doc, "email_id", None) if lead_doc else None)
    mobile = pipeline_doc.get("mobile_no") or (getattr(lead_doc, "mobile_no", None) if lead_doc else None)

    if not first_name and not email and not mobile:
        return None

    contact_doc = frappe.get_doc({
        "doctype": "Contact",
        "first_name": first_name or _("Pipeline Contact"),
    })
    if last_name:
        contact_doc.last_name = last_name
    if email:
        contact_doc.append("email_ids", {"email_id": email, "is_primary": 1})
    if mobile:
        contact_doc.append("phone_nos", {"phone": mobile, "is_primary_mobile_no": 1})

    contact_doc.insert(ignore_permissions=True)
    return contact_doc.name


@frappe.whitelist()
def convert_to_deal(pipeline, deal=None, existing_contact=None, existing_organization=None):
    """Create a Deal from a Pipeline with proper field mapping"""
    try:
        print(f"🚀 START: convert_to_deal called")
        print(f"📝 Parameters received:")
        print(f"   - pipeline: {pipeline}")
        print(f"   - deal: {deal}")
        print(f"   - existing_contact: {existing_contact}")
        print(f"   - existing_organization: {existing_organization}")
        
        # Get the pipeline document
        pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline)
        print(f"✅ Pipeline loaded: {pipeline_doc.name}")
        print(f"📊 Pipeline data - lead_name: {pipeline_doc.lead_name}, organization: {pipeline_doc.organization}")

        organization_name, organization_display_name = _ensure_pipeline_organization(
            pipeline_doc, existing_organization
        )

        if not organization_name:
            frappe.throw(
                _("Unable to determine an organization for this pipeline. Please add organization details before converting.")
            )

        contact_name = _ensure_pipeline_contact(pipeline_doc, existing_contact)

        print(f"🏢 Using organization: {organization_name} ({organization_display_name})")
        print(f"👤 Using contact: {contact_name or 'auto-create skipped'}")

        # Prepare base deal data from pipeline
        deal_data = {
            "doctype": "CRM Deal",
            "deal_name": pipeline_doc.lead_name or pipeline_doc.pipeline_name,
            "pipeline": pipeline_doc.name,
            "organization": organization_name,
            "organization_name": organization_display_name or pipeline_doc.organization_name,
            "website": pipeline_doc.website,
            "lead_name": pipeline_doc.lead_name,
            "organization_owner": pipeline_doc.organization_owner,
            "deal_owner": pipeline_doc.pipeline_owner or frappe.session.user,
            "lead": pipeline_doc.lead,
            "source": pipeline_doc.source,
            "email": pipeline_doc.email,
            "mobile_no": pipeline_doc.mobile_no,
        }

        # Add contact if provided/ensured
        if contact_name:
            deal_data["contact"] = contact_name
            print(f"👤 Contact set: {contact_name}")

        # Add custom fields if they exist
        if hasattr(pipeline_doc, 'est_pipeline_value') and pipeline_doc.est_pipeline_value:
            deal_data["deal_value"] = pipeline_doc.est_pipeline_value
            print(f"💰 Added est_pipeline_value: {pipeline_doc.est_pipeline_value}")
            # Also set custom field if it exists
            if frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_est_quotation_sale"}):
                deal_data["custom_est_quotation_sale"] = pipeline_doc.est_pipeline_value
                print(f"🔧 Added custom_est_quotation_sale: {pipeline_doc.est_pipeline_value}")

        # Merge deal data from frontend if provided
        if deal and isinstance(deal, dict):
            print(f"🔄 Merging deal data from frontend: {deal}")
            deal_data.update(deal)
        elif deal and isinstance(deal, str) and deal.strip():
            try:
                deal_dict = frappe.parse_json(deal)
                print(f"🔄 Merging deal data from JSON string: {deal_dict}")
                deal_data.update(deal_dict)
            except Exception as parse_error:
                print(f"⚠️ Failed to parse deal parameter: {parse_error}")

        print(f"🎯 Final deal data before creation:")
        for key, value in deal_data.items():
            print(f"   - {key}: {value}")

        # Create the deal
        deal_doc = frappe.get_doc(deal_data)
        deal_doc.insert(ignore_permissions=True)
        print(f"✅ Deal created successfully: {deal_doc.name}")

        if organization_name:
            pipeline_doc.organization = organization_name
            if organization_display_name:
                pipeline_doc.organization_name = organization_display_name

        pipeline_meta = pipeline_doc.meta
        if contact_name:
            if pipeline_meta.has_field("contact_person"):
                pipeline_doc.contact_person = contact_name
            if pipeline_meta.has_field("contact"):
                pipeline_doc.contact = contact_name

        # Link deal back to pipeline if deals child table exists
        if hasattr(pipeline_doc, 'deals'):
            new_deal = pipeline_doc.append("deals", {})
            new_deal.deal = deal_doc.name
            new_deal.deal_owner = deal_doc.deal_owner
            new_deal.deal_value = deal_doc.deal_value
            
            if hasattr(deal_doc, 'probability'):
                new_deal.probability = deal_doc.probability
            if hasattr(deal_doc, 'expected_deal_value'):
                new_deal.expected_deal_value = deal_doc.expected_deal_value
            
            
            pipeline_doc.save(ignore_permissions=True)
            print(f"🔗 Deal linked to pipeline deals child table")
        else:
            print(f"ℹ️ No deals child table found in pipeline")

        # Update pipeline status to indicate conversion
        pipeline_doc.converted_to_deal = deal_doc.name
        pipeline_doc.save(ignore_permissions=True)
        print(f"🔄 Pipeline status updated to: {pipeline_doc.status}")

        frappe.db.commit()
        print(f"💾 Database changes committed")
        
        frappe.msgprint(_("Deal {0} created successfully from pipeline").format(deal_doc.name))
        print(f"🎉 SUCCESS: Conversion completed for pipeline {pipeline} -> deal {deal_doc.name}")
        
        return deal_doc.name

    except Exception as e:
        print(f"❌ ERROR in convert_to_deal: {str(e)}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        frappe.db.rollback()
        print(f"🔄 Database changes rolled back due to error")
        frappe.log_error(f"Error converting pipeline to deal: {str(e)}")
        frappe.throw(_("Error converting pipeline to deal: {0}").format(str(e)))
        


@frappe.whitelist()
def link_deal_to_pipeline(pipeline, deal_data):
    """
    Simple function to link deal to pipeline's deals child table
    """
    try:
        # Get pipeline document
        pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline)
        
        # Parse deal data if string
        if isinstance(deal_data, str):
            deal_data = frappe.parse_json(deal_data)
        
        print("Received deal data:", deal_data)  # Debug log
        
        # Link deal to pipeline child table using the data directly
        if hasattr(pipeline_doc, 'deals'):
            # Create the child table row with all incoming data
            new_deal = pipeline_doc.append("deals", deal_data)
            
            pipeline_doc.save(ignore_permissions=True)
            frappe.db.commit()

        return {"success": True, "message": "Deal linked to pipeline, successfully.", "data": deal_data}

    except Exception as e:
        frappe.log_error(f"Error linking deal to pipeline: {str(e)}")
        return {"success": False, "error": str(e)}
    


@frappe.whitelist()
def unlink_deal_from_pipeline(pipeline, deal_name):
    """
    Remove deal from pipeline's deals child table
    """
    try:
        # Get pipeline document
        pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline)
        
        # Remove the deal from child table
        if hasattr(pipeline_doc, 'deals'):
            # Find and remove the deal by name
            pipeline_doc.deals = [d for d in pipeline_doc.deals if d.name != deal_name]
            
            pipeline_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
        return {"success": True, "message": "Deal unlinked from pipeline"}
        
    except Exception as e:
        frappe.log_error(f"Error unlinking deal from pipeline: {str(e)}")
        return {"success": False, "error": str(e)}
    
        
        
@frappe.whitelist()
def get_data(
	doctype: str,
	filters: dict = None,
	order_by: str = None,
	page_length=20,
	page_length_count=20,
	column_field=None,
	title_field=None,
	columns=[],
	rows=[],
	kanban_columns=[],
	kanban_fields=[],
	view=None,
	default_filters=None,
):
	"""
	Override the default get_data API to properly handle CRM Pipeline controller lookup.
	For CRM Pipeline, we import the controller directly to avoid get_controller issues.
	For all other doctypes, we call the original CRM get_data.
	"""
	# Import the original get_data function
	from crm.api.doc import get_data as original_get_data
	from frappe.model.document import get_controller
	from frappe.model import no_value_fields
	import json
	
	# For CRM Pipeline, handle controller lookup manually
	if doctype == "CRM Pipeline":
		try:
			# Import CRMPipeline controller directly
			from crm_pipeline.doctype.crm_pipeline.crm_pipeline import CRMPipeline
			_list = CRMPipeline
		except ImportError:
			# Fallback: try to get controller normally
			try:
				_list = get_controller(doctype)
			except:
				# If all else fails, use Document base class
				from frappe.model.document import Document
				_list = Document
	else:
		# For all other doctypes, use the original function
		return original_get_data(
			doctype=doctype,
			filters=filters,
			order_by=order_by,
			page_length=page_length,
			page_length_count=page_length_count,
			column_field=column_field,
			title_field=title_field,
			columns=columns,
			rows=rows,
			kanban_columns=kanban_columns,
			kanban_fields=kanban_fields,
			view=view,
			default_filters=default_filters,
		)
	
	# Rest of the function is identical to the original CRM get_data
	# but uses _list (CRMPipeline) instead of get_controller(doctype)
	custom_view = False
	filters = frappe._dict(filters or {})
	rows = frappe.parse_json(rows or "[]")
	columns = frappe.parse_json(columns or "[]")
	kanban_fields = frappe.parse_json(kanban_fields or "[]")
	kanban_columns = frappe.parse_json(kanban_columns or "[]")

	custom_view_name = view.get("custom_view_name") if view else None
	view_type = view.get("view_type") if view else None
	group_by_field = view.get("group_by_field") if view else None

	for key in filters:
		value = filters[key]
		if isinstance(value, list):
			if "@me" in value:
				value[value.index("@me")] = frappe.session.user
			elif "%@me%" in value:
				index = [i for i, v in enumerate(value) if v == "%@me%"]
				for i in index:
					value[i] = "%" + frappe.session.user + "%"
		elif value == "@me":
			filters[key] = frappe.session.user

	if default_filters:
		default_filters = frappe.parse_json(default_filters)
		filters.update(default_filters)

	is_default = True
	data = []
	default_rows = []
	if hasattr(_list, "default_list_data"):
		default_rows = _list.default_list_data().get("rows")

	meta = frappe.get_meta(doctype)

	if view_type != "kanban":
		if columns or rows:
			custom_view = True
			is_default = False
			columns = frappe.parse_json(columns)
			rows = frappe.parse_json(rows)

		if not columns:
			columns = [
				{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
				{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
			]

		if not rows:
			rows = ["name"]

		default_view_filters = {
			"dt": doctype,
			"type": view_type or "list",
			"is_standard": 1,
			"user": frappe.session.user,
		}

		if not custom_view and frappe.db.exists("CRM View Settings", default_view_filters):
			list_view_settings = frappe.get_doc("CRM View Settings", default_view_filters)
			columns = frappe.parse_json(list_view_settings.columns)
			rows = frappe.parse_json(list_view_settings.rows)
			is_default = False
		elif not custom_view or (is_default and hasattr(_list, "default_list_data")):
			rows = default_rows
			columns = _list.default_list_data().get("columns")

		# check if rows has all keys from columns if not add them
		for column in columns:
			if column.get("key") not in rows:
				rows.append(column.get("key"))
			column["label"] = _(column.get("label"))

			if column.get("key") == "_liked_by" and column.get("width") == "10rem":
				column["width"] = "50px"

			# remove column if column.hidden is True
			column_meta = meta.get_field(column.get("key"))
			if column_meta and column_meta.get("hidden"):
				columns.remove(column)

		# check if rows has group_by_field if not add it
		if group_by_field and group_by_field not in rows:
			rows.append(group_by_field)

		data = (
			frappe.get_list(
				doctype,
				fields=rows,
				filters=filters,
				order_by=order_by,
				page_length=page_length,
			)
			or []
		)
		# Import parse_list_data from crm.api.doc
		from crm.api.doc import parse_list_data
		data = parse_list_data(data, doctype)

	if view_type == "kanban":
		if not rows:
			rows = default_rows

		field_meta = frappe.get_meta(doctype).get_field(column_field) if column_field else None

		if not kanban_columns and field_meta:
			if field_meta.fieldtype == "Link":
				kanban_columns = frappe.get_all(
					field_meta.options,
					fields=["name"],
					order_by="modified asc",
				)
			elif field_meta.fieldtype == "Select":
				kanban_columns = [{"name": option} for option in field_meta.options.split("\n")]

		if not title_field:
			title_field = "name"
			if hasattr(_list, "default_kanban_settings"):
				title_field = _list.default_kanban_settings().get("title_field")

		if title_field not in rows:
			rows.append(title_field)

		if not kanban_fields:
			kanban_fields = ["name"]
			if hasattr(_list, "default_kanban_settings"):
				kanban_fields = json.loads(_list.default_kanban_settings().get("kanban_fields"))

		for field in kanban_fields:
			if field not in rows:
				rows.append(field)

		# Import convert_filter_to_tuple and get_records_based_on_order from crm.api.doc
		from crm.api.doc import convert_filter_to_tuple, get_records_based_on_order
		
		status_color_map = {}
		if (
			field_meta
			and field_meta.fieldtype == "Link"
			and field_meta.options
		):
			status_meta = frappe.get_meta(field_meta.options)
			has_color_field = any(df.fieldname == "color" for df in status_meta.fields)
			if has_color_field:
				status_color_map = {
					doc.name: doc.get("color")
					for doc in frappe.get_all(field_meta.options, fields=["name", "color"])
				}

		for kc in kanban_columns:
			# Ensure delete property exists (default to False)
			if "delete" not in kc:
				kc["delete"] = False

			if status_color_map and not kc.get("color"):
				kc["color"] = status_color_map.get(kc.get("name"))
			
			# Start with base filters
			column_filters = []

			# Convert and add the main filters first
			if filters:
				base_filters = convert_filter_to_tuple(doctype, filters)
				column_filters.extend(base_filters)

			# Add the column-specific filter
			if column_field and kc.get("name"):
				column_filters.append([doctype, column_field, "=", kc.get("name")])

			order = kc.get("order")
			if kc.get("delete"):
				column_data = []
			else:
				page_length = kc.get("page_length", 20)

				if order:
					column_data = get_records_based_on_order(
						doctype, rows, column_filters, page_length, order
					)
				else:
					column_data = frappe.get_list(
						doctype,
						fields=rows,
						filters=column_filters,
						order_by=order_by,
						page_length=page_length,
					)

				all_count = frappe.get_list(
					doctype,
					filters=column_filters,
					fields="count(*) as total_count",
				)[0].total_count

				kc["all_count"] = all_count
				kc["count"] = len(column_data)

			if order:
				column_data = sorted(
					column_data,
					key=lambda x: order.index(x.get("name")) if x.get("name") in order else len(order),
				)

			data.append({"column": kc, "fields": kanban_fields, "data": column_data})

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": _(field.label),
			"fieldtype": field.fieldtype,
			"fieldname": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "fieldtype": "Data", "fieldname": "name"},
		{"label": "Created On", "fieldtype": "Datetime", "fieldname": "creation"},
		{"label": "Last Modified", "fieldtype": "Datetime", "fieldname": "modified"},
		{
			"label": "Modified By",
			"fieldtype": "Link",
			"fieldname": "modified_by",
			"options": "User",
		},
		{"label": "Assigned To", "fieldtype": "Text", "fieldname": "_assign"},
		{"label": "Owner", "fieldtype": "Link", "fieldname": "owner", "options": "User"},
		{"label": "Like", "fieldtype": "Data", "fieldname": "_liked_by"},
	]

	for field in std_fields:
		if field.get("fieldname") not in rows:
			rows.append(field.get("fieldname"))
		if field not in fields:
			field["label"] = _(field["label"])
			fields.append(field)

	if not is_default and custom_view_name:
		is_default = frappe.db.get_value("CRM View Settings", custom_view_name, "load_default_columns")

	if group_by_field and view_type == "group_by":
		group_by_field_name = group_by_field

		def get_options(type, options):
			if type == "Select":
				return [option for option in options.split("\n")]
			else:
				has_empty_values = any([not d.get(group_by_field_name) for d in data])
				options = list(set([d.get(group_by_field_name) for d in data]))
				options = [u for u in options if u]
				if has_empty_values:
					options.append("")

				if order_by and group_by_field_name in order_by:
					order_by_fields = order_by.split(",")
					order_by_fields = [
						(field.split(" ")[0], field.split(" ")[1]) for field in order_by_fields
					]
					if (group_by_field_name, "asc") in order_by_fields:
						options.sort()
					elif (group_by_field_name, "desc") in order_by_fields:
						options.sort(reverse=True)
				else:
					options.sort()
				return options

		group_by_field_dict = None
		for field in fields:
			if field.get("fieldname") == group_by_field_name:
				group_by_field_dict = {
					"label": field.get("label"),
					"fieldname": field.get("fieldname"),
					"fieldtype": field.get("fieldtype"),
					"options": field.get("options"),
				}
				break

		if group_by_field_dict:
			options = get_options(group_by_field_dict.get("fieldtype"), group_by_field_dict.get("options"))
		else:
			group_by_field_meta = meta.get_field(group_by_field_name)
			options = get_options(group_by_field_meta.fieldtype, group_by_field_meta.options)

		grouped_data = {}
		for option in options:
			grouped_data[option] = [d for d in data if d.get(group_by_field_name) == option]

		data = grouped_data
		group_by_field = group_by_field_dict or group_by_field_name

	# Import get_views from crm.api.views
	from crm.api.views import get_views
	
	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"column_field": column_field,
		"title_field": title_field,
		"kanban_columns": kanban_columns,
		"kanban_fields": kanban_fields,
		"group_by_field": group_by_field,
		"view_type": view_type,
		"is_default": is_default,
		"views": get_views(doctype),
	}
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
@frappe.whitelist()
def link_pipeline_to_master(pipeline, pipeline_data):
    """
    Simple function to link pipeline to master pipeline's sub_pipelines child table
    Uses same logic as link_deal_to_pipeline
    """
    try:
        # Get pipeline document
        pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline)
        
        # Parse pipeline data if string
        if isinstance(pipeline_data, str):
            pipeline_data = frappe.parse_json(pipeline_data)
        
        print("Received pipeline data:", pipeline_data)  # Debug log
        
        # Link pipeline to master pipeline child table using the data directly
        if hasattr(pipeline_doc, 'sub_pipelines'):
            # Create the child table row with all incoming data
            new_pipeline = pipeline_doc.append("sub_pipelines", pipeline_data)
            
            pipeline_doc.save(ignore_permissions=True)
            frappe.db.commit()

        return {"success": True, "message": "Pipeline linked to master pipeline successfully.", "data": pipeline_data}

    except Exception as e:
        frappe.log_error(f"Error linking pipeline to master: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def unlink_pipeline_from_master(pipeline, pipeline_name):
    """
    Remove pipeline from master pipeline's sub_pipelines child table
    Uses same logic as unlink_deal_from_pipeline
    """
    try:
        # Get pipeline document
        pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline)
        
        # Remove the pipeline from child table
        if hasattr(pipeline_doc, 'sub_pipelines'):
            # Find and remove the pipeline by name
            pipeline_doc.sub_pipelines = [p for p in pipeline_doc.sub_pipelines if p.name != pipeline_name]
            
            pipeline_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
        return {"success": True, "message": "Pipeline unlinked from master pipeline"}
        
    except Exception as e:
        frappe.log_error(f"Error unlinking pipeline from master: {str(e)}")
        return {"success": False, "error": str(e)}
    
    

@frappe.whitelist()
def get_child_pipelines_with_deals(master_pipeline):
    """
    Get all child pipelines with their deal counts and total values
    """
    try:
        # Get the master pipeline document
        master_doc = frappe.get_doc("CRM Pipeline", master_pipeline)
        child_pipelines = []
        
        # Get all child pipelines from sub_pipelines child table
        for child in master_doc.sub_pipelines:
            pipeline_name = child.pipeline_name
            
            # Get the child pipeline document to access its deals
            try:
                child_pipeline_doc = frappe.get_doc("CRM Pipeline", pipeline_name)
                
                # Count deals and calculate total value from the child pipeline's deals table
                total_deals = len(child_pipeline_doc.deals) if hasattr(child_pipeline_doc, 'deals') else 0
                total_value = 0
                
                if hasattr(child_pipeline_doc, 'deals'):
                    for deal in child_pipeline_doc.deals:
                        total_value += float(deal.deal_value or 0)
                
                child_pipelines.append({
                    "name": child.name,
                    "pipeline_name": child.pipeline_name,
                    "pipeline_owner": child.pipeline_owner,
                    "status": child.status,
                    "creation": child.creation,
                    "total_deals": total_deals,
                    "total_value": total_value
                })
                
            except Exception as e:
                # If child pipeline doesn't exist or other error, include basic info
                frappe.log_error(f"Error processing child pipeline {pipeline_name}: {str(e)}")
                child_pipelines.append({
                    "name": child.name,
                    "pipeline": pipeline_name,
                    "pipeline_name": child.pipeline_name,
                    "pipeline_owner": child.pipeline_owner,
                    "status": child.status,
                    "creation": child.creation,
                    "total_deals": 0,
                    "total_value": 0
                })
        
        return {
            "success": True,
            "child_pipelines": child_pipelines
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting child pipelines with deals: {str(e)}")
        return {
            "success": False,
            "error": _("Failed to get child pipelines with deals: {0}").format(str(e))
        }
        



























@frappe.whitelist()
def get_grid_layout(doctype):
    """
    Get the grid layout for a specific doctype and return in table format
    """
    try:
        # Get the raw layout data
        layout_data = []
        if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": "Grid Row"}):
            layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": "Grid Row"})
            if layout and layout.layout:
                layout_data = json.loads(layout.layout)
        
        
        # Log the raw layout data for debugging
        frappe.logger().info(f"Raw grid layout for {doctype}: {json.dumps(layout_data, indent=2)}")
        
        # Initialize result structure
        result = {
            "success": True,
            "columns": [],
            "field_metadata": {},
            "raw_layout": layout_data
        }
        
        # Extract columns from the layout data
        columns = []
        field_metadata = {}
        
        if isinstance(layout_data, list):
            # Handle your JSON structure: [{"name": "Deal", "field": "deal"}, ...]
            for item in layout_data:
                if isinstance(item, dict) and "field" in item:
                    fieldname = item["field"]
                    label = item.get("name", fieldname)
                    
                    # Get field metadata from doctype
                    field_meta = frappe.get_meta(doctype).get_field(fieldname)
                    
                    column_data = {
                        "fieldname": fieldname,
                        "label": label,
                        "fieldtype": field_meta.fieldtype if field_meta else "Data",
                        "options": getattr(field_meta, 'options', None) if field_meta else None,
                        "width": getattr(field_meta, 'width', None) if field_meta else None,
                        "read_only": getattr(field_meta, 'read_only', 0) if field_meta else 0,
                        "hidden": getattr(field_meta, 'hidden', 0) if field_meta else 0,
                        "reqd": getattr(field_meta, 'reqd', 0) if field_meta else 0
                    }
                    
                    columns.append(column_data)
                    
                    # Store full field metadata
                    if field_meta:
                        field_metadata[fieldname] = {
                            "label": field_meta.label,
                            "fieldtype": field_meta.fieldtype,
                            "options": getattr(field_meta, 'options', None),
                            "mandatory": getattr(field_meta, 'reqd', 0),
                            "read_only": getattr(field_meta, 'read_only', 0),
                            "hidden": getattr(field_meta, 'hidden', 0)
                        }
        
        # If no columns found in the expected structure, try alternative parsing
        if not columns and layout_data:
            frappe.logger().info("Trying alternative layout parsing...")
            columns = extract_columns_from_alternative_layout(layout_data, doctype)
        
        result["columns"] = columns
        result["field_metadata"] = field_metadata
        
        # Log the final result
        frappe.logger().info(f"Processed grid layout for {doctype}: {len(columns)} columns found")
        frappe.logger().info(f"Columns: {[col['fieldname'] for col in columns]}")
        
        return result
        
    except Exception as e:
        frappe.logger().error(f"Error in get_grid_layout for {doctype}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "columns": [],
            "field_metadata": {}
        }


def extract_columns_from_alternative_layout(layout_data, doctype):
    """
    Extract columns from alternative layout structures
    """
    columns = []
    
    def extract_from_dict(data, path=""):
        if isinstance(data, dict):
            # Check if this is a field definition
            if "fieldname" in data or "field" in data:
                fieldname = data.get("fieldname") or data.get("field")
                if fieldname:
                    label = data.get("label") or data.get("name") or fieldname
                    
                    # Get field metadata
                    field_meta = frappe.get_meta(doctype).get_field(fieldname)
                    
                    columns.append({
                        "fieldname": fieldname,
                        "label": label,
                        "fieldtype": field_meta.fieldtype if field_meta else data.get("fieldtype", "Data"),
                        "options": getattr(field_meta, 'options', None) if field_meta else data.get("options"),
                        "width": data.get("width"),
                        "read_only": data.get("read_only", 0),
                        "hidden": data.get("hidden", 0),
                        "reqd": data.get("reqd", 0)
                    })
            
            # Recursively check nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    extract_from_dict(value, f"{path}.{key}" if path else key)
    
    def extract_from_list(data_list, path=""):
        for item in data_list:
            if isinstance(item, (dict, list)):
                extract_from_dict(item, path)
    
    if isinstance(layout_data, list):
        extract_from_list(layout_data)
    elif isinstance(layout_data, dict):
        extract_from_dict(layout_data)
    
    return columns


@frappe.whitelist()
def get_grid_data(doctype, filters=None, fields=None, parent_doctype=None, parent_name=None):
    """
    Get grid data with dynamic columns based on grid layout
    """
    try:
        # Get the grid layout to determine which fields to show
        layout_result = get_grid_layout(doctype)
        
        if not layout_result.get("success"):
            return layout_result
        
        columns = layout_result.get("columns", [])
        
        # Use fields from grid layout if not specified
        if not fields:
            fields = [col["fieldname"] for col in columns if not col.get("hidden")]
        
        # Add essential fields if not present
        essential_fields = ["name", "modified", "creation"]
        for field in essential_fields:
            if field not in fields:
                fields.append(field)
        
        # Parse filters if they are JSON string
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except json.JSONDecodeError:
                filters = {}
        
        # Build query based on whether it's a child table or standalone
        if parent_doctype and parent_name:
            # This is a child table - get data from parent document
            parent_doc = frappe.get_doc(parent_doctype, parent_name)
            
            # Find the child table field
            child_table_data = []
            for child_field in frappe.get_meta(parent_doctype).get_table_fields():
                if child_field.options == doctype:
                    child_table = parent_doc.get(child_field.fieldname)
                    if child_table:
                        for child in child_table:
                            child_dict = child.as_dict()
                            # Filter to only include requested fields
                            filtered_child = {}
                            for field in fields:
                                if field in child_dict:
                                    filtered_child[field] = child_dict[field]
                            child_table_data.append(filtered_child)
                        break
            
            data = child_table_data
            
        else:
            # This is a standalone document
            data = frappe.get_list(
                doctype,
                fields=fields,
                filters=filters or {},
                order_by="creation desc"
            )
        
        result = {
            "success": True,
            "columns": columns,
            "data": data,
            "field_metadata": layout_result.get("field_metadata", {}),
            "total_count": len(data)
        }
        
        # Log the result for debugging
        frappe.logger().info(f"Grid data for {doctype}: {len(data)} records with {len(fields)} fields")
        
        return result
        
    except Exception as e:
        frappe.logger().error(f"Error in get_grid_data for {doctype}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "columns": [],
            "data": [],
            "total_count": 0
        }


@frappe.whitelist()
def get_child_table_grid(parent_doctype, parent_name, child_doctype, child_fieldname):
    """
    Convenience function specifically for child table grids
    """
    return get_grid_data(
        doctype=child_doctype,
        parent_doctype=parent_doctype,
        parent_name=parent_name
    )


# Example usage and test function
@frappe.whitelist()
def test_grid_layout(doctype="CRM Pipeline Items"):
    """
    Test function to see what the grid layout returns
    """
    result = get_grid_layout(doctype)
    
    frappe.logger().info("=== GRID LAYOUT TEST RESULTS ===")
    frappe.logger().info(f"Doctype: {doctype}")
    frappe.logger().info(f"Success: {result.get('success')}")
    frappe.logger().info(f"Number of columns: {len(result.get('columns', []))}")
    frappe.logger().info(f"Columns: {[col['fieldname'] for col in result.get('columns', [])]}")
    frappe.logger().info(f"Raw layout sample: {json.dumps(result.get('raw_layout', [])[:2], indent=2)}")
    
    return result