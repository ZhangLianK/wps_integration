import json
import requests
import hashlib
import time
import frappe
from frappe.utils.password import get_decrypted_password

# 应用信息
#get app_id and app_key from social login keys
wps_login_key = frappe.get_doc("Social Login Key", "wps")
app_id = wps_login_key.client_id
app_key = get_decrypted_password("Social Login Key", wps_login_key.name, "client_secret")
openapi_host = "https://openapi.wps.cn"


def _sig(content_md5, url, date):
    sha1 = hashlib.sha1(app_key.lower().encode('utf-8'))
    sha1.update(content_md5.encode('utf-8'))
    sha1.update(url.encode('utf-8'))
    sha1.update("application/json".encode('utf-8'))
    sha1.update(date.encode('utf-8'))

    return "WPS-3:%s:%s" % (app_id, sha1.hexdigest())


def request(method, host, uri, body=None, cookie=None, headers=None):
    requests.packages.urllib3.disable_warnings()

    if method == "PUT" or method == "POST" or method == "DELETE":
        body = json.dumps(body)

    if method == "PUT" or method == "POST" or method == "DELETE":
        content_md5 = hashlib.md5(body.encode('utf-8')).hexdigest()
    else:
        content_md5 = hashlib.md5("".encode('utf-8')).hexdigest()

    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    # print date
    header = {"Content-type": "application/json"}
    header['X-Auth'] = _sig(content_md5, uri, date)
    header['Date'] = date
    header['Content-Md5'] = content_md5

    if headers != None:
        header = {}
        for key, value in headers.items():
            header[key] = value

    url = "%s%s" % (host, uri)
    r = requests.request(method, url, data=body,
                         headers=header, cookies=cookie, verify=False)

    print("[response]: status=[%d],URL=[%s],data=[%s]" % (r.status_code, url, r.text))
    print("+++\n")

    return r.status_code, r.text


def get_company_token():
    url = "/oauthapi/v3/inner/company/token?app_id=%s" % (app_id)
    print("[request] url:", url, "\n")

    status, rsp = request("GET", openapi_host, url, None, None, None)
    rsp = json.loads(rsp)

    if rsp.__contains__('company_token'):
        return rsp["company_token"]
    else:
        print("no company-token found in response, authorized failed")
        exit(-1)
        

def get_company_users(company_token, company_uids, status=None):
    """
    获取企业通讯录信息

    :param company_token: 企业授权凭证
    :param company_uids: 成员 id 列表，以逗号分隔的字符串
    :param status: 状态，逗号分隔的字符串, 默认为 None
    :return: 企业成员列表
    """
    url = "/plus/v1/batch/company/company_users"
    query_params = {
        "company_token": company_token,
        "company_uids": company_uids
    }
    if status:
        query_params["status"] = status

    # 构建完整的请求 URL
    query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
    full_url = f"{url}?{query_string}"

    # 使用已有的 request 函数发送请求
    status_code, response = request("GET", openapi_host, full_url)

    # 解析响应
    if status_code == 200:
        data = json.loads(response)
        if data.get("result") == 0:
            return data.get("company_users")
        else:
            print("Error in response:", data.get("result"))
    else:
        print("Failed to get company users, status code:", status_code)

    return None

# 使用示例
# company_token = get_company_token()  # 确保你已经获取了 company_token
# company_users = get_company_users(company_token, "1,2,3")  # 示例的 company_uids
# print(company_users)

def send_message(company_token, app_key, msg_type, content, to_users=None, to_depts=None, to_companies=None, to_chats=None, partner_members=None, biz_type=None, ctx_id=None, company_uid=None, company_id=None, utype=None):
    """
    发送消息到 WPS

    :param company_token: 企业授权凭证
    :param app_key: 应用的 AK，即 app_id
    :param msg_type: 消息内容格式类型
    :param content: 消息内容
    :param to_users: 发送给某个企业的部分人员
    :param to_depts: 发送给对应部门
    :param to_companies: 发送给对应公司
    :param to_chats: 发送给对应群聊
    :param partner_members: 发送给关联组织的部分人员
    :param biz_type: 消息所属业务类型
    :param ctx_id: app_key+ctx_id 映射到消息 id
    :param company_uid: 消息生产者 id
    :param company_id: 消息生产者企业 id
    :param utype: 后续消息更新方式
    :return: 响应数据
    """
    url = "/kopen/woa/v2/dev/app/messages"
    full_url = f"{url}?company_token={company_token}"

    # 构建请求体
    body = {
        "app_key": app_key,
        "msg_type": msg_type,
        "content": content
    }

    if to_users:
        body["to_users"] = to_users
    if to_depts:
        body["to_depts"] = to_depts
    if to_companies:
        body["to_companies"] = to_companies
    if to_chats:
        body["to_chats"] = to_chats
    if partner_members:
        body["partner_members"] = partner_members
    if biz_type:
        body["biz_type"] = biz_type
    if ctx_id:
        body["ctx_id"] = ctx_id
    if company_uid:
        body["company_uid"] = company_uid
    if company_id:
        body["company_id"] = company_id
    if utype:
        body["utype"] = utype

    # 使用已有的 request 函数发送请求
    status_code, response = request("POST", openapi_host, full_url, body=body)

    # 解析响应
    if status_code == 200:
        data = json.loads(response)
        if data.get("result") == 0:
            return data.get("message_id")
        else:
            print("Error in response:", data.get("result"))
    else:
        print("Failed to send message, status code:", status_code)

    return None

# 使用示例
# company_token = get_company_token()  # 确保你已经获取了 company_token
# message_id = send_message(company_token, "your_app_id", 1, {"type": 1, "body": "这是一条纯文本消息"}, to_users={"company_id": "xxxxxxxxxxxx", "company_uids": ["xxxxxxxxxxxx"]})
# print(message_id)


def get_company_info(company_token, status=None):
    """
    获取企业信息

    :param company_token: 企业授权凭证
    :param status: 企业状态，多个状态用逗号分隔，可选
    :return: 企业信息
    """
    url = "/plus/v1/company"
    query_params = {"company_token": company_token}
    if status:
        query_params["status"] = status

    # 构建完整的请求 URL
    query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
    full_url = f"{url}?{query_string}"

    # 使用已有的 request 函数发送请求
    status_code, response = request("GET", openapi_host, full_url)

    # 解析响应
    if status_code == 200:
        data = json.loads(response)
        if data.get("result") == 0:
            return data.get("company")
        else:
            print("Error in response:", data.get("result"))
    else:
        print("Failed to get company info, status code:", status_code)

    return None

# 使用示例
# company_token = get_company_token()  # 确保你已经获取了 company_token
# company_info = get_company_info(company_token)
# print(company_info)

def get_sub_departments(company_token, dept_id, offset, limit, recursive=False):
    """
    获取指定部门下的子部门列表

    :param company_token: 企业授权凭证
    :param dept_id: 部门 id，值为 0 时返回根部门的信息
    :param offset: 下标，从 0 开始
    :param limit: 大小，不超过 1000
    :param recursive: 是否递归获取，默认为 False
    :return: 部门列表
    """
    url = f"/plus/v1/company/depts/{dept_id}/children"
    query_params = {
        "company_token": company_token,
        "offset": offset,
        "limit": limit,
        "recursive": str(recursive).lower()
    }

    # 构建完整的请求 URL
    query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
    full_url = f"{url}?{query_string}"

    # 使用已有的 request 函数发送请求
    status_code, response = request("GET", openapi_host, full_url)

    # 解析响应
    if status_code == 200:
        data = json.loads(response)
        if data.get("result") == 0:
            return data.get("depts")
        else:
            print("Error in response:", data.get("result"))
    else:
        print("Failed to get sub departments, status code:", status_code)

    return None

# 使用示例
# company_token = get_company_token()  # 确保你已经获取了 company_token
# sub_depts = get_sub_departments(company_token, "1", 0, 100)
# print(sub_depts)

def get_batch_department_info(company_token, dept_ids):
    """
    批量获取部门信息

    :param company_token: 企业授权凭证
    :param dept_ids: 部门id列表，以逗号分隔的字符串
    :return: 部门信息数组
    """
    url = "/plus/v1/batch/company/depts"
    query_params = {
        "company_token": company_token,
        "dept_ids": dept_ids
    }

    # 构建完整的请求 URL
    query_string = "&".join([f"{key}={value}" for key, value in query_params.items()])
    full_url = f"{url}?{query_string}"

    # 使用已有的 request 函数发送请求
    status_code, response = request("GET", openapi_host, full_url)

    # 解析响应
    if status_code == 200:
        data = json.loads(response)
        if data.get("result") == 0:
            return data.get("depts")
        else:
            print("Error in response:", data.get("result"))
    else:
        print("Failed to get batch department info, status code:", status_code)

    return None

# 使用示例
# company_token = get_company_token()  # 确保你已经获取了 company_token
# dept_info = get_batch_department_info(company_token, "1,2,3")  # 示例的部门 ID 列表
# print(dept_info)
