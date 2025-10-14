app_name = "crm_pipeline"
app_title = "Crm Pipeline"
app_publisher = "Samuael Ketema"
app_description = "Middlware between CRM Lead and CRM Deal"
app_email = "lijsamuael@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "crm_pipeline",
# 		"logo": "/assets/crm_pipeline/logo.png",
# 		"title": "Crm Pipeline",
# 		"route": "/crm_pipeline",
# 		"has_permission": "crm_pipeline.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/crm_pipeline/css/trigger.css?verion=1"

# app_include_js = "/assets/crm_pipeline/js/crm_pipeline.js"

# include js, css files in header of web template
# web_include_css = "/assets/crm_pipeline/css/crm_pipeline.css"
# web_include_js = "/assets/crm_pipeline/js/crm_pipeline.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "crm_pipeline/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "crm_pipeline/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "crm_pipeline.utils.jinja_methods",
# 	"filters": "crm_pipeline.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "crm_pipeline.install.before_install"
# after_install = "crm_pipeline.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "crm_pipeline.uninstall.before_uninstall"
# after_uninstall = "crm_pipeline.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "crm_pipeline.utils.before_app_install"
# after_app_install = "crm_pipeline.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "crm_pipeline.utils.before_app_uninstall"
# after_app_uninstall = "crm_pipeline.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "crm_pipeline.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

doc_events = {
    "CRM Pipeline Status": {
        "before_insert": "crm_pipeline.api.set_status_from_type"
    },
}

# Document Events
# ---------------
# Hook on document methods and events


# Overriding Methods
override_whitelisted_methods = {
    "crm.api.doc.get_data": "crm_pipeline.api.get_data",
    "crm.api.doc.get_fields": "crm_pipeline.api.get_fields",
    "crm.fcrm.doctype.crm_view_settings.crm_view_settings.create_or_update_standard_view": "crm_pipeline.api.create_or_update_standard_view",
    "crm.api.activities.get_activities": "crm_pipeline.activities.get_activities",

}

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"crm_pipeline.tasks.all"
# 	],
# 	"daily": [
# 		"crm_pipeline.tasks.daily"
# 	],
# 	"hourly": [
# 		"crm_pipeline.tasks.hourly"
# 	],
# 	"weekly": [
# 		"crm_pipeline.tasks.weekly"
# 	],
# 	"monthly": [
# 		"crm_pipeline.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "crm_pipeline.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "crm_pipeline.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "crm_pipeline.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["crm_pipeline.utils.before_request"]
# after_request = ["crm_pipeline.utils.after_request"]

# Job Events
# ----------
# before_job = ["crm_pipeline.utils.before_job"]
# after_job = ["crm_pipeline.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"crm_pipeline.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
    {
        "dt": "Custom Field",
    },
    {
        "dt": "Client Script",
    },
    {
        "dt": "DocType",
        "filters": [["module", "=", "CRM Pipeline"]],
    },
    {
        "dt": "Property Setter",
    }
]

