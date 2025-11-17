# Copyright (c) 2025, Samuael Ketema and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMPipeline(Document):
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Pipeline Name",
				"type": "Data",
				"key": "pipeline_name",
				"width": "12rem",
			},
			{
				"label": "Organization",
				"type": "Link",
				"key": "organization",
				"options": "CRM Organization",
				"width": "10rem",
			},
			{
				"label": "Status",
				"type": "Link",
				"key": "status",
				"options": "CRM Pipeline Status",
				"width": "8rem",
			},
			{
				"label": "Pipeline Owner",
				"type": "Link",
				"key": "pipeline_owner",
				"options": "User",
				"width": "10rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "12rem",
			},
			{
				"label": "Mobile No",
				"type": "Data",
				"key": "mobile_no",
				"width": "11rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"pipeline_name",
			"organization",
			"status",
			"pipeline_owner",
			"email",
			"mobile_no",
			"lead",
			"lead_name",
			"source",
			"organization_name",
			"website",
			"territory",
			"modified",
			"creation",
			"_assign",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "pipeline_name",
			"kanban_fields": '["organization", "email", "mobile_no", "_assign", "modified"]',
		}

