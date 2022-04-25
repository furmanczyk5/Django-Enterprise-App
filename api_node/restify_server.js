var restify = require('restify');
var TYPES = require('tedious').TYPES;
var fs = require('fs');
var db = require('./db_helper');
var apa_webuser = require('./apa_WebUser');

var getWebUser = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.Tedious_WebUser_Get", 
	"parameters":[{"name":"WebUserID","type":TYPES.VarChar}]
});

var getWebUserGroups = apa_webuser.get_WebUserGroups;


var getConferenceAttendeeList = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_NPC_Attendees",
	"parameters":[{"name":"WebUserID", "type":TYPES.VarChar}]
});

var getWebUserAll = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUser_Import",
	"parameters":[{"name":"GroupID","type":TYPES.Int}]
});

var getContactEmailExists = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_IMIS_Contacts_EmailExists_GET",
	"parameters":[{"name":"Email","type":TYPES.NVarChar}]
});

var postNonMemberAccount = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_MyAPA_NonMember_CreateSubmit",
	"parameters":[
		{"name":"Prefix","type":TYPES.NVarChar},
		{"name":"FirstName","type":TYPES.NVarChar},

		{"name":"MiddleName","type":TYPES.NVarChar},
		{"name":"LastName","type":TYPES.NVarChar},
		{"name":"Suffix","type":TYPES.NVarChar},
		{"name":"PasswordHintCode","type":TYPES.NVarChar},

		{"name":"PasswordHintAnswer","type":TYPES.NVarChar},
		{"name":"Email","type":TYPES.NVarChar},
		{"name":"Company","type":TYPES.NVarChar},

		{"name":"Address1","type":TYPES.NVarChar},
		{"name":"Address2","type":TYPES.NVarChar},
		{"name":"City","type":TYPES.NVarChar},
		{"name":"StateProvince", "type":TYPES.NVarChar},
		{"name":"Zip","type":TYPES.NVarChar},
		{"name":"Country", "type":TYPES.NVarChar},
		{"name":"Phone","type":TYPES.NVarChar},
]});

var postProviderCompany= db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_MyAPA_ProviderCompany_CreateSubmit",
	"parameters":[
		{"name":"Company","type":TYPES.NVarChar},
		{"name":"Address1","type":TYPES.NVarChar},
		{"name":"Address2","type":TYPES.NVarChar},
		{"name":"City","type":TYPES.NVarChar},
		{"name":"StateProvince", "type":TYPES.NVarChar},
		{"name":"Zip","type":TYPES.NVarChar},
		{"name":"Country", "type":TYPES.NVarChar},
		{"name":"Phone", "type":TYPES.NVarChar},
		{"name":"Website", "type":TYPES.NVarChar},
]});

var postMemberGeneralInfo = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUser_Create",
	"parameters":[
		{"name":"Prefix","type":TYPES.NVarChar},
		{"name":"FirstName","type":TYPES.NVarChar},
		{"name":"MiddleName","type":TYPES.NVarChar},
		{"name":"LastName","type":TYPES.NVarChar},
		{"name":"Suffix","type":TYPES.NVarChar},

		{"name":"PasswordHintCode","type":TYPES.NVarChar},
		{"name":"PasswordHintAnswer","type":TYPES.NVarChar},
		{"name":"Email","type":TYPES.NVarChar},
		{"name":"WebUserID","type":TYPES.NVarChar},
		{"name":"BirthDate","type":TYPES.NVarChar},
]});

var getFreeStudentsList = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_FreeStudents_Students_List", 
	"parameters":[]
});


var postImisEvent = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Event_Import_Submit",
	"parameters": [
		{"name": "EventType", "type": TYPES.VarChar},

		{"name":"ConferenceCode","type":TYPES.VarChar},
		{"name":"EventCode","type":TYPES.VarChar},
		{"name":"EventName","type":TYPES.VarChar},
		{"name":"BeginTime","type":TYPES.VarChar},
		{"name":"EndTime","type":TYPES.VarChar},
		{"name":"Description","type":TYPES.VarChar},
		{"name":"Address1","type":TYPES.VarChar},
		{"name":"Address2","type":TYPES.VarChar},
		{"name":"City","type":TYPES.VarChar},
		{"name":"State","type":TYPES.VarChar},
		{"name":"Zip","type":TYPES.VarChar},
		{"name":"Country","type":TYPES.VarChar},

		{"name":"ProductMaxQuantity","type":TYPES.Int},
		{"name":"ProductCode","type":TYPES.VarChar},
		{"name":"ProductTitle","type":TYPES.VarChar},
		{"name":"ProductPrice","type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"ProductGLAccount","type":TYPES.VarChar},
		{"name":"ProductStatus","type":TYPES.VarChar},
		{"name":"ProductDescription","type":TYPES.VarChar},
	]
});


var postImisEventProductOption = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Event_ProductOption_Import_Submit",
	"parameters": [

		{"name":"ConferenceCode","type":TYPES.VarChar},
		{"name":"BeginTime","type":TYPES.VarChar},
		{"name":"EndTime","type":TYPES.VarChar},
		{"name":"Code","type":TYPES.VarChar},
		{"name":"Title","type":TYPES.VarChar},
		{"name":"Price","type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"GLAccount","type":TYPES.VarChar},
		{"name":"Status","type":TYPES.VarChar},
	]
});

//////////////////////////////////////////////////////////////////////////////////////
// IMIS TRANSACTIONS
var getImisTransaction = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Transaction_Create", 
	"parameters":[]
});

var postImisInvoice = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Invoice_Create", 
	"parameters":[{"name":"WebUserID","type":TYPES.VarChar},
				  {"name":"ConferenceCode","type":TYPES.VarChar},
	]
});


var postImisPurchaseTransaction = db.makeProcedureCaller({	
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Transaction_Purchase_Submit", 
	"parameters":[	
		{"name":"ProductTypeCode","type":TYPES.VarChar},
		{"name":"OrderID","type":TYPES.Int},
		{"name":"WebUserID","type":TYPES.VarChar},
		{"name":"ProductCode","type":TYPES.VarChar},
		{"name":"ProductOption","type":TYPES.VarChar},
		{"name":"Quantity","type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"EventQuantity","type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"ProductPrice","type":TYPES.Decimal, options:{"precision":9,"scale":2}},
		{"name":"Amount","type":TYPES.Decimal, options:{"precision":9,"scale":2}},
		{"name":"ConferenceCode","type":TYPES.VarChar},
		{"name":"TransNumber","type":TYPES.Int},
		{"name":"PurchaseID","type":TYPES.Int},
		{"name":"BatchNumber","type":TYPES.VarChar},
		{"name":"BatchTime","type":TYPES.VarChar},
		{"name":"IsStandby","type":TYPES.Int},
		{"name":"EventPurchaseTotal","type":TYPES.Decimal, options:{"percision":6,"scale":2}},
		{"name":"EventPaymentTotal","type":TYPES.Decimal, options:{"percision":6,"scale":2}},
		{"name":"EventBalanceTotal","type":TYPES.Decimal, options:{"percision":6,"scale":2}},
		{"name":"DjangoProductCode","type":TYPES.VarChar},
		{"name":"InvoiceReferenceNumber","type":TYPES.Int},
		{"name":"IsChapterAdmin","type":TYPES.Int},
		{"name":"SourceSystem","type":TYPES.VarChar},
		
			
]});

var postImisARTransaction = db.makeProcedureCaller({	
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Transaction_AR_Submit", 
	"parameters":[	
		{"name":"OrderID","type":TYPES.Int},
		{"name":"WebUserID","type":TYPES.VarChar},
		{"name":"Balance","type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"TransNumber","type":TYPES.Int},
		{"name":"BatchNumber","type":TYPES.VarChar},
		{"name":"BatchDate","type":TYPES.VarChar},
		{"name":"InvoiceReferenceNumber","type":TYPES.Int},
			
]});

var postImisPaymentTransaction = db.makeProcedureCaller({	
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Transaction_Payment_Submit", 
	"parameters":[	
		{"name":"OrderID","type":TYPES.Int},
		{"name":"WebUserID","type":TYPES.VarChar},
		{"name":"Method","type":TYPES.VarChar},
		{"name":"Amount","type":TYPES.Decimal, options:{"precision":9,"scale":2}},	
		{"name":"BatchTime","type":TYPES.VarChar},
		{"name":"BatchNumber","type":TYPES.VarChar},
		{"name":"TransNumber","type":TYPES.Int},
		{"name":"PaymentID","type":TYPES.Int},
		{"name":"PNRef","type":TYPES.VarChar},
		{"name":"InvoiceReferenceNumber","type":TYPES.Int},
		{"name":"IsChapterAdmin","type":TYPES.Int},
		{"name":"SourceSystem","type":TYPES.VarChar},
]});


var postImisInvoiceTransaction = db.makeProcedureCaller({	
	"procedure_name":"imis_live.dbo.Tedious_iMIS_Transaction_Invoice_Submit", 
	"parameters":[	
		{"name":"WebUserID","type":TYPES.VarChar},
		{"name":"TransNumber","type":TYPES.Int},
]});

//////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////////////
// JOIN & INVOICE 

var postContactsSecurity = db.makeProcedureCallerSingleRecord({	
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Security_POST", 
	"parameters":[	
		{"name":"prefix_name","type":TYPES.NVarChar},
		{"name":"first_name","type":TYPES.NVarChar},
		{"name":"middle_name","type":TYPES.NVarChar},
		{"name":"last_name","type":TYPES.NVarChar},
		{"name":"suffix_name","type":TYPES.NVarChar},
		{"name":"password_hint_code","type":TYPES.NVarChar},
		{"name":"password_hint_answer","type":TYPES.NVarChar},
		{"name":"email","type":TYPES.NVarChar},
		{"name":"email_secondary","type":TYPES.NVarChar},
		{"name":"designation","type":TYPES.NVarChar},
		{"name":"birth_date","type":TYPES.NVarChar},
		{"name":"mobile_phone","type":TYPES.NVarChar},
		{"name":"work_phone","type":TYPES.NVarChar},
		{"name":"home_phone","type":TYPES.NVarChar},
		{"name":"informal_name","type":TYPES.NVarChar},

]});

var putContactsSecurity = db.makeProcedureCallerSingleRecord({	
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Security_PUT", 
	"parameters":[	
		{"name":"webuserid","type":TYPES.NVarChar},	
		{"name":"prefix_name","type":TYPES.NVarChar},
		{"name":"first_name","type":TYPES.NVarChar},
		{"name":"middle_name","type":TYPES.NVarChar},
		{"name":"last_name","type":TYPES.NVarChar},
		{"name":"suffix_name","type":TYPES.NVarChar},
		{"name":"password_hint_code","type":TYPES.NVarChar},
		{"name":"password_hint_answer","type":TYPES.NVarChar},
		{"name":"email","type":TYPES.NVarChar},
		{"name":"email_secondary","type":TYPES.NVarChar},
		{"name":"designation","type":TYPES.NVarChar},
		{"name":"birth_date","type":TYPES.NVarChar},
		{"name":"mobile_phone","type":TYPES.NVarChar},
		{"name":"work_phone","type":TYPES.NVarChar},
		{"name":"home_phone","type":TYPES.NVarChar},
		{"name":"informal_name","type":TYPES.NVarChar},
]});

var getContactsSecurity = db.makeProcedureCallerSingleRecord({	
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Security_GET", 
	"parameters":[	
		{"name":"webuserid","type":TYPES.NVarChar},
		
]});

// ADDRESS
var postContactsAddresses = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Addresses_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"address_1","type":TYPES.NVarChar},
		{"name":"address_2","type":TYPES.NVarChar},
		{"name":"city","type":TYPES.NVarChar},
		{"name":"state_province", "type":TYPES.NVarChar},
		{"name":"zip","type":TYPES.NVarChar},
		{"name":"country", "type":TYPES.NVarChar},
		{"name":"company", "type":TYPES.NVarChar},

		{"name":"is_primary","type":TYPES.Int},
		{"name":"is_billing", "type":TYPES.Int},
		
]});

var putContactsAddresses = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Addresses_PUT",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"address_num","type":TYPES.Int},
		{"name":"address_1","type":TYPES.NVarChar},
		{"name":"address_2","type":TYPES.NVarChar},
		{"name":"city","type":TYPES.NVarChar},
		{"name":"state_province", "type":TYPES.NVarChar},
		{"name":"zip","type":TYPES.NVarChar},
		{"name":"country", "type":TYPES.NVarChar},
		{"name":"company", "type":TYPES.NVarChar},
		{"name":"is_primary","type":TYPES.Int},
		{"name":"is_billing", "type":TYPES.Int},
		
]});
var getContactsAddresses = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Addresses_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"is_primary","type":TYPES.Int}, //defaults to 0 to return all addresses
		
]});

var delContactsAddresses = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Addresses_DEL",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"address_num","type":TYPES.Int},
		
]});

// DEMOGRAPHICS
var postContactsDemographics = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Demographics_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"functional_title","type":TYPES.NVarChar},
		{"name":"salary_range","type":TYPES.NVarChar},
		{"name":"origin","type":TYPES.NVarChar},
		{"name":"span_hisp_latino","type":TYPES.NVarChar},
		{"name":"ethnicity", "type":TYPES.NVarChar},
		{"name":"ai_an","type":TYPES.NVarChar},
		{"name":"asian_pacific", "type":TYPES.NVarChar},
		{"name":"ethnicity_other", "type":TYPES.NVarChar},
		{"name":"origin_noanswer","type":TYPES.Int},
		{"name":"ethnicity_noanswer", "type":TYPES.Int},
		{"name":"specialty", "type":TYPES.NVarChar},
		{"name":"gender", "type":TYPES.NVarChar},
		{"name":"gender_other", "type":TYPES.NVarChar},
		{"name":"exclude_planning_print","type":TYPES.Int},
		{"name":"join_source", "type":TYPES.NVarChar}
]});

var getContactsDemographics = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Demographics_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
]});


// ADVOCACY
var postContactsAdvocacy = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Advocacy_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"grassroots_member","type":TYPES.Int},		
		
]});

var getContactsAdvocacy = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Advocacy_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
]});


// SUBSCRIPTIONS
var getContactsSubscriptions = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Subscriptions_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"product_code","type":TYPES.NVarChar},
		{"name":"has_bill_amount","type":TYPES.Int},

]});

// DEMOGRAPHICS
var postContactsCMLog = db.makeProcedureCallerSingleRecord({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_CMLog_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"periodcode","type":TYPES.NVarChar},
		{"name":"general", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"law", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"ethics", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"status", "type":TYPES.NVarChar},
		{"name":"credits_required", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"begin_time", "type":TYPES.NVarChar},
		{"name":"end_time", "type":TYPES.NVarChar},
		{"name":"reinstatement_end_time", "type":TYPES.NVarChar},

		{"name":"self_reported", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"is_author", "type":TYPES.Decimal, options:{"precision":6,"scale":2}},
		{"name":"period_iscurrent", "type":TYPES.Int},	
]});
//////////////////////////////////////////////////////////////////////////////////////
// single api calls for each section (ie demographics, contact info)

var getContactsOrganizations = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
]});
var getOrganizationsContacts = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Organizations_Contacts_GET",
	"parameters":[
		{"name":"co_id","type":TYPES.NVarChar},
]});

var postContactsOrganizations = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"record_type","type":TYPES.NVarChar},
			
]});
var postContactsOrganizationsRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_Relationships_POST",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"relation_type","type":TYPES.NVarChar},
		{"name":"co_id","type":TYPES.NVarChar},
			
]});

var delContactsOrganizationsRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_Relationships_DEL",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"relation_type","type":TYPES.NVarChar},
		{"name":"co_id","type":TYPES.NVarChar},
			
]});

var putContactsOrganizationsPAS = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_PAS_PUT",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"pas_code","type":TYPES.NVarChar},
			
]});
var putContactsOrganizationsRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_Relationships_PUT",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"relation_type","type":TYPES.NVarChar},
		{"name":"co_id","type":TYPES.NVarChar},
			
]});

var getContactsOrganizationsRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Organizations_Relationships_GET",
	"parameters":[
		{"name":"co_id","type":TYPES.NVarChar},
		{"name":"relation_type","type":TYPES.NVarChar},
]});

var getContactsRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Relationships_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"relation_type","type":TYPES.NVarChar},
]});

var getContactsPreferences = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Preferences_GET",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
]});

var putContactsPreferences = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_Preferences_PUT",
	"parameters":[
		{"name":"webuserid","type":TYPES.NVarChar},
		{"name":"incl_interact","type":TYPES.Int},
		{"name":"incl_tuesdays","type":TYPES.Int},
		{"name":"incl_bookstore","type":TYPES.Int},
		{"name":"incl_survey","type":TYPES.Int},
		{"name":"incl_apa_marketing","type":TYPES.Int},
		{"name":"incl_maillist","type":TYPES.Int},
		{"name":"incl_natlconf","type":TYPES.Int},
		{"name":"incl_china","type":TYPES.Int},
		{"name":"incl_otherconf","type":TYPES.Int},
		{"name":"incl_planning","type":TYPES.Int},
		{"name":"incl_japa","type":TYPES.Int},
		{"name":"incl_japanews","type":TYPES.Int},
		{"name":"incl_zp","type":TYPES.Int},
		{"name":"incl_pel","type":TYPES.Int},
		{"name":"incl_pas","type":TYPES.Int},
		{"name":"incl_commissioner","type":TYPES.Int},
		{"name":"incl_apaadvocate","type":TYPES.Int},
		{"name":"incl_insurance","type":TYPES.Int},
		{"name":"incl_website","type":TYPES.Int},
		{"name":"excl_planning_print","type":TYPES.Int},
]});

var getWebUserGroupsTest = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebGroups", 
	"parameters":[{"name":"WebUserID","type":TYPES.VarChar}]
});

var getContactID = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUserID", 
	"parameters":[{"name":"email","type":TYPES.VarChar},]
});

var getContactsExamApplications = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Contacts_ExamApplications_GET", 
	"parameters":[{"name":"webuserid","type":TYPES.VarChar},]
});

var getiMISSubscriptions = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Subscriptions_GET", 
	"parameters":[{"name":"ProductCode","type":TYPES.VarChar},]
});

var getiMISChapter= db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Chapter_GET", 
	"parameters":[{"name":"zip_code","type":TYPES.VarChar},]
});

var getSchoolAccredited = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_School_Accredited_GET", 
	"parameters":[]
});

// TO DO... the _POST sp name (API_iMIS_School_Accredited_POST) is misleading because not used for POST method and no data is updated... should change name to _GET
var getSchoolAccreditedCheck = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_School_Accredited_POST", 
	"parameters":[{"name":"SchoolID","type":TYPES.VarChar},
				  {"name":"DegreeLevel","type":TYPES.VarChar},
				  {"name":"DegreeDate","type":TYPES.NVarChar},]
});

var postCMLogDrop = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_CM_Log_Drop_POST", 
	"parameters":[{"name":"webuserid","type":TYPES.VarChar},
				  {"name":"period_code","type":TYPES.VarChar},]
});

var postCMLogBackupCreate = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_CM_Backup_Log_Drop_POST", 
	"parameters":[{"name":"period_code","type":TYPES.VarChar},]
});

var getSchool = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Organizations_GET", 
	"parameters":[{"name":"webuserid","type":TYPES.VarChar},]
});

var getSchoolAdmins = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_School_Admins_GET", 
	"parameters":[{"name":"school_id","type":TYPES.VarChar},]
});

var postSchoolStudent = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.API_iMIS_Schools_Students_POST", 
	"parameters":[
				{"name":"school_id","type":TYPES.NVarChar},	
				{"name":"first_name","type":TYPES.NVarChar},
				{"name":"middle_name","type":TYPES.NVarChar},
				{"name":"last_name","type":TYPES.NVarChar},
				{"name":"expected_graduation_date","type":TYPES.NVarChar},
				{"name":"degree_type","type":TYPES.NVarChar},
				{"name":"student_id","type":TYPES.NVarChar},
				{"name":"birth_date","type":TYPES.NVarChar},

				{"name":"address1","type":TYPES.NVarChar},
				{"name":"address2","type":TYPES.NVarChar},
				{"name":"city","type":TYPES.NVarChar},
				{"name":"state","type":TYPES.NVarChar},
				{"name":"country","type":TYPES.NVarChar},
				{"name":"zip_code","type":TYPES.NVarChar},

				{"name":"secondary_address1","type":TYPES.NVarChar},
				{"name":"secondary_address2","type":TYPES.NVarChar},
				{"name":"secondary_city","type":TYPES.NVarChar},
				{"name":"secondary_state","type":TYPES.NVarChar},
				{"name":"secondary_country","type":TYPES.NVarChar},
				{"name":"secondary_zip_code","type":TYPES.NVarChar},


				{"name":"email","type":TYPES.NVarChar},
				{"name":"phone","type":TYPES.NVarChar},
				{"name":"secondary_phone","type":TYPES.NVarChar},
				{"name":"secondary_email","type":TYPES.NVarChar},

				{"name":"registration_period","type":TYPES.NVarChar},
				{"name":"registration_year","type":TYPES.NVarChar},

	]
});

if(db.hostname=='conference' || db.hostname=='conference-staging'){
	server = restify.createServer({
	    certificate: fs.readFileSync('/etc/nginx/ssl/Conference.crt'),
	    key: fs.readFileSync('/etc/nginx/ssl/Conference_planning_org.key')
	});
}else{
	server = restify.createServer();
}

server.use(restify.bodyParser());
server.use(restify.queryParser());

// TO DO... SOME KIND OF API AUTHENTICATION...  



// JOIN APA REST API STUFF

// an example url with the filter would probably be: /api/0\.2/contacts/:WebUserID/addresses/?IsPrimaryMail=True

// // FOR CONSIDERATION... PULL DJANGO-BASED DATA LIKE THIS?
// server.get('/api/0\.2/profiles/?state=IL', getProfilesFromDjangoUrl); // e.g. pulls django-based profiles? (bio, etc.)
// server.get('/api/0\.2/events/9000321/activities/', getActivitiesFromDjangoUrl); // activities at the national conference
// // SHOULD ALSO LOOK AT: http://www.django-rest-framework.org/


server.get('/api/0\.2/contacts/:webuserid/addresses', getContactsAddresses);
server.post('/api/0\.2/contacts/:webuserid/addresses', postContactsAddresses);
server.put('/api/0\.2/contacts/:webuserid/addresses/:address_num', putContactsAddresses);
server.del('/api/0\.2/contacts/:webuserid/addresses/:address_num', delContactsAddresses);

server.get('/api/0\.2/contacts/:webuserid/demographics', getContactsDemographics);
server.post('/api/0\.2/contacts/:webuserid/demographics', postContactsDemographics);

server.get('/api/0\.2/contacts/:webuserid/advocacy', getContactsAdvocacy);
server.post('/api/0\.2/contacts/:webuserid/advocacy', postContactsAdvocacy);

server.get('/api/0\.2/contacts/emailexists', getContactEmailExists);


server.post('/api/0\.2/contacts', postContactsSecurity);
server.put('/api/0\.2/contacts/:webuserid', putContactsSecurity);
server.get('/api/0\.2/contacts/:webuserid', getContactsSecurity);

server.get('/contact/email/:email', getContactID);

server.get('/api/0\.2/contacts/:webuserid/subscriptions', getContactsSubscriptions);

server.post('/api/0\.2/contacts/:webuserid/cmlog/:periodcode', postContactsCMLog);
//////////////////

server.get('/api/0\.2/contacts/:webuserid/organizations', getContactsOrganizations);
server.get('/api/0\.2/organizations/:co_id/contacts', getOrganizationsContacts);
server.post('/api/0\.2/contacts/:webuserid/organizations', postContactsOrganizations);
server.post('/api/0\.2/contacts/:webuserid/organizations/:co_id/relationships', postContactsOrganizationsRelationships);
server.put('/api/0\.2/contacts/:webuserid/organizations/:co_id/relationships', putContactsOrganizationsRelationships);
server.del('/api/0\.2/contacts/:webuserid/organizations/:co_id/relationships', delContactsOrganizationsRelationships);
server.put('/api/0\.2/contacts/:webuserid/organizations/pas', putContactsOrganizationsPAS);
server.get('/contact/:WebUserID', getWebUser);
server.get('/contact/:WebUserID/webgroups', getWebUserGroups);
server.get('/contact/:WebUserID/test', getWebUserGroupsTest);

server.get('/api/0\.2/contacts/:webuserid/preferences', getContactsPreferences);
server.put('/api/0\.2/contacts/:webuserid/preferences', putContactsPreferences);

// // eventually will want something like: 
// server.get('/api/0\.2/contacts/:WebUserID/webgroups', getWebUserGroups); // to pull from both iMIS and django/postgres

server.get('/conference/attendee/list', getConferenceAttendeeList);

server.post('/account/nonmember/create', postNonMemberAccount);
server.post('/account/provider/create', postProviderCompany);

server.post('/account/member/generalinfo', postMemberGeneralInfo);

server.get('contact/:GroupID/all', getWebUserAll);

server.post('/imis/payment/create', postImisPaymentTransaction);

server.post('/imis/purchase/create', postImisPurchaseTransaction);

server.post('/imis/invoice', postImisInvoiceTransaction);

server.post('/imis/ar/create', postImisARTransaction);

server.post('/imis/invoice/create', postImisInvoice);

server.get('/imis/transaction/create', getImisTransaction);

server.get('/freestudents/list', getFreeStudentsList);

server.post('/imis/import/event', postImisEvent);
server.post('/imis/import/event/productoption', postImisEventProductOption);

server.get('/api/0\.2/contacts/organizations/:co_id/relationships', getContactsOrganizationsRelationships);

server.get('/api/0\.2/contacts/:webuserid/relationships', getContactsRelationships);

server.get('/api/0\.2/contacts/:webuserid/examapplications', getContactsExamApplications);

server.get('/api/0\.2/subscriptions/:ProductCode', getiMISSubscriptions);

server.get('/api/0\.2/chapter/:zip_code', getiMISChapter);

// CLEAN THIS UP TO FOLLOW OUR COMMON NAMING CONVENTIONS!! (SCHOOL SHOULD BE PLURAL)

server.get('/api/0\.2/schools/accredited', getSchoolAccredited);

server.get('/api/0\.2/school/:SchoolID/accredited', getSchoolAccreditedCheck);

server.post('/api/0\.2/cm/period/:period_code/backup-tables/create/', postCMLogBackupCreate);

server.post('/api/0\.2/contacts/:webuserid/cm/period/:period_code/log/drop', postCMLogDrop);

server.get('/api/0\.2/school/:webuserid', getSchool);

server.get('/api/0\.2/school/:school_id/admins', getSchoolAdmins);

server.post('/api/0\.2/school/:school_id/students/create', postSchoolStudent);

server.listen(8080, function(){
	console.log('%s listening at %s', server.name, server.url);
});
