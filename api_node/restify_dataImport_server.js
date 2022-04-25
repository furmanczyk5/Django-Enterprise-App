var restify = require('restify');
var TYPES = require('tedious').TYPES;
var db = require('./db_helper');

// we'll use this one once we import all events:
//var getEventList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_EventList"});
var getEvent =db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Event", "parameters":[{"name":"EventID","type":TYPES.Int}]});

// pulling activities for a particular event (2015 national conference)... down the road will probably change to pull activities from all events EXCEPT 2015 national conference
var getActivityList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ActivityList", "parameters":[{"name":"EventID","type":TYPES.Int}]});
var getActivity = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Activity", "parameters":[{"name":"ActivityID","type":TYPES.Int}]});

// pull everyone or just current national conference participants??
var getContactList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ContactList", "parameters":[{"name":"EventID","type":TYPES.Int}]});
var getContact = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Contact", "parameters":[{"name":"ParticipantID","type":TYPES.Int}]});

// for national conference participants... will need to create more role imports down the road (e.g. CM speakers for other events, authors, publishers, etc.)
//var getParticipantContactRolesList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ContactRoleList", "parameters":[{"name":"EventID","type":TYPES.Int}]});
//var getParticipantContactRoles = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ContactRole", "parameters":[{"name":"ParticipantID","type":TYPES.Int}]});

var getTagTypeList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_TagTypeList"}); 
// there aren't so many tag types, so OK to pull all necessary fields at once in the list

var getTagList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_TagList", "parameters":[{"name":"TagTypeCode","type":TYPES.VarChar}]});

var getTagRelationshipList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Tag_RelatedList", "parameters":[{"name":"TagTypeCode","type":TYPES.VarChar}]});
//var getTag = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Tag", "parameters":[{"name":"TagID","type":TYPES.Int}]});

// tag assignments for various kinds of records
var getActivityTagAssignmentList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ActivityTagAssignmentList", "parameters":[{"name":"EventID","type":TYPES.Int}]});
// once we import all events:
//var getEventTagAssignmentList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_EventTagAssignmentList", "parameters":[{"name":"EventID","type":TYPES.Int}]});

// for once we import pages from c1 into django:
//var getPageContentList = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_ActivityList", "parameters":[{"name":"EventID","type":TYPES.Int}]});
//var getPageContent = db.makeProcedureCaller({"procedure_name":"web.dbo.DjangoExport_Activity", "parameters":[{"name":"EventID","type":TYPES.Int}]});

var getProviderRelationships = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_ProviderRelationship_Get",
		"parameters":[	
		{"name":"ProviderID","type":TYPES.VarChar}
	]
});

// var getCMRegistrationAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Registration_All", 
// 	"parameters":[]
// });

// var getCMCreditClaim = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_CreditClaim", 
// 	"parameters":[
// 		{"name":"UserID","type":TYPES.NVarChar},
// 		{"name":"PeriodCode","type":TYPES.NVarChar},

// ]});

// var getCMLogDates = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Log_Dates", 
// 	"parameters":[{"name":"PeriodCode","type":TYPES.NVarChar}]
// });

// var getCMClaim = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Claim", 
// 	"parameters":[{"name":"ClaimID","type":TYPES.Int}]
// });
// var getProviderEinPurchases = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_Provider_Ein_Purchases", 
// 	"parameters":[{"name":"EinNumber","type":TYPES.NVarChar},
// 				  {"name":"RegistrationPeriodCode","type":TYPES.NVarChar},
// 	]
// });
// var getCMConferenceClaims = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_CreditClaim_Conference", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getEventAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_Event_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getEvent = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_Event", 
// 	"parameters":[{"name":"EventID","type":TYPES.Int}]
// });

// var getEventActivities = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_Event_Activities", 
// 	"parameters":[{"name":"EventID","type":TYPES.Int}]
// });

// var getActivityAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_Activity_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getCMLogAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Log_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getCMLog = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Log", 
// 	"parameters":[
// 		{"name":"UserID","type":TYPES.NVarChar},
// 		{"name":"PeriodCode","type":TYPES.NVarChar},

// ]});

// var getCMCreditClaimAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_CreditClaim_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getCMCreditPeriodAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_CreditPeriod_All", 
// 	"parameters":[]
// });

// var getCMInstructorAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Instructor_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getProviderRelationships = db.makeProcedureCaller({
// 	"procedure_name":"imis_live.dbo.Tedious_ProviderRelationship_Get",
// 		"parameters":[	
// 		{"name":"ProviderID","type":TYPES.VarChar}
// 	]
// });

// var getProviderEventTransactions = db.makeProcedureCaller({	
// 	"procedure_name":"events.dbo.Tedious_Provider_Transactions", 
// 	"parameters":[	
// 		{"name":"ProviderID","type":TYPES.VarChar}
// 	]
// });

// var postUserPasswordLength = db.makeProcedureCaller({	
// 	"procedure_name":"web.dbo.Tedious_PasswordLength_Submit", 
// 	"parameters":[	
// 		{"name":"WebUserID","type":TYPES.VarChar},
// 		{"name":"IsPasswordShort","type":TYPES.Int},
			
// 	]
// });


// var postCMCredits = db.makeProcedureCaller({
// 	"procedure_name":"events.dbo.Tedious_Event_CM_Submit",
// 	"parameters":[
// 		{"name":"WebUserID","type":TYPES.VarChar},
// 		{"name":"EventID","type":TYPES.Int},
// 		{"name":"IsSpeaker","type":TYPES.Int},

// 		{"name":"EventName","type":TYPES.NVarChar},
// 		{"name":"RatingStars","type":TYPES.SmallInt},
// 		{"name":"Comments","type":TYPES.NVarChar},
// 		{"name":"CommentsStatus","type":TYPES.VarChar},

// 		{"name":"CreditNumber","type":TYPES.Decimal, options:{"precision":6,"scale":2} },
// 		{"name":"CreditLawNumber","type":TYPES.Decimal, options:{"precision":6,"scale":2} },
// 		{"name":"CreditEthicsNumber","type":TYPES.Decimal, options:{"precision":6,"scale":2}  },

// 		{"name":"EventBeginDate","type":TYPES.VarChar},
// 		{"name":"EventEndDate","type":TYPES.VarChar},
// 		{"name":"MasterID","type":TYPES.Int},
// 		{"name":"IsDelete", "type":TYPES.Int}
// ]});

// var getEventCMAll = db.makeProcedureCaller({
// 	"procedure_name":"events.dbo.Tedious_Event_CM_All",
// 	"parameters":[{"name":"EventID","type":TYPES.Int}]
// });

// var getCMOrderAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Order_All", 
// 	"parameters":[{"name":"GroupID","type":TYPES.Int}]
// });

// var getCMPurchaseAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Purchase_All", 
// 	"parameters":[{"name":"OrderID","type":TYPES.Int}]
// });

// var getCMPaymentAll = db.makeProcedureCaller({
// 	"procedure_name":"web.dbo.Tedious_CM_Payment_All", 
// 	"parameters":[{"name":"OrderID","type":TYPES.Int}]
// });

var getStoreProductsType = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Products", 
	"parameters":[{"name":"ProductType","type":TYPES.NVarChar}]
});

var getStoreProductsOptions = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Products_Options", 
	"parameters":[{"name":"ProductCode","type":TYPES.NVarChar}]
});

var getStoreProductsPriceRules = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Products_PriceRules", 
	"parameters":[{"name":"OptionID","type":TYPES.VarChar},
				  {"name":"ProductCode","type":TYPES.VarChar}]
});

var getStoreProductsAuthorities = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Products_Authorities", 
	"parameters":[{"name":"ProductCode","type":TYPES.VarChar}]
});

var getOrders = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Orders", 
	"parameters":[{"name":"product_type","type":TYPES.VarChar}]
});

var getPurchases = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Purchases", 
	"parameters":[{"name":"product_type","type":TYPES.VarChar},
				{"name":"order_id","type":TYPES.Int}]
});
var getPayments = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Payments", 
	"parameters":[{"name":"order_id","type":TYPES.Int}]
});

var getProfiles = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUser_Profiles", 
	"parameters":[]
});

var getShippingOptions = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_USC_Shipping", 
	"parameters":[]
});
var getProfilesUploads = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUser_Profiles_Uploads", 
	"parameters":[]
});

var getJobHistory = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_WebUser_Profiles_JobHistory", 
	"parameters":[]
});

var getDegree = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_WebUser_Profiles_Degree", 
	"parameters":[]
});

var getWebUserAll = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_WebUser_All", 
	"parameters":[]
});

var getWebUser = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.Tedious_WebUser_Import", 
	"parameters":[{"name":"webuserid","type":TYPES.VarChar}]
});

var getPurchaseExpiration = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Purchase_Expiration", 
	"parameters":[]
});

var getJobOrders = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Jobs_Orders", 
	"parameters":[]
});


var getJobOrdersItems = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Jobs_Orders_Items", 
	"parameters":[{"name":"OrderID","type":TYPES.Int}]
});


var getExam = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam", 
	"parameters":[]
});

var getExamRegistration = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam_Registration",
	"parameters":[{"name":"ExamCode","type":TYPES.VarChar}]
});

var getExamApplication = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam_Application",
	"parameters":[{"name":"ExamCode","type":TYPES.VarChar},
				  {"name":"ArchiveTypeCode","type":TYPES.VarChar}]
});

var getExamApplicationJobHistory = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam_Application_JobHistory",
	"parameters":[{"name":"ExamArchiveID","type":TYPES.Int}]
});

var getJobsAll = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Jobs_All",
	"parameters":[{"name":"StartJobID","type":TYPES.Int}]
});

var getJobTags = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Job_Tags",
	"parameters":[{"name":"AdID","type":TYPES.Int}]
});

var getExamApplicationArchive = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam_Application_Archive",
	"parameters":[{"name":"ArchiveTypeCode","type":TYPES.VarChar}]
});

var getExamApplicationDegreeHistory = db.makeProcedureCaller({
	"procedure_name":"web.dbo.Tedious_Exam_Application_DegreeHistory",
	"parameters":[{"name":"ExamArchiveID","type":TYPES.Int}]
});

var getAICPExamResults = db.makeProcedureCaller({
	"procedure_name":"imis_live.dbo.DataImport_AICP_Exam_Results",
	"parameters":[{"name":"ExamCode","type":TYPES.VarChar}]
});
var server = restify.createServer();

// TO DO... SOME KIND OF API AUTHENTICATION...  

server.get('/dataimport/activity/list/:EventID', getActivityList);
server.get('/dataimport/activity/:ActivityID', getActivity);

server.get('/dataimport/contact/list/:EventID', getContactList);
server.get('/dataimport/contact/:ParticipantID', getContact);

server.get('/dataimport/tagtype/list/', getTagTypeList);
server.get('/dataimport/tag/list/:TagTypeCode', getTagList);
server.get('/dataimport/tagrelationship/list/:TagTypeCode', getTagRelationshipList);
server.get('/dataimport/provider/relationships', getProviderRelationships);

server.get('/dataimport/products/:ProductType/all', getStoreProductsType);
server.get('/dataimport/products/:ProductCode/options', getStoreProductsOptions);
server.get('/dataimport/products/:ProductCode/options/:OptionID/prices', getStoreProductsPriceRules);

server.get('/dataimport/products/:ProductCode/authorities', getStoreProductsAuthorities);

server.get('/dataimport/orders/product_type/:product_type', getOrders);
server.get('/dataimport/orders/:order_id/product_type/:product_type/purchases', getPurchases);
server.get('/dataimport/orders/:order_id/payments', getPayments);

server.get('/dataimport/shipping', getShippingOptions);


// server.get('/dataimport/profiles/:UserGroup', getProfiles);

// server.get('/dataimport/profiles/:UserGroup', getProfiles);

server.get('/dataimport/profiles', getProfiles);
server.get('/dataimport/profiles/uploads', getProfilesUploads);

server.get('/dataimport/profiles/jobhistory', getJobHistory);

server.get('/dataimport/profiles/degree', getDegree);

server.get('/dataimport/webuser/all', getWebUserAll);

server.get('/dataimport/webuser/:webuserid', getWebUser);

server.get('/dataimport/webuser/purchases/expirationtime', getPurchaseExpiration);

server.get('/dataimport/jobs/all/:StartJobID', getJobsAll);


server.get('/dataimport/jobs/tags/:AdID', getJobTags);

server.get('/dataimport/jobs/orders', getJobOrders);

server.get('/dataimport/jobs/orders/:OrderID', getJobOrdersItems);

server.get('/dataimport/exam', getExam);

server.get('/dataimport/examregistration/:ExamCode', getExamRegistration);

server.get('/dataimport/examapplication/examcode/:ExamCode/archivetypecode/:ArchiveTypeCode', getExamApplication);

server.get('/dataimport/examapplication/archive/:ArchiveTypeCode', getExamApplicationArchive);

server.get('/dataimport/examapplication/jobhistory/:ExamArchiveID', getExamApplicationJobHistory);

server.get('/dataimport/examapplication/degreehistory/:ExamArchiveID', getExamApplicationDegreeHistory);

server.get('/dataimport/examregistration/results/:ExamCode', getAICPExamResults);

// server.get('/event/:GroupID/all', getEventAll);

// server.get('/event/:EventID', getEvent);

// server.get('/event/:EventID/activities', getEventActivities);

// server.get('/activity/:GroupID/all', getActivityAll);

// server.get('/cm/log/:GroupID/all', getCMLogAll);

// server.get('/cm/creditclaim/:GroupID/all', getCMCreditClaimAll);

// server.get('/cm/creditperiod/all', getCMCreditPeriodAll);

// server.get('/cm/instructor/:GroupID/all', getCMInstructorAll);

// server.get('/cm/order/:GroupID/all', getCMOrderAll);

// server.get('/cm/purchase/:OrderID/all', getCMPurchaseAll);

// server.get('/cm/payment/:OrderID/all', getCMPaymentAll);

// server.get('/cm/approved/application/:GroupID/all', getCMApplicationAll);

// server.get('/cm/registration/all', getCMRegistrationAll);

// server.get('/cm/log/:UserID/:PeriodCode', getCMLog);

// server.get('/cm/claim/:ClaimID', getCMClaim);

// server.get('/cm/creditclaim/:UserID/:PeriodCode', getCMCreditClaim);

// server.get('/cm/provider/purchase/:EinNumber/:RegistrationPeriodCode', getProviderEinPurchases);

// server.get('/cm/dates/:PeriodCode', getCMLogDates);

// server.get('/cm/conference/claims/:GroupID', getCMConferenceClaims);

// server.post('contact/passwordlength', postUserPasswordLength);

//server.head('/user/:WebUserID', getWebUser);

// server.post('/event/creditclaim', postCMCredits);

// server.get('/event/:EventID/cm/all', getEventCMAll);
// server.get('/provider/events/transactions/:ProviderID', getProviderEventTransactions);
// server.get('/provider/relationships', getProviderRelationships);

server.listen(8081, function(){
	console.log('%s listening at %s', server.name, server.url);
});