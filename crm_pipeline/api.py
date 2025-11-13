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

        # Prepare base deal data from pipeline
        deal_data = {
            "doctype": "CRM Deal",
            "deal_name": pipeline_doc.lead_name or pipeline_doc.pipeline_name,
            "pipeline": pipeline_doc.name,
            "organization": existing_organization or pipeline_doc.organization,
            "organization_name": pipeline_doc.organization_name,
            "website": pipeline_doc.website,
            "lead_name": pipeline_doc.lead_name,
            "organization_owner": pipeline_doc.organization_owner,
            "deal_owner": pipeline_doc.pipeline_owner or frappe.session.user,
            "lead": pipeline_doc.lead,
            "source": pipeline_doc.source,
            "no_of_employees": pipeline_doc.no_of_employees,
            "territory": pipeline_doc.territory,
            "currency": pipeline_doc.currency,
            "exchange_rate": pipeline_doc.exchange_rate,
            "email": pipeline_doc.email,
            "mobile_no": pipeline_doc.mobile_no,
        }

        # Add contact if provided
        if existing_contact:
            deal_data["contact"] = existing_contact
            print(f"👤 Contact set: {existing_contact}")

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
def get_data(doctype, filters=None, order_by=None, **kwargs):
    """
    Override the default get_data API for CRM Pipeline
    """
    
    # Only handle CRM Pipeline, pass everything else through
    if doctype != "CRM Pipeline":
        from crm.api.doc import get_data as original_get_data
        
        # Prepare parameters for the original function, excluding 'cmd'
        original_kwargs = {k: v for k, v in kwargs.items() if k != 'cmd'}
        return original_get_data(doctype, filters, order_by, **original_kwargs)
    
    # CRM Pipeline specific handling
    try:
        # Get all relevant fields from your doctype
        fields = [
            "name", "pipeline_name", "organization", "status", 
            "pipeline_owner", "est_pipeline_value", "total_deal_value",
            "email", "mobile_no", "lead", "lead_name", "source",
            "organization_name", "website", "territory", "modified",
            "creation", "_assign"
        ]
        
        # Parse filters
        if isinstance(filters, str):
            filters = frappe.parse_json(filters)
        elif filters is None:
            filters = {}
            
        # Set default order_by
        if not order_by:
            order_by = 'modified desc'
            
        # Get pagination parameters (filter out 'cmd')
        safe_kwargs = {k: v for k, v in kwargs.items() if k != 'cmd'}
        page_length = int(safe_kwargs.get('page_length', 20))
        page_length_count = int(safe_kwargs.get('page_length_count', 20))
        
        # Get view parameters
        view = safe_kwargs.get('view', {})
        if isinstance(view, str):
            view = frappe.parse_json(view)
        view_type = view.get('view_type', 'list')
        group_by_field = view.get('group_by_field', 'owner')
        
        # Get other view-related parameters
        column_field = safe_kwargs.get('column_field', 'status')
        title_field = safe_kwargs.get('title_field', '')
        
        # Get kanban parameters
        kanban_columns = safe_kwargs.get('kanban_columns', '[]')
        if isinstance(kanban_columns, str):
            try:
                kanban_columns = frappe.parse_json(kanban_columns)
            except:
                kanban_columns = []
        elif not kanban_columns:
            kanban_columns = []
            
        kanban_fields = safe_kwargs.get('kanban_fields', '[]')
        if isinstance(kanban_fields, str):
            try:
                kanban_fields = frappe.parse_json(kanban_fields)
            except:
                kanban_fields = []
        elif not kanban_fields:
            kanban_fields = []
        
        # Get the actual data
        data = frappe.get_all(
            doctype,
            fields=fields,
            filters=filters,
            order_by=order_by,
            limit_page_length=page_length
        )
        
        # Get total count for pagination
        total_count = frappe.db.count(doctype, filters)
        
        # Get field metadata for column selection
        meta = frappe.get_meta(doctype)
        all_fields = []
        for field in meta.fields:
            if field.fieldtype not in ['Section Break', 'Column Break', 'Tab Break']:
                all_fields.append({
                    "label": field.label,
                    "value": field.fieldname,
                    "type": field.fieldtype,
                    "options": field.options
                })
        
        # Get columns from request (saved view) or use defaults
        columns = safe_kwargs.get('columns')
        if columns:
            # Parse if it's a string
            if isinstance(columns, str):
                try:
                    columns = frappe.parse_json(columns)
                except:
                    columns = None
        
        # If no columns provided, use defaults
        if not columns:
            columns = [
                {"label": "Pipeline Name", "type": "Data", "key": "pipeline_name", "width": "12rem"},
                {"label": "Organization", "type": "Link", "key": "organization", "options": "CRM Organization", "width": "10rem"},
                {"label": "Status", "type": "Link", "key": "status", "options": "CRM Pipeline Status", "width": "8rem"},
                {"label": "Pipeline Owner", "type": "Link", "key": "pipeline_owner", "options": "User", "width": "10rem"},
                {"label": "Est Pipeline Value", "type": "Data", "key": "est_pipeline_value", "width": "10rem"},
                {"label": "Email", "type": "Data", "key": "email", "width": "12rem"},
                {"label": "Mobile No", "type": "Data", "key": "mobile_no", "width": "11rem"},
                {"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
            ]
        
        # Get rows from request (saved view) or use defaults
        rows = safe_kwargs.get('rows')
        if rows:
            # Parse if it's a string
            if isinstance(rows, str):
                try:
                    rows = frappe.parse_json(rows)
                except:
                    rows = None
        
        # If no rows provided, use default fields
        if not rows:
            rows = fields
        
        return {
            "data": data,
            "columns": columns,
            "rows": rows,
            "fields": all_fields,
            "column_field": column_field,
            "title_field": title_field,
            "kanban_columns": kanban_columns,
            "kanban_fields": kanban_fields,
            "group_by_field": group_by_field,
            "page_length": page_length,
            "page_length_count": page_length_count,
            "total_count": total_count,
            "row_count": len(data),
            "view_type": view_type,
            "is_default": False
        }
        
    except Exception as e:
        frappe.log_error(f"Error in CRM Pipeline get_data: {str(e)}")
        # Return minimal fallback structure
        return {
            "columns": [],
            "rows": [],
            "total_count": 0,
            "row_count": 0,
            "data": [],
            "page_length": 20,
            "page_length_count": 20,
            "fields": []  # Empty fields array as fallback
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