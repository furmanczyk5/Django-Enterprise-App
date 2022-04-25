// javascript admin page checkin system (requires jquery)
// - user will receive a warning when someone else is checked in
// - a request will be made every [refresh_checkin_rate] milliseconds to keep user checked in,
	// however, for some browsers this call is not made when window is no in focus
// - user will be checked out before leaving this page (close, navigate away, etc.), but different for every browser

var planning_admin = planning_admin || {};

(function(PA){

	PA.CheckinSystem = (function(){
		var self = this;

		self.refresh_checkin_rate = 30000; // 30 seconds
		self.checkedIn = false;
		self.keep_checked_in_interval = null;

		self.checkIn = function(onsuccess){

			var content_id = $(".planning-admin-checkin-tool").attr("data-content-id");
			var url = "/pages/admin/"+content_id+"/checkin/";

			self.displayLoading();

			$.get(url)
				.done(function(data){
					if(data.success == true){
						self.checkedIn = true;
						self.displayCheckedIn();
						if(onsuccess)onsuccess();
					}else{
						self.checkedIn = false;
						self.checkOut();
						alert(data.message);
					}
				})
				.fail(function(data){
					self.checkedIn = false;
					// This means something was wrong with request,
					//     so we still want to try to checkin again,
					//     only calling displayCheckedOut so that keepCheckIn still in effect
					self.displayCheckedOut(); 
				});
		};

		self.checkOut = function(){

			var content_id = $(".planning-admin-checkin-tool").attr("data-content-id");
			var url = "/pages/admin/"+content_id+"/checkout/";

			self.removeKeepCheckedIn();

			if(self.checkedIn){
				self.displayLoading();
				$.get(url)
					.always(function(data){
						self.checkedIn = false;
						self.displayCheckedOut();
					}); // make sure we checkout user in db before leaving
			}else{
				self.checkedIn = false;
				self.displayCheckedOut();
			}
		};

		self.keepCheckedIn = function(){

			self.removeKeepCheckedIn();

			self.checkIn(function(){
				self.keep_checked_in_interval = window.setInterval(self.checkIn, self.refresh_checkin_rate);
				$(window).on("focus", self.keepCheckedIn);
			});
		};

		self.removeKeepCheckedIn = function() {
			if(self.keep_checked_in_interval){
				window.clearInterval(self.keep_checked_in_interval);
				self.keep_checked_in_interval = null;
			}
			$(window).off("focus", self.keepCheckedIn);
		};

		self.displayLoading = function(){
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedin").addClass("loading");
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedout").addClass("loading");
		};

		self.displayNotLoading = function(){
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedin").removeClass("loading");
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedout").removeClass("loading");
		}

		self.displayCheckedIn = function(){
			self.displayNotLoading();
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedout").hide();
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedin").show();
		};

		self.displayCheckedOut = function(){
			self.displayNotLoading();
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedin").hide();
			$(".planning-admin-checkin-tool .planning-admin-checkin-checkedout").show();
		};

		// Maybe use custom modal later
		// self.alertCheckInConflict = function(user){
		// 	// code to alert user that someone else is checkin to this content
		// };

		return self
	})();

})(planning_admin);

$(function(){

	if($(".planning-admin-checkin-tool").length){ // so this only happens on change_form pages

		planning_admin.CheckinSystem.keepCheckedIn();
		$(window).on("unload beforeunload",planning_admin.CheckinSystem.checkOut);

		$(document).on("click","a.planning-admin-checkin",function(){
			planning_admin.CheckinSystem.keepCheckedIn();
		});
	}

});






