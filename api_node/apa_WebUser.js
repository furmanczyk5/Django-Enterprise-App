var db = require('./db_helper');
var TYPES = require('tedious').TYPES;
var fs = require('fs');
var async = require('async');
//designed to work with webframeworks like express, or restify
var path = require('path');

function get_WebUserGroups(req, res, next){

	var _webuserid = req.params.WebUserID;
	var _webuser = WebUser(_webuserid);

	// TODO: Change this back to permission_groups.json
	var filePath = path.join(__dirname + '/../myapa/', 'permission_groups.json');
	// var filePath = path.join(__dirname + '/../myapa/tests/permissions/', 'permission_groups_scratch_file.json');
	console.log(filePath);

	async.parallel({
		webgroups: function(callback){
			fs.readFile(filePath, 'utf8', function(error,data){
				if(error) throw error;
				var test = JSON.parse(data);
				callback(error,test);
			});
		},
		tedious_webgroups: function(callback){
			db.callProcedure({
				"procedure_name":"web.dbo.Tedious_WebGroups",
				"parameters":[{"name":"WebUserID","type":TYPES.VarChar,"value":_webuser.ID}]
			},callback);
		}

	}, function(err, results){
	
		res.setHeader('content-type', 'application/json');
		res.send(_webuser.processWebUserGroupsData(results));
		next();
	});
}


// create object with properties and methods representing a Web User
function WebUser(WebUserID){

	self = this;
	this.ID = WebUserID;

	this.hasWebUserID = function(){
		return !!self.ID;
	};


	//NOTE: Won't work if we pass a condition in regards to a particular field. Add condition field param later if needed.
	// field2 value is only checked when condition is null.
	this.hasFieldValue = function(table, field, value, field2, value2, condition){

		isValid = false;

		if (condition == null)
		{
			for(var i = 0; i < self.tedious_webgroups.length; i++){
				
				if(self.tedious_webgroups[i]["TABLE_NAME"] == table && self.tedious_webgroups[i][field] == value && (field2 == null || self.tedious_webgroups[i][field2] == value2) ) {
					isValid = true;
					break;
				}	
			}
		}

		//condition = not are valid until requirement is found
		if (condition == "not")
		{
			isValid = true;

			for(var i = 0; i < self.tedious_webgroups.length; i++){
				
				if(self.tedious_webgroups[i]["TABLE_NAME"] == table && self.tedious_webgroups[i][field] == value ) {
					isValid = false;
					break;
				}	
			}

		}
		if (condition =="startswith")
		{
			isValid = false;

			for(var i = 0; i < self.tedious_webgroups.length; i++){
				
				if(self.tedious_webgroups[i]["TABLE_NAME"] == table && self.tedious_webgroups[i][field].lastIndexOf(value, 0) == 0 ) {
					isValid = true;
					break;
				}	
			}
		}
		if (condition =="exists")
		{
			isValid = false;

			for(var i = 0; i < self.tedious_webgroups.length; i++){
				
				if(self.tedious_webgroups[i]["TABLE_NAME"] == table && self.tedious_webgroups[i][field]) {
					isValid = true;
					break;
				}	
			}
		}
		return isValid;
	};

	

	// given all db queries and possible webuser groups, return object of keys + values (group, bool)
	this.processWebUserGroupsData = function(data){

		var _WebUserGroups = [];

		//self.Name = data.Name.data || self.Name || [];
		self.tedious_webgroups = data.tedious_webgroups.data || [];
		for(group in data.webgroups){
			
			if ( data.webgroups[group].source == "SQL"){
				var hasgroup;
				
				for (var x = 0; x < data.webgroups[group].requisites.requisites_list.length; x++){
					
					for(var i = 0; i < data.webgroups[group].requisites.requisites_list[x].requirements.length; i++){
						hasgroup = checkRequirement(data.webgroups[group].requisites.requisites_list[x].requirements[i]);
						
						if(data.webgroups[group].requisites.requisites_list[x].logical == "or" && hasgroup) break; //break if any are true

						else if(data.webgroups[group].requisites.requisites_list[x].logical == "and" && !hasgroup) break;
					}

					if (hasgroup) _WebUserGroups[_WebUserGroups.length] = group;
				}
			}
		}
		return _WebUserGroups;

		function checkRequirement(requirement){

			var ret_val = false;

			switch(requirement.requirement){
				case "hasWebUserID":
					ret_val = self.hasWebUserID();
					break;
				case "hasFieldValue":
					ret_val = self.hasFieldValue(requirement.table, requirement.field, requirement.value, requirement.field2, requirement.value2, requirement.condition);
					break;
				case "hasPurchase":
					ret_val = self.hasFieldValue("USC_Purchase", "ProductCode", requirement.value, requirement.field2, requirement.value2, requirement.condition);
					break;
				case "hasSubscription":
					ret_val = self.hasFieldValue("Subscriptions", "PRODUCT_CODE", requirement.value, null, null, requirement.condition);
					break;
				case "hasMemberType":
					ret_val = self.hasFieldValue("Name", "MEMBER_TYPE", requirement.value, null, null, requirement.condition);
					break;
				case "hasAgencyType":
					ret_val = self.hasFieldValue("Name_Agency", "MEMBER_TYPE", requirement.value, null, null, requirement.condition);
					break;
				case "hasCommittee":
					ret_val = self.hasFieldValue("Activity_Committee", "PRODUCT_CODE", "COMMITTEE/" + requirement.value, null, null, requirement.condition);
					break;
				case "hasAgencyProduct":
					ret_val = self.hasFieldValue("Subscriptions_Agency", "PRODUCT_CODE", requirement.value, null, null, requirement.condition);
					break;
				case "hasSubscriptionType":
					ret_val = self.hasFieldValue("Subscriptions", "PROD_TYPE", requirement.value, null, null, requirement.condition);
					break;
				default:
					break;
			}

			return ret_val;
		}

	}

	return self;
}
module.exports.get_WebUserGroups = get_WebUserGroups;
module.exports.WebUser = WebUser;