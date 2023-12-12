

import json

import frappe
import frappe.utils
from tencent_integration.oauth2_weixin.oauth_weixin import login_via_oauth2, login_via_oauth2_id_token

@frappe.whitelist(allow_guest=True)
def custom(code: str, state: str):
	"""
	Callback for processing code and state for user added providers

	process social login from /api/method/frappe.integrations.custom/<provider>
	"""
	path = frappe.request.path[1:].split("/")
	if len(path) == 4 and path[3]:
		provider = path[3]
		# Validates if provider doctype exists
		if frappe.db.exists("Social Login Key", provider):
			login_via_oauth2(provider, code, state, decoder=decoder_compat)


def decoder_compat(b):
	# https://github.com/litl/rauth/issues/145#issuecomment-31199471
	return json.loads(bytes(b).decode("utf-8"))
