var tedious = require('tedious');
var os = require('os')
var constants = require('./constants');

// TO DO... CAN WE ENCRYPT THIS? ALSO... HOW TO DIFFIRENTIATE BETWEEN ENVIRONMENTS
// STAGING SERVER
var hostname = os.hostname();
var ms_sql_server;

// Issue with connecting to dev via IP. Firewall issue?
if (hostname == 'web01do' || hostname == 'web02do' || hostname == 'planning-web01do' || hostname == 'planning-web02do' || hostname == 'planning-web01do.planning.org' || hostname == 'planning-web02do.planning.org' || hostname == 'web01do.planning.org' || hostname == 'web02do.planning.org'){
	ms_sql_server = 'prodsql01.planning.org'
} else if (hostname=='web01do-stage' || hostname == 'web01do-stg.planning.org') {
	ms_sql_server = 'devsql01.planning.org'
} else
{
	// ms_sql_server = '172.86.160.78'
	ms_sql_server = 'devsql01.planning.org'
  // ms_sql_server = 'localhost'
}

// }else if (hostname == 'conference-staging'){
// 	ms_sql_server = '38.124.107.156'
// }else{
// 	ms_sql_server = 'SQL05C-DEV' // make this dev server?
//}

// if (ms_sql_server == 'SQL05C-DEV' || ms_sql_server == '38.124.107.156'){
// 	var SQL_CONFIG = {
// 	userName: 'sa',
// 	password: '313phant',
// 	server: ms_sql_server,
// 	options: {
// 		//rowCollectionOnRequestCompletion:true,
// 		useColumnNames:true
// 	}}}
// else{
// var dbPassword = process.env.MSSQL_PASSWORD;
var dbPassword = constants.mssqlpassword
var SQL_CONFIG = {
	userName: 'django',
	password: dbPassword,
	server: ms_sql_server,
	options: {
		//rowCollectionOnRequestCompletion:true,
		useColumnNames:true,
        encrypt: true,
        database: 'imis_live'
	}}
//}

//for returning the results of a procedure to a variable
//meant to be used with async.js (notice the callback)
function callProcedure(props, callback){
	var PROCEDURE_NAME = props.procedure_name;
	var PARAMETERS = props.parameters;

	var results = {"data":[]};

	var connection = new tedious.Connection(SQL_CONFIG);
	connection.on('connect', connectCallback);

	function connectCallback(err) {

		var request = new tedious.Request(PROCEDURE_NAME, function(err, rowCount){
			callback(err,results);
			connection.close();
		});

		var d = new Date().getTime()

		request.on('row',function(cols){
			var _row = {};
			for(x in cols) {
				_row[x] = cols[x].value
			}
			results.data.push(_row);
		});

		for(var i = 0; i < PARAMETERS.length; i++){
			request.addParameter(PARAMETERS[i].name, PARAMETERS[i].type, PARAMETERS[i].value);
		}

		connection.callProcedure(request);
	}

}

// Pass the procedure name and an array of parameters with types.
// This will generate a function to call that procedure ard return the rows throught the 'res' object as json
function makeProcedureCaller(props){
	var PROCEDURE_NAME = props.procedure_name;
	var PARAMETERS = props.parameters;
	var is_single_record = props.return_type && props.return_type == "SINGLE"

	function ProcedureCaller(req, res, next){

		api_key = req.params['api_key'];
		req_url = req.url;

		// throw an error if the key is invalid AND the is an api url
		if (isValidKey(api_key) == false && isAPIUrl(req_url)) {
			res.send({
			data: [ ],
			success: false,
			error: {
			name: "RequestError",
			message: "Invalid request",
			code: "EREQUEST"
			} });
			return next()
		}

		var connection = new tedious.Connection(SQL_CONFIG);
		connection.on('connect', connectCallback);

		function connectCallback(err) {

			var results = {"data":[]};

			var request = new tedious.Request(PROCEDURE_NAME, function(err, rowCount){
				if(err){
					console.log(err);
					results.success = false
					results.error = err
					res.setHeader('content-type', 'application/json');
					res.send(results);
				} else {
					results.success = true
					res.setHeader('content-type', 'application/json');
					res.send(results);
	  				next();
				}
				connection.close();
			});


			request.on('row',function(cols){
				var _row = {}
				for(x in cols) {
					_row[x] = cols[x].value
				}

				if(is_single_record) {
					results.data = _row
				}else{
					results.data.push(_row)
				}
			});

			for(var i = 0; i < PARAMETERS.length; i++){
				request.addParameter(PARAMETERS[i].name, PARAMETERS[i].type, req.params[PARAMETERS[i].name], PARAMETERS[i].options);
			}

			connection.callProcedure(request);
		}

	}
	return ProcedureCaller;
}

function makeProcedureCallerSingleRecord(props) {
	props.return_type = "SINGLE";
	return makeProcedureCaller(props)
}

function isValidKey(api_key) {
	valid_key = false;

	if (api_key == "C00k13m0nst3r.") valid_key = true;
	return valid_key;
}

function isAPIUrl(req_url) {
	is_api_url = false;

	if (req_url.indexOf("/api/0.2/") > -1 ) is_api_url = true;
	return is_api_url;
}

module.exports.callProcedure = callProcedure;
module.exports.makeProcedureCaller = makeProcedureCaller;
module.exports.makeProcedureCallerSingleRecord = makeProcedureCallerSingleRecord;
module.exports.hostname = hostname;
