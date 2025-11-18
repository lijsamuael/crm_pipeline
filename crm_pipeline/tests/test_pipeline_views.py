# Copyright (c) 2025, Samuael Ketema and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.tests.utils import FrappeTestCase


class TestPipelineViews(FrappeTestCase):
	"""Test cases for CRM Pipeline list and Kanban views"""

	def setUp(self):
		"""Set up test data"""
		# Create test organization
		if not frappe.db.exists("CRM Organization", {"organization_name": "Test Org"}):
			self.org = frappe.get_doc({
				"doctype": "CRM Organization",
				"organization_name": "Test Org",
			})
			self.org.insert(ignore_permissions=True)
		else:
			self.org = frappe.get_doc("CRM Organization", {"organization_name": "Test Org"})

		# Create test pipeline statuses
		for status_name in ["Open", "Ongoing", "Won"]:
			if not frappe.db.exists("CRM Pipeline Status", status_name):
				status = frappe.get_doc({
					"doctype": "CRM Pipeline Status",
					"status": status_name,
				})
				status.insert(ignore_permissions=True)

		# Create test pipelines
		self.pipelines = []
		for i in range(3):
			pipeline = frappe.get_doc({
				"doctype": "CRM Pipeline",
				"pipeline_name": f"Test Pipeline {i+1}",
				"organization": self.org.name,
				"status": ["Open", "Ongoing", "Won"][i],
				"pipeline_owner": frappe.session.user,
			})
			pipeline.insert(ignore_permissions=True)
			self.pipelines.append(pipeline)

	def tearDown(self):
		"""Clean up test data"""
		for pipeline in self.pipelines:
			if frappe.db.exists("CRM Pipeline", pipeline.name):
				frappe.delete_doc("CRM Pipeline", pipeline.name, force=1, ignore_permissions=True)

	def test_controller_has_default_list_data(self):
		"""Test that CRMPipeline controller has default_list_data method"""
		from crm_pipeline.doctype.crm_pipeline.crm_pipeline import CRMPipeline
		
		self.assertTrue(hasattr(CRMPipeline, "default_list_data"))
		result = CRMPipeline.default_list_data()
		self.assertIn("columns", result)
		self.assertIn("rows", result)
		self.assertIsInstance(result["columns"], list)
		self.assertIsInstance(result["rows"], list)
		self.assertGreater(len(result["columns"]), 0)
		self.assertGreater(len(result["rows"]), 0)

	def test_controller_has_default_kanban_settings(self):
		"""Test that CRMPipeline controller has default_kanban_settings method"""
		from crm_pipeline.doctype.crm_pipeline.crm_pipeline import CRMPipeline
		
		self.assertTrue(hasattr(CRMPipeline, "default_kanban_settings"))
		result = CRMPipeline.default_kanban_settings()
		self.assertIn("column_field", result)
		self.assertIn("title_field", result)
		self.assertIn("kanban_fields", result)

	def test_get_data_list_view(self):
		"""Test get_data API for list view"""
		from crm_pipeline.api import get_data
		
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "list"},
		)
		
		self.assertIn("data", result)
		self.assertIn("columns", result)
		self.assertIn("rows", result)
		self.assertIn("fields", result)
		self.assertIsInstance(result["data"], list)
		self.assertIsInstance(result["columns"], list)
		self.assertIsInstance(result["rows"], list)
		self.assertGreater(len(result["columns"]), 0)

	def test_get_data_kanban_view(self):
		"""Test get_data API for Kanban view"""
		from crm_pipeline.api import get_data
		
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "kanban"},
			column_field="status",
		)
		
		self.assertIn("data", result)
		self.assertIsInstance(result["data"], list)
		
		# Check that each kanban column has delete property
		for item in result["data"]:
			if "column" in item:
				self.assertIn("delete", item["column"])
				self.assertIsInstance(item["column"]["delete"], bool)

	def test_get_data_uses_default_columns(self):
		"""Test that get_data uses default columns when no custom view"""
		from crm_pipeline.api import get_data
		from crm_pipeline.doctype.crm_pipeline.crm_pipeline import CRMPipeline
		
		default_columns = CRMPipeline.default_list_data()["columns"]
		
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "list"},
		)
		
		# Check that default columns are used
		self.assertEqual(len(result["columns"]), len(default_columns))
		for default_col in default_columns:
			# Find matching column in result
			matching = [c for c in result["columns"] if c.get("key") == default_col.get("key")]
			self.assertGreater(len(matching), 0, f"Default column {default_col.get('key')} not found")

	def test_get_data_kanban_columns_have_delete_property(self):
		"""Test that Kanban columns always have delete property"""
		from crm_pipeline.api import get_data
		
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "kanban"},
			column_field="status",
		)
		
		# Check kanban_columns in response
		if "kanban_columns" in result:
			for kc in result["kanban_columns"]:
				if isinstance(kc, dict):
					self.assertIn("delete", kc)
		
		# Check columns in data items
		for item in result.get("data", []):
			if "column" in item and isinstance(item["column"], dict):
				self.assertIn("delete", item["column"])

	def test_get_data_passes_through_other_doctypes(self):
		"""Test that get_data passes through to original function for other doctypes"""
		from crm_pipeline.api import get_data
		
		# This should call the original CRM get_data
		result = get_data(
			doctype="CRM Lead",
			filters={},
			order_by="modified desc",
			view={"view_type": "list"},
		)
		
		# Should still return valid structure
		self.assertIn("data", result)
		self.assertIn("columns", result)

	def test_column_management_persistence(self):
		"""Test that column changes can be saved and retrieved"""
		from crm_pipeline.api import get_data
		
		# Get initial data
		initial = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "list"},
		)
		
		# Modify columns
		custom_columns = initial["columns"][:3]  # Take first 3 columns
		
		# Get data with custom columns
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "list"},
			columns=custom_columns,
		)
		
		# Should use custom columns
		self.assertEqual(len(result["columns"]), len(custom_columns))

	def test_kanban_view_with_custom_columns(self):
		"""Test Kanban view with custom kanban columns"""
		from crm_pipeline.api import get_data
		
		custom_kanban_columns = [
			{"name": "Open", "delete": False},
			{"name": "Ongoing", "delete": False},
		]
		
		result = get_data(
			doctype="CRM Pipeline",
			filters={},
			order_by="modified desc",
			view={"view_type": "kanban"},
			column_field="status",
			kanban_columns=custom_kanban_columns,
		)
		
		self.assertIn("data", result)
		# Should have data for custom columns
		self.assertGreater(len(result["data"]), 0)

